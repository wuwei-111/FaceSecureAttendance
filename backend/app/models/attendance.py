from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    check_time = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    status = Column(String(16), nullable=False, server_default="present")  # present / failed / pending
    confidence = Column(Float, nullable=True)
    emotion = Column(String(32), nullable=True)
    session_id = Column(String(64), nullable=True, index=True)

    student = relationship("Student", back_populates="attendance_records")
