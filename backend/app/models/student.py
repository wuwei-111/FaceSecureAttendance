from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_no = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    face_embedding_path = Column(String(255), nullable=True)

    attendance_records = relationship("AttendanceRecord", back_populates="student")
