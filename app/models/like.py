from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class Like(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: Optional[str] = Field(None, alias="_id")
    photo_id: str
    user_id: str
    liked: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
