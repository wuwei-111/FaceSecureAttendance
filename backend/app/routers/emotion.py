from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.emotion_log import EmotionLog
from app.schemas.common import ApiResponse
from app.schemas.emotion import EmotionStatsResponse

router = APIRouter()


@router.get("/stats", response_model=ApiResponse[EmotionStatsResponse])
async def emotion_stats(db: Session = Depends(get_db)) -> ApiResponse[EmotionStatsResponse]:
    rows = (
        db.query(EmotionLog.emotion, func.count(EmotionLog.id))
        .group_by(EmotionLog.emotion)
        .all()
    )
    distribution = {emotion: int(cnt) for emotion, cnt in rows}
    total = int(sum(distribution.values()))
    return ApiResponse(data=EmotionStatsResponse(total=total, distribution=distribution))
