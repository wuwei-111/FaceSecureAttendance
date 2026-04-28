import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8
JWT_SECRET = os.getenv("JWT_SECRET", "facesecure-dev-secret-change-me")


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def create_access_token(user: User) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user.username,
        "uid": user.id,
        "role": user.role,
        "exp": expire_at,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="unauthorized") from exc
    return payload


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="unauthorized")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return user


def require_roles(*allowed_roles: str):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if allowed_roles and current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return current_user

    return _dependency
