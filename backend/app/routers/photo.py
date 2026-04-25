from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.group_photo import GroupPhoto
from app.schemas.common import ApiResponse
from app.schemas.photo import PhotoRecognizeResponse

router = APIRouter()


@router.post("/recognize", response_model=ApiResponse[PhotoRecognizeResponse])
async def recognize_group_photo(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ApiResponse[PhotoRecognizeResponse]:
    # 先打通数据流：接收图片 -> 写入合照占位记录 -> 返回 group_photo_id
    _ = image
    gp = GroupPhoto(photo_path=image.filename or "uploaded.jpg", activity_name=None, total_faces=0, matched=0)
    db.add(gp)
    db.commit()
    db.refresh(gp)
    return ApiResponse(
        data=PhotoRecognizeResponse(group_photo_id=gp.id, matched_students=[], count=0)
    )
