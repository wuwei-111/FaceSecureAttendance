import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.core.request_context import current_request_id
from app import models  # noqa: F401
from app.db_schema import ensure_sqlite_columns
from app.routers import attendance, auth, emotion, export_api, photo, students

Base.metadata.create_all(bind=engine)
ensure_sqlite_columns()

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("facesecure")

app = FastAPI(title="FaceSecureAttendance API", version="0.1.0")

FACE_UPLOAD_DIR = Path("face_uploads")
FACE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/face_uploads", StaticFiles(directory=str(FACE_UPLOAD_DIR)), name="face_uploads")

GROUP_UPLOAD_DIR = Path("group_uploads")
GROUP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/group_uploads", StaticFiles(directory=str(GROUP_UPLOAD_DIR)), name="group_uploads")

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]
_cors_origin_regex = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    token = current_request_id.set(request_id)
    try:
        response = await call_next(request)
    finally:
        current_request_id.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    _ = request
    request_id = current_request_id.get()
    if exc.status_code == 401:
        code, message = 40100, "unauthorized"
    elif exc.status_code == 403:
        code, message = 40300, "forbidden"
    else:
        code, message = exc.status_code, str(exc.detail)
    payload = {"code": code, "message": message, "data": None, "request_id": request_id}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    _ = request
    payload = {
        "code": 42200,
        "message": "validation_error",
        "data": {"errors": exc.errors()},
        "request_id": current_request_id.get(),
    }
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """未捕获异常：写日志；响应不暴露内部细节（APP_DEBUG=1 时可看详情）。"""
    request_id = current_request_id.get()
    _log.exception(
        "Unhandled error request_id=%s path=%s",
        request_id,
        request.url.path,
    )
    debug = os.getenv("APP_DEBUG", "").lower() in ("1", "true", "yes")
    message = str(exc) if debug else "服务暂时不可用，请稍后重试"
    return JSONResponse(
        status_code=500,
        content={
            "code": 50000,
            "message": message,
            "data": None,
            "request_id": request_id,
        },
    )


app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(photo.router, prefix="/api/photo", tags=["photo"])
app.include_router(emotion.router, prefix="/api/emotion", tags=["emotion"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(export_api.router, prefix="/api/export", tags=["export"])


@app.get("/")
def root() -> dict:
    return {"message": "FaceSecureAttendance API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
