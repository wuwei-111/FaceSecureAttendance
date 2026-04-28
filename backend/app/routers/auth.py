from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password
from app.models.user import User
from app.schemas.auth import LoginData, LoginRequest, UserProfileData
from app.schemas.common import ApiResponse

router = APIRouter()


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
        db.add(User(username=username, password_hash=hash_password(password), role=role))
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

    if user.password_hash != hash_password(password):
        raise HTTPException(status_code=401, detail="unauthorized")

    token = create_access_token(user)
    return ApiResponse(
        data=LoginData(
            access_token=token,
            username=user.username,
            role=user.role,
        )
    )


@router.get("/me", response_model=ApiResponse[UserProfileData])
def auth_me(current_user: User = Depends(get_current_user)) -> ApiResponse[UserProfileData]:
    return ApiResponse(
        data=UserProfileData(
            id=current_user.id,
            username=current_user.username,
            role=current_user.role,
        )
    )

