from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttendanceCreateResponse(BaseModel):
    record_id: int
    status: str
    matched_student_no: Optional[str] = None
    emotion: Optional[str] = None
    timestamp: datetime
