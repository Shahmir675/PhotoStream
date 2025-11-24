from fastapi import APIRouter, Depends, status
from app.schemas.like import LikeResponse, PhotoLikeStats
from app.services.like_service import LikeService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/photos", tags=["Likes"])


@router.post("/{photo_id}/likes", response_model=LikeResponse, status_code=status.HTTP_200_OK)
async def toggle_like(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Toggle like on a photo (like if not liked, unlike if already liked)"""
    like_service = LikeService()
    like = await like_service.toggle_like(
        photo_id=photo_id,
        user_id=current_user.id
    )
    return like


@router.get("/{photo_id}/likes", response_model=PhotoLikeStats)
async def get_photo_likes(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get like statistics for a photo"""
    like_service = LikeService()
    stats = await like_service.get_photo_like_stats(photo_id, current_user.id)
    return stats
