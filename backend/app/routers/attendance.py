from datetime import datetime

from fastapi import APIRouter, File, UploadFile

from app.schemas.attendance import AttendanceCreateResponse

router = APIRouter()


@router.post("/checkin", response_model=AttendanceCreateResponse)
async def checkin(image: UploadFile = File(...)) -> AttendanceCreateResponse:
    # 这里后续接入：活体检测 + DeepFace 比对 + 入库
    _ = image
    return AttendanceCreateResponse(
        status="pending",
        matched_student_no=None,
        emotion=None,
        timestamp=datetime.utcnow(),
    )
