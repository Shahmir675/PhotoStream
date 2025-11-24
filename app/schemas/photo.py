from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PhotoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    caption: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    people_present: List[str] = Field(default_factory=list)


class PhotoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    caption: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    people_present: Optional[List[str]] = None


class PhotoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    creator_id: str
    username: str  # Username of the creator who posted the photo
    title: str
    caption: Optional[str]
    location: Optional[str]
    people_present: List[str]
    cloudinary_url: str
    thumbnail_url: Optional[str]
    upload_date: datetime
    average_rating: float
    total_ratings: int
    total_likes: int = 0


class PhotoListResponse(BaseModel):
    photos: List[PhotoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
