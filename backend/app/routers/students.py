import csv
import io
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.core.upload_limits import read_uploaded_image, validate_text_upload_bytes
from app.models.student import Student
from app.schemas.common import ApiResponse
from app.schemas.student import (
    BatchImportResult,
    StudentCreate,
    StudentListData,
    StudentRead,
    StudentUpdate,
)
from app.services.face_service import extract_face_embedding, serialize_embedding

router = APIRouter(dependencies=[Depends(require_roles("teacher"))])

FACE_UPLOAD_DIR = Path("face_uploads")
FACE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _normalize_csv_header(cell: str) -> str | None:
    key = (cell or "").strip().lower().replace("\ufeff", "")
    mapping = {
        "student_id": "student_id",
        "student_no": "student_id",
        "studentid": "student_id",
        "学号": "student_id",
        "no": "student_id",
        "name": "name",
        "姓名": "name",
        "class_name": "class_name",
        "class": "class_name",
        "班级": "class_name",
    }
    return mapping.get(key)


@router.post("/batch-import", response_model=ApiResponse[BatchImportResult])
async def batch_import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ApiResponse[BatchImportResult]:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    validate_text_upload_bytes(raw)

    text = raw.decode("utf-8-sig", errors="replace")
    sample = text[:4096]
    delimiter = "," if sample.count(",") >= sample.count(";") else ";"
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV 无内容")

    header_map: dict[str, int] | None = None
    start_idx = 0
    first = [c.strip() for c in rows[0]]
    mapped = [_normalize_csv_header(c) for c in first]
    if any(mapped):
        header_map = {}
        for idx, m in enumerate(mapped):
            if m:
                header_map[m] = idx
        if "student_id" not in header_map or "name" not in header_map:
            raise HTTPException(status_code=400, detail="CSV 表头需包含学号与姓名列")
        start_idx = 1
    else:
        if len(first) < 2:
            raise HTTPException(status_code=400, detail="每行至少包含学号与姓名两列")
        header_map = {"student_id": 0, "name": 1, "class_name": 2}

    created = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    def cell(row: list[str], key: str) -> str:
        idx = header_map[key]
        if idx >= len(row):
            return ""
        return (row[idx] or "").strip()

    for line_no, row in enumerate(rows[start_idx:], start=start_idx + 1):
        if not row or all(not (c or "").strip() for c in row):
            continue
        sid = cell(row, "student_id")
        name = cell(row, "name")
        class_name_raw = cell(row, "class_name") if "class_name" in header_map else ""
        if not sid or not name:
            failed += 1
            errors.append(f"第{line_no}行：学号或姓名为空")
            continue
        exists = db.query(Student).filter(Student.student_id == sid).first()
        if exists:
            skipped += 1
            continue
        db.add(Student(student_id=sid, name=name, class_name=class_name_raw or None))
        created += 1

    db.commit()
    return ApiResponse(
        data=BatchImportResult(
            created=created, skipped=skipped, failed=failed, errors=errors[:50]
        )
    )


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


@router.put("/{student_id}", response_model=ApiResponse[StudentRead])
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[StudentRead]:
    row = db.query(Student).filter(Student.id == student_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="学生不存在")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="没有可更新字段")

    new_sid = updates.get("student_id")
    if new_sid is not None:
        new_sid = str(new_sid).strip()
        if not new_sid:
            raise HTTPException(status_code=400, detail="学号不能为空")
        if new_sid != row.student_id:
            clash = db.query(Student).filter(Student.student_id == new_sid).first()
            if clash:
                raise HTTPException(status_code=409, detail="学号已存在")
        row.student_id = new_sid

    if "name" in updates and updates["name"] is not None:
        name = str(updates["name"]).strip()
        if not name:
            raise HTTPException(status_code=400, detail="姓名不能为空")
        row.name = name

    if "class_name" in updates:
        cn = updates["class_name"]
        row.class_name = str(cn).strip() if cn else None

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

    content = await read_uploaded_image(image)

    ext = Path(image.filename or "").suffix.lower() or ".jpg"
    filename = f"{student_id}_{uuid4().hex}{ext}"
    save_path = FACE_UPLOAD_DIR / filename
    save_path.write_bytes(content)

    try:
        embedding = extract_face_embedding(content)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    row.face_path = f"/face_uploads/{filename}"
    row.face_encoding = serialize_embedding(embedding)
    db.commit()
    db.refresh(row)

    return ApiResponse(data={"ok": True, "face_path": row.face_path})


@router.delete("/{student_id}/face", response_model=ApiResponse[dict])
def delete_face(student_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    row = db.query(Student).filter(Student.id == student_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="学生不存在")

    old_path = row.face_path
    row.face_path = None
    row.face_encoding = None
    db.commit()

    if old_path:
        try:
            # 兼容旧数据：old_path 可能是绝对路径，也可能是 /face_uploads/xxx
            if old_path.startswith("/face_uploads/"):
                p = FACE_UPLOAD_DIR / Path(old_path).name
            else:
                p = Path(old_path)
            if p.exists() and p.is_file():
                p.unlink()
        except Exception:
            pass

    return ApiResponse(data={"ok": True})

