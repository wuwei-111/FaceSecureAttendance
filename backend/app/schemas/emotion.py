from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmotionStatsResponse(BaseModel):
    total: int
    distribution: dict[str, int]


class EmotionRecordItem(BaseModel):
    id: int
    student_no: str
    student_name: Optional[str] = None
    emotion: str
    confidence: Optional[float] = None
    source: str
    record_time: datetime

    model_config = ConfigDict(from_attributes=True)


class EmotionRecordListData(BaseModel):
    items: list[EmotionRecordItem]
    total: int
    page: int
    page_size: int
