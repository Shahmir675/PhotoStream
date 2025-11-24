from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    email: EmailStr
    username: str
    role: UserRole
    profile_picture_url: Optional[str] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None


class UserProfilePicture(BaseModel):
    """Simplified user info with profile picture"""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    username: str
    profile_picture_url: Optional[str] = None
    role: UserRole
    created_at: datetime


class ProfilePicturesListResponse(BaseModel):
    """Response for listing profile pictures"""
    users: list[UserProfilePicture]
    total: int
    page: int
    page_size: int
    has_next: bool
