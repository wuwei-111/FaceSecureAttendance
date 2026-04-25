from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def emotion_stats() -> dict:
    return {
        "total": 0,
        "distribution": {"happy": 0, "neutral": 0, "sad": 0, "angry": 0},
    }
