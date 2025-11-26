from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PhotoMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    size: Optional[int] = None


class PhotoAIModeration(BaseModel):
    is_adult_content: Optional[bool] = None
    is_racy_content: Optional[bool] = None
    is_gory_content: Optional[bool] = None
    adult_score: Optional[float] = None
    racy_score: Optional[float] = None
    gore_score: Optional[float] = None


class PhotoAIInsights(BaseModel):
    tags: List[str] = Field(default_factory=list)
    objects: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    dominant_colors: List[str] = Field(default_factory=list)
    caption: Optional[str] = None
    caption_confidence: Optional[float] = None
    moderation: Optional[PhotoAIModeration] = None
    model_version: Optional[str] = None
    analyzed_at: Optional[datetime] = None


class Photo(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: Optional[str] = Field(None, alias="_id")
    creator_id: str
    title: str
    caption: Optional[str] = None
    location: Optional[str] = None
    people_present: List[str] = Field(default_factory=list)
    cloudinary_public_id: str
    cloudinary_url: str
    thumbnail_url: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    average_rating: float = 0.0
    total_ratings: int = 0
    total_likes: int = 0
    metadata: Optional[PhotoMetadata] = None
    ai_insights: Optional[PhotoAIInsights] = None
