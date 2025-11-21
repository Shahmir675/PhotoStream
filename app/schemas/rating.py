from pydantic import BaseModel, Field, field_validator, ConfigDict


class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


class RatingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    photo_id: str
    user_id: str
    rating: int


class PhotoRatingStats(BaseModel):
    average_rating: float
    total_ratings: int
    rating_distribution: dict
