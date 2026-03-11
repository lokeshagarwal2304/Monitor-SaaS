from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, validator, Field

class WebsiteBase(BaseModel):
    url: str
    name: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class WebsiteCreate(WebsiteBase):
    check_interval: Optional[int] = Field(default=5, ge=1, le=60)

# RESTORED: This class was missing in the last update
class WebsiteUpdate(BaseModel):
    url: Optional[str] = None
    name: Optional[str] = None
    check_interval: Optional[int] = Field(default=None, ge=1, le=60)

class WebsiteBulkImport(BaseModel):
    urls: str 

class WebsiteResponse(WebsiteBase):
    id: int
    owner_id: int
    check_interval: int
    status: str
    last_checked: Optional[datetime] = None
    created_at: datetime
    history: List[dict] = [] # Added for real data visuals

    class Config:
        orm_mode = True
    
    @validator('status', pre=True)
    def convert_enum_to_str(cls, v):
        if hasattr(v, 'value'):
            return v.value
        return v