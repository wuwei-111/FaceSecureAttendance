from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.emotion_log import EmotionLog
from app.models.student import Student
from app.schemas.common import ApiResponse
from app.schemas.emotion import EmotionRecordItem, EmotionRecordListData, EmotionStatsResponse

router = APIRouter(dependencies=[Depends(require_roles("teacher"))])


@router.get("/stats", response_model=ApiResponse[EmotionStatsResponse])
def emotion_stats(
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
) -> ApiResponse[EmotionStatsResponse]:
    q = db.query(EmotionLog.emotion, func.count(EmotionLog.id))
    if date_from is not None:
        q = q.filter(
            EmotionLog.record_time >= datetime.combine(date_from, time.min)
        )
    if date_to is not None:
        q = q.filter(
            EmotionLog.record_time <= datetime.combine(date_to, time.max)
        )
    rows = q.group_by(EmotionLog.emotion).all()
    distribution = {emotion: int(cnt) for emotion, cnt in rows}
    total = int(sum(distribution.values()))
    return ApiResponse(data=EmotionStatsResponse(total=total, distribution=distribution))


@router.get("/records", response_model=ApiResponse[EmotionRecordListData])
def emotion_records(
    q: str = Query(default="", description="学号/姓名关键字"),
    emotion: str = Query(default="all"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse[EmotionRecordListData]:
    query = (
        db.query(EmotionLog, Student)
        .join(Student, EmotionLog.student_id == Student.id)
        .order_by(EmotionLog.id.desc())
    )
    conditions = []
    keyword = q.strip()
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(Student.student_id.ilike(like), Student.name.ilike(like))
        )
    if emotion != "all":
        conditions.append(EmotionLog.emotion == emotion)
    if date_from is not None:
        conditions.append(
            EmotionLog.record_time >= datetime.combine(date_from, time.min)
        )
    if date_to is not None:
        conditions.append(
            EmotionLog.record_time <= datetime.combine(date_to, time.max)
        )
    if conditions:
        query = query.filter(and_(*conditions))

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [
        EmotionRecordItem(
            id=log.id,
            student_no=stu.student_id,
            student_name=stu.name,
            emotion=log.emotion,
            confidence=log.confidence,
            source=log.source,
            record_time=log.record_time,
        )
        for log, stu in rows
    ]
    return ApiResponse(
        data=EmotionRecordListData(
            items=items, total=total, page=page, page_size=page_size
        )
    )
