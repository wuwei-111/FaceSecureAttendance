from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class GroupPhoto(Base):
    __tablename__ = "group_photos"

    id = Column(Integer, primary_key=True, index=True)
    photo_path = Column(String(255), nullable=False)
    activity_name = Column(String(128), nullable=True)
    upload_time = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    total_faces = Column(Integer, nullable=True)
    matched = Column(Integer, nullable=True)

