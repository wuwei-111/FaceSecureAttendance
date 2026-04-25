from pydantic import BaseModel


class EmotionStatsResponse(BaseModel):
    total: int
    distribution: dict[str, int]

