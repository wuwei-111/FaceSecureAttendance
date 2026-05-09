import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.core.upload_limits import read_uploaded_image
from app.models.activity_log import ActivityLog
from app.models.group_photo import GroupPhoto
from app.models.student import Student
from app.schemas.common import ApiResponse
from app.schemas.photo import (
    GroupPhotoListData,
    MatchedStudent,
    PhotoActivityStatsData,
    PhotoActivityStatItem,
    PhotoRecognizeResponse,
    GroupPhotoItem,
)
from app.services.group_match_service import match_group_photo_faces, match_threshold_used

router = APIRouter(dependencies=[Depends(require_roles("teacher"))])

GROUP_UPLOAD_DIR = Path("group_uploads")
GROUP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/recognize", response_model=ApiResponse[PhotoRecognizeResponse])
async def recognize_group_photo(
    image: UploadFile = File(...),
    activity_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> ApiResponse[PhotoRecognizeResponse]:
    raw = await read_uploaded_image(image)

    try:
        matches_raw, n_faces = match_group_photo_faces(db, raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    ext = Path(image.filename or "").suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"
    save_name = f"{uuid4().hex}{ext}"
    save_path = GROUP_UPLOAD_DIR / save_name
    save_path.write_bytes(raw)
    rel_path = f"/group_uploads/{save_name}"

    act = activity_name.strip() if activity_name else None
    detail = {
        "matches": matches_raw,
        "total_faces": n_faces,
        "threshold": match_threshold_used(),
    }

    gp = GroupPhoto(
        photo_path=rel_path,
        activity_name=act,
        total_faces=n_faces,
        matched=len(matches_raw),
        detail_json=json.dumps(detail, ensure_ascii=False),
    )
    db.add(gp)
    db.commit()
    db.refresh(gp)

    for m in matches_raw:
        stu = db.query(Student).filter(Student.student_id == m["student_no"]).first()
        if stu:
            db.add(
                ActivityLog(
                    student_id=stu.id,
                    group_photo_id=gp.id,
                    activity_name=act,
                    emotion=None,
                    confidence=m.get("confidence"),
                )
            )
    db.commit()

    matched_models = [MatchedStudent(**x) for x in matches_raw]
    return ApiResponse(
        data=PhotoRecognizeResponse(
            group_photo_id=gp.id,
            matched_students=matched_models,
            count=len(matches_raw),
            total_faces_detected=n_faces,
        )
    )


@router.get("/list", response_model=ApiResponse[GroupPhotoListData])
def list_group_photos(
    q: str = Query(default="", description="活动名称关键字"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse[GroupPhotoListData]:
    query = db.query(GroupPhoto).order_by(GroupPhoto.id.desc())
    keyword = q.strip()
    if keyword:
        query = query.filter(GroupPhoto.activity_name.ilike(f"%{keyword}%"))
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return ApiResponse(
        data=GroupPhotoListData(
            items=[GroupPhotoItem.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/activity-stats", response_model=ApiResponse[PhotoActivityStatsData])
def photo_activity_stats(db: Session = Depends(get_db)) -> ApiResponse[PhotoActivityStatsData]:
    rows = (
        db.query(
            GroupPhoto.activity_name,
            func.count(GroupPhoto.id).label("cnt"),
            func.sum(GroupPhoto.matched).label("msum"),
        )
        .group_by(GroupPhoto.activity_name)
        .order_by(func.count(GroupPhoto.id).desc())
        .all()
    )
    items = [
        PhotoActivityStatItem(
            activity_name=name,
            photo_count=int(cnt or 0),
            matched_sum=int(msum or 0),
        )
        for name, cnt, msum in rows
    ]
    return ApiResponse(data=PhotoActivityStatsData(items=items))
