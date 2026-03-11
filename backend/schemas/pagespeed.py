from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PageSpeedResult(BaseModel):
    """Represents the result of a one-off PageSpeed check for a URL."""

    url: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    is_up: bool
    error_message: Optional[str] = None
    checked_at: datetime

    class Config:
        orm_mode = False
