from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    source = Column(String(32), nullable=False)  # attendance / group_photo
    emotion = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=True)
    record_time = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    student = relationship("Student", back_populates="emotion_logs")

