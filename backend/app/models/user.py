from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), nullable=False, server_default="student")  # teacher / student
    linked_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

