import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.attendance import AttendanceRecord
from app.models.student import Student
from app.schemas.common import ApiResponse
from app.schemas.attendance import AttendanceCreateResponse

router = APIRouter()


@router.post("/checkin", response_model=ApiResponse[AttendanceCreateResponse])
async def checkin(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ApiResponse[AttendanceCreateResponse]:
    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")

    digest = hashlib.sha256(content).digest()
    student = db.query(Student).filter(Student.face_encoding == digest).first()

    if student:
        status = "present"
        confidence = 1.0
        matched_student_no = student.student_id
        student_fk = student.id
    else:
        status = "failed"
        confidence = 0.0
        matched_student_no = None
        student_fk = None

    record = AttendanceRecord(
        student_id=student_fk,
        status=status,
        confidence=confidence,
        emotion=None,
        session_id=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ApiResponse(
        data=AttendanceCreateResponse(
            record_id=record.id,
            status=record.status,
            matched_student_no=matched_student_no,
            emotion=record.emotion,
            timestamp=record.check_time or datetime.utcnow(),
        )
    )
