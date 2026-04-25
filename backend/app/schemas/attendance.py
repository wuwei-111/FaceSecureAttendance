from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttendanceCreateResponse(BaseModel):
    status: str
    matched_student_no: Optional[str] = None
    emotion: Optional[str] = None
    timestamp: datetime
