from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import Base, engine
from app.core.request_context import current_request_id
from app import models  # noqa: F401
from app.routers import attendance, auth, emotion, photo, students

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FaceSecureAttendance API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(photo.router, prefix="/api/photo", tags=["photo"])
app.include_router(emotion.router, prefix="/api/emotion", tags=["emotion"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/")
def root() -> dict:
    return {"message": "FaceSecureAttendance API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
