from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.request_context import current_request_id

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T
    request_id: str | None = Field(default_factory=lambda: current_request_id.get())

