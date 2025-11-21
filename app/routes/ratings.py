from fastapi import APIRouter, Depends, status
from app.schemas.rating import RatingCreate, RatingResponse, PhotoRatingStats
from app.services.rating_service import RatingService
from app.middleware.auth_middleware import get_current_consumer
from app.models.user import User

router = APIRouter(prefix="/api/photos", tags=["Ratings"])


@router.post("/{photo_id}/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def rate_photo(
    photo_id: str,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_consumer)
):
    """Rate a photo (Consumer only)"""
    rating_service = RatingService()
    rating = await rating_service.create_or_update_rating(
        photo_id=photo_id,
        rating_data=rating_data,
        user_id=current_user.id
    )
    return rating


@router.get("/{photo_id}/ratings", response_model=PhotoRatingStats)
async def get_photo_ratings(
    photo_id: str,
    current_user: User = Depends(get_current_consumer)
):
    """Get rating statistics for a photo (Consumer only)"""
    rating_service = RatingService()
    stats = await rating_service.get_photo_rating_stats(photo_id)
    return stats
