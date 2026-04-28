from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MatchedStudent(BaseModel):
    student_no: str
    student_name: Optional[str] = None
    confidence: float


class PhotoRecognizeResponse(BaseModel):
    group_photo_id: int
    matched_students: list[MatchedStudent]
    count: int
    total_faces_detected: int


class GroupPhotoItem(BaseModel):
    id: int
    photo_path: str
    activity_name: Optional[str] = None
    upload_time: datetime
    total_faces: Optional[int] = None
    matched: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class GroupPhotoListData(BaseModel):
    items: list[GroupPhotoItem]
    total: int
    page: int
    page_size: int


class PhotoActivityStatItem(BaseModel):
    activity_name: Optional[str] = None
    photo_count: int
    matched_sum: int


class PhotoActivityStatsData(BaseModel):
    items: list[PhotoActivityStatItem]
