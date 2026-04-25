from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StudentCreate(BaseModel):
    student_id: str
    name: str
    class_name: Optional[str] = None


class StudentRead(BaseModel):
    id: int
    student_id: str
    name: str
    class_name: Optional[str] = None
    face_path: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentListData(BaseModel):
    items: list[StudentRead]
    total: int
    page: int
    page_size: int

