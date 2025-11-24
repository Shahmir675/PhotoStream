from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    CREATOR = "creator"
    CONSUMER = "consumer"


class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    username: str
    password_hash: str
    role: UserRole
    profile_picture_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
