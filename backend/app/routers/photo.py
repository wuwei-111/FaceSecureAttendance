from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/recognize")
async def recognize_group_photo(image: UploadFile = File(...)) -> dict:
    # 这里后续接入：多人脸检测与批量比对
    _ = image
    return {"matched_students": [], "count": 0}
