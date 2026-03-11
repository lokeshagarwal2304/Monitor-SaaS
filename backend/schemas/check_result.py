from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CheckResultBase(BaseModel):
    website_id: int
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    is_up: bool
    error_message: Optional[str] = None

class CheckResultCreate(CheckResultBase):
    pass

class CheckResultResponse(CheckResultBase):
    id: int
    checked_at: datetime
    
    class Config:
        orm_mode = True

class CheckResultStats(BaseModel):
    website_id: int
    total_checks: int
    successful_checks: int
    failed_checks: int
    uptime_percentage: float
    average_response_time: Optional[float] = None
    last_24h_checks: int
    last_24h_uptime: float