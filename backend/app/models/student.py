from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(32), unique=True, nullable=False, index=True)  # 学号
    name = Column(String(64), nullable=False)
    class_name = Column(String(64), nullable=True)
    face_path = Column(String(255), nullable=True)
    face_encoding = Column(LargeBinary, nullable=True)  # pickle 序列化后的 BLOB
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    attendance_records = relationship("AttendanceRecord", back_populates="student")
    activity_logs = relationship("ActivityLog", back_populates="student")
    emotion_logs = relationship("EmotionLog", back_populates="student")
