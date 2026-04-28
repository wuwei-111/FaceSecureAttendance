from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.attendance import AttendanceRecord
from app.models.student import Student
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.attendance import (
    AttendanceCreateResponse,
    AttendanceRecordItem,
    AttendanceRecordListData,
    AttendanceSessionItem,
    AttendanceSessionListData,
)
from app.services.face_service import (
    cosine_distance,
    deserialize_embedding,
    extract_face_embedding,
)
from app.services.liveness_service import passive_liveness_check
from app.core.upload_limits import validate_image_bytes

router = APIRouter()


def _attendance_records_base_query(db: Session):
    return (
        db.query(AttendanceRecord, Student)
        .outerjoin(Student, AttendanceRecord.student_id == Student.id)
        .order_by(AttendanceRecord.id.desc())
    )


def _apply_attendance_filters(
    query,
    *,
    current_user: User,
    q: str,
    status: str,
    date_from: Optional[date],
    date_to: Optional[date],
):
    conditions = []
    keyword = q.strip()
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(Student.student_id.ilike(like), Student.name.ilike(like))
        )
    if status != "all":
        conditions.append(AttendanceRecord.status == status)
    if current_user.role == "student":
        conditions.append(Student.student_id == current_user.username)
    if date_from is not None:
        conditions.append(
            AttendanceRecord.check_time >= datetime.combine(date_from, time.min)
        )
    if date_to is not None:
        conditions.append(
            AttendanceRecord.check_time <= datetime.combine(date_to, time.max)
        )
    if conditions:
        query = query.filter(and_(*conditions))
    return query


@router.get("/records", response_model=ApiResponse[AttendanceRecordListData])
def attendance_records(
    q: str = Query(default="", description="学号/姓名关键字"),
    status: str = Query(default="all"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    date_from: Optional[date] = Query(default=None, description="起始日期"),
    date_to: Optional[date] = Query(default=None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[AttendanceRecordListData]:
    query = _apply_attendance_filters(
        _attendance_records_base_query(db),
        current_user=current_user,
        q=q,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [
        AttendanceRecordItem(
            record_id=rec.id,
            student_no=stu.student_id if stu else None,
            student_name=stu.name if stu else None,
            status=rec.status,
            check_time=rec.check_time or datetime.utcnow(),
            emotion=rec.emotion,
            confidence=rec.confidence,
        )
        for rec, stu in rows
    ]
    return ApiResponse(
        data=AttendanceRecordListData(
            items=items, total=total, page=page, page_size=page_size
        )
    )


@router.get("/sessions", response_model=ApiResponse[AttendanceSessionListData])
def attendance_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[AttendanceSessionListData]:
    date_expr = func.strftime("%Y-%m-%d", AttendanceRecord.check_time)
    query = db.query(
        date_expr.label("d"),
        func.count(AttendanceRecord.id).label("total"),
        func.sum(case((AttendanceRecord.status == "present", 1), else_=0)).label("present"),
        func.sum(case((AttendanceRecord.status != "present", 1), else_=0)).label("failed"),
    ).outerjoin(Student, AttendanceRecord.student_id == Student.id)

    if current_user.role == "student":
        query = query.filter(Student.student_id == current_user.username)

    rows = (
        query.group_by(date_expr)
        .order_by(date_expr.desc())
        .all()
    )

    items = [
        AttendanceSessionItem(
            session_id=f"session-{d}",
            date=d,
            total=int(total or 0),
            present=int(present or 0),
            failed=int(failed or 0),
        )
        for d, total, present, failed in rows
    ]
    return ApiResponse(data=AttendanceSessionListData(items=items))


@router.post("/checkin", response_model=ApiResponse[AttendanceCreateResponse])
async def checkin(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("teacher", "student")),
) -> ApiResponse[AttendanceCreateResponse]:
    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    validate_image_bytes(content)

    try:
        liveness_ok, liveness_reason = passive_liveness_check(content)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not liveness_ok:
        record = AttendanceRecord(
            student_id=None,
            status="failed_liveness",
            confidence=0.0,
            emotion=None,
            session_id=None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return ApiResponse(
            data=AttendanceCreateResponse(
                record_id=record.id,
                status=f"failed_liveness:{liveness_reason}",
                matched_student_no=None,
                emotion=None,
                timestamp=record.check_time or datetime.utcnow(),
            )
        )

    try:
        probe_emb = extract_face_embedding(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    best_student = None
    best_dist = 1.0
    for s in db.query(Student).all():
        emb = deserialize_embedding(s.face_encoding)
        if not emb:
            continue
        dist = cosine_distance(probe_emb, emb)
        if dist < best_dist:
            best_dist = dist
            best_student = s

    threshold = 0.35
    if best_student and best_dist <= threshold:
        status = "present"
        confidence = max(0.0, 1.0 - best_dist)
        matched_student_no = best_student.student_id
        student_fk = best_student.id
    else:
        status = "failed"
        confidence = 0.0
        matched_student_no = None
        student_fk = None

    record = AttendanceRecord(
        student_id=student_fk,
        status=status,
        confidence=confidence,
        emotion=None,
        session_id=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ApiResponse(
        data=AttendanceCreateResponse(
            record_id=record.id,
            status=record.status,
            matched_student_no=matched_student_no,
            emotion=record.emotion,
            timestamp=record.check_time or datetime.utcnow(),
        )
    )
