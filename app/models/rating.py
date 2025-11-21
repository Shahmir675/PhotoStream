from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class Rating(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: Optional[str] = Field(None, alias="_id")
    photo_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
