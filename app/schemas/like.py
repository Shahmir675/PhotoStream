from pydantic import BaseModel, Field, ConfigDict


class LikeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    photo_id: str
    user_id: str
    liked: bool


class PhotoLikeStats(BaseModel):
    total_likes: int
    user_has_liked: bool
