from fastapi import APIRouter, Depends, status
from app.schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from app.services.comment_service import CommentService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/photos", tags=["Comments"])


@router.post("/{photo_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    photo_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a photo (All authenticated users)"""
    comment_service = CommentService()
    comment = await comment_service.create_comment(
        photo_id=photo_id,
        comment_data=comment_data,
        user_id=current_user.id,
        username=current_user.username
    )
    return comment


@router.get("/{photo_id}/comments", response_model=CommentListResponse)
async def get_photo_comments(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a photo (All authenticated users)"""
    comment_service = CommentService()
    comments = await comment_service.get_photo_comments(photo_id)
    return comments
