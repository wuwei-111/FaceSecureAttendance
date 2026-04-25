from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    group_photo_id = Column(Integer, ForeignKey("group_photos.id"), nullable=True, index=True)
    activity_name = Column(String(128), nullable=True, index=True)
    emotion = Column(String(32), nullable=True)
    confidence = Column(Float, nullable=True)
    record_time = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    student = relationship("Student", back_populates="activity_logs")
    group_photo = relationship("GroupPhoto")

