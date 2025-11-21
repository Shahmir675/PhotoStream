from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class CommentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    photo_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    total: int
