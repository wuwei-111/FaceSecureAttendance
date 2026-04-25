from pydantic import BaseModel


class PhotoRecognizeResponse(BaseModel):
    group_photo_id: int
    matched_students: list[str]
    count: int

