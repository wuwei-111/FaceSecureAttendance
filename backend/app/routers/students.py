import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.student import Student
from app.schemas.common import ApiResponse
from app.schemas.student import StudentCreate, StudentListData, StudentRead

router = APIRouter()

FACE_UPLOAD_DIR = Path("face_uploads")
FACE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=ApiResponse[StudentListData])
def list_students(
    q: str = Query(default="", description="按学号/姓名/班级模糊搜索"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse[StudentListData]:
    query = db.query(Student).order_by(Student.id.desc())
    keyword = q.strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Student.student_id.ilike(like),
                Student.name.ilike(like),
                Student.class_name.ilike(like),
            )
        )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ApiResponse(
        data=StudentListData(items=items, total=total, page=page, page_size=page_size)
    )


@router.post("", response_model=ApiResponse[StudentRead])
def create_student(
    payload: StudentCreate, db: Session = Depends(get_db)
) -> ApiResponse[StudentRead]:
    student_id = payload.student_id.strip()
    name = payload.name.strip()
    class_name = payload.class_name.strip() if payload.class_name else None

    if not student_id or not name:
        raise HTTPException(status_code=400, detail="学号和姓名不能为空")

    exists = db.query(Student).filter(Student.student_id == student_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="学号已存在")

    row = Student(student_id=student_id, name=name, class_name=class_name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ApiResponse(data=row)


@router.delete("/{student_id}", response_model=ApiResponse[dict])
def delete_student(student_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    row = db.query(Student).filter(Student.id == student_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="学生不存在")
    db.delete(row)
    db.commit()
    return ApiResponse(data={"ok": True})


@router.post("/{student_id}/face")
async def upload_face(
    student_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    row = db.query(Student).filter(Student.id == student_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="学生不存在")

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")

    ext = Path(image.filename or "").suffix.lower() or ".jpg"
    filename = f"{student_id}_{uuid4().hex}{ext}"
    save_path = FACE_UPLOAD_DIR / filename
    save_path.write_bytes(content)

    # 先用图片指纹做轻量比对占位；后续替换为真正的人脸 embedding
    digest = hashlib.sha256(content).digest()
    row.face_path = str(save_path).replace("\\", "/")
    row.face_encoding = digest
    db.commit()
    db.refresh(row)

    return ApiResponse(data={"ok": True, "face_path": row.face_path})

