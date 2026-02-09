from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClipboardItemCreate(BaseModel):
    content: str
    content_type: str = "text"
    device_name: Optional[str] = None

class ClipboardItemUpdate(BaseModel):
    content: str
    content_type: Optional[str] = "text"

class ClipboardItemResponse(BaseModel):
    id: str
    content: str
    content_type: str
    device_name: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ClipboardSyncRequest(BaseModel):
    last_sync: Optional[datetime] = None