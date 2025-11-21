from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Comment(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    photo_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
