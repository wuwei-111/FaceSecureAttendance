from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttendanceCreateResponse(BaseModel):
    record_id: int
    status: str
    matched_student_no: Optional[str] = None
    emotion: Optional[str] = None
    timestamp: datetime


class AttendanceRecordItem(BaseModel):
    record_id: int
    student_no: Optional[str] = None
    student_name: Optional[str] = None
    status: str
    check_time: datetime
    emotion: Optional[str] = None
    confidence: Optional[float] = None


class AttendanceRecordListData(BaseModel):
    items: list[AttendanceRecordItem]
    total: int
    page: int
    page_size: int


class AttendanceSessionItem(BaseModel):
    session_id: str
    date: str
    total: int
    present: int
    failed: int


class AttendanceSessionListData(BaseModel):
    items: list[AttendanceSessionItem]
