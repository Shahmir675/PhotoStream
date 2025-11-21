from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class CommentResponse(BaseModel):
    id: str = Field(..., alias="_id")
    photo_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    total: int
