import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginData, LoginRequest
from app.schemas.common import ApiResponse

router = APIRouter()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _issue_dev_token(user: User) -> str:
    exp = int((datetime.now(timezone.utc) + timedelta(hours=8)).timestamp())
    raw = f"{user.id}:{user.username}:{user.role}:{exp}"
    sig = _sha256(f"facesecure:{raw}")[:16]
    return f"dev.{raw}.{sig}"


def _ensure_seed_users(db: Session) -> None:
    presets = [
        ("admin", "123456", "teacher"),
        ("teacher1", "123456", "teacher"),
        ("teacher2", "123456", "teacher"),
        ("student1", "123456", "student"),
        ("student2", "123456", "student"),
    ]
    existing = {u.username for u in db.query(User).all()}
    created = False
    for username, password, role in presets:
        if username in existing:
            continue
        db.add(User(username=username, password_hash=_sha256(password), role=role))
        created = True
    if created:
        db.commit()


@router.post("/login", response_model=ApiResponse[LoginData])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> ApiResponse[LoginData]:
    _ensure_seed_users(db)
    username = payload.username.strip()
    password = payload.password
    if not username or not password:
        raise HTTPException(status_code=401, detail="unauthorized")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")

    if user.password_hash != _sha256(password):
        raise HTTPException(status_code=401, detail="unauthorized")

    token = _issue_dev_token(user)
    return ApiResponse(
        data=LoginData(
            access_token=token,
            username=user.username,
            role=user.role,
        )
    )

