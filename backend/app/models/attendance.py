from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    status = Column(String(16), nullable=False, default="failed")
    liveness_passed = Column(Integer, nullable=False, default=0)
    emotion = Column(String(32), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    student = relationship("Student", back_populates="attendance_records")
