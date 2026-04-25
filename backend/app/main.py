from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app import models  # noqa: F401
from app.routers import attendance, emotion, photo

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FaceSecureAttendance API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(photo.router, prefix="/api/photo", tags=["photo"])
app.include_router(emotion.router, prefix="/api/emotion", tags=["emotion"])


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
