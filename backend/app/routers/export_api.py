"""考勤 / 活动记录导出 Excel（教师导出全班，学生仅本人）。"""

from datetime import date, datetime, time
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.student_visibility import student_own_student_clause
from app.models.activity_log import ActivityLog
from app.models.student import Student
from app.models.user import User
from app.routers.attendance import _apply_attendance_filters, _attendance_records_base_query

router = APIRouter()


def _filename_ts(prefix: str) -> str:
    return f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"


@router.get("/attendance/excel")
def export_attendance_excel(
    q: str = Query(default=""),
    status: str = Query(default="all"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _apply_attendance_filters(
        _attendance_records_base_query(db),
        current_user=current_user,
        q=q,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    rows = query.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "考勤记录"
    ws.append(
        ["record_id", "student_no", "student_name", "status", "check_time", "emotion", "confidence"]
    )
    for rec, stu in rows:
        ws.append(
            [
                rec.id,
                stu.student_id if stu else "",
                stu.name if stu else "",
                rec.status,
                (rec.check_time or datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S"),
                rec.emotion or "",
                rec.confidence if rec.confidence is not None else "",
            ]
        )

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{_filename_ts("attendance")}"',
        },
    )


@router.get("/activity/excel")
def export_activity_excel(
    q: str = Query(default="", description="学号/姓名"),
    activity: str = Query(default="", description="活动名称关键字"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(ActivityLog, Student)
        .join(Student, ActivityLog.student_id == Student.id)
        .order_by(ActivityLog.id.desc())
    )
    conditions = []
    kw = q.strip()
    if kw:
        like = f"%{kw}%"
        conditions.append(
            or_(Student.student_id.ilike(like), Student.name.ilike(like))
        )
    act_kw = activity.strip()
    if act_kw:
        conditions.append(ActivityLog.activity_name.ilike(f"%{act_kw}%"))
    if current_user.role == "student":
        conditions.append(student_own_student_clause(current_user))
    if date_from is not None:
        conditions.append(
            ActivityLog.record_time >= datetime.combine(date_from, time.min)
        )
    if date_to is not None:
        conditions.append(
            ActivityLog.record_time <= datetime.combine(date_to, time.max)
        )
    if conditions:
        query = query.filter(and_(*conditions))

    rows = query.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "活动记录"
    ws.append(
        [
            "record_id",
            "record_time",
            "student_no",
            "student_name",
            "activity_name",
            "emotion",
            "confidence",
            "group_photo_id",
        ]
    )
    for log, stu in rows:
        ws.append(
            [
                log.id,
                (log.record_time or datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S"),
                stu.student_id,
                stu.name,
                log.activity_name or "",
                log.emotion or "",
                log.confidence if log.confidence is not None else "",
                log.group_photo_id or "",
            ]
        )

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{_filename_ts("activity")}"',
        },
    )
