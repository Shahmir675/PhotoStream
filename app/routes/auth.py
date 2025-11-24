from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Query
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse, ProfilePicturesListResponse, UserProfilePicture
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.cloudinary_service import CloudinaryService
from app.services.cache_service import cache_service
from app.database import get_database
from app.utils.validators import validate_image_file
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register-consumer", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_consumer(user_data: UserRegister):
    """Register a new consumer user"""
    try:
        auth_service = AuthService()
        user = await auth_service.register_consumer(user_data)

        return UserResponse(
            _id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            profile_picture_url=user.profile_picture_url,
            created_at=user.created_at
        )
    except HTTPException:
        # Re-raise HTTPExceptions (400, 401, etc.) as-is
        raise
    except Exception as e:
        # Log the actual error for debugging
        logger.error(f"Registration failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed. Please try again later. Error: {type(e).__name__}"
        )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login and get JWT token"""
    try:
        auth_service = AuthService()
        token = await auth_service.authenticate_user(login_data)
        return token
    except HTTPException:
        # Re-raise HTTPExceptions (401, etc.) as-is
        raise
    except Exception as e:
        logger.error(f"Login failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed. Please try again later."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        _id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        profile_picture_url=current_user.profile_picture_url,
        created_at=current_user.created_at
    )


@router.post("/upgrade-to-creator", response_model=UserResponse)
async def upgrade_to_creator(current_user: User = Depends(get_current_user)):
    """Upgrade current user to creator role"""
    try:
        auth_service = AuthService()
        updated_user = await auth_service.upgrade_to_creator(current_user.id)

        return UserResponse(
            _id=updated_user.id,
            email=updated_user.email,
            username=updated_user.username,
            role=updated_user.role,
            profile_picture_url=updated_user.profile_picture_url,
            created_at=updated_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Role upgrade failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade user role"
        )


@router.post("/profile-picture", response_model=UserResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload or update profile picture for the current user"""
    try:
        # Validate file
        validate_image_file(file)

        # Upload to Cloudinary
        cloudinary_service = CloudinaryService()
        upload_result = await cloudinary_service.upload_profile_picture(file, current_user.id)

        # Update user in database
        db = get_database()
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {"profile_picture_url": upload_result["url"]}}
        )

        # Invalidate user cache so next request gets fresh data
        await cache_service.delete(f"user:{current_user.id}")

        # Get updated user
        updated_user = await db.users.find_one({"_id": ObjectId(current_user.id)})
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            _id=str(updated_user["_id"]),
            email=updated_user["email"],
            username=updated_user["username"],
            role=updated_user["role"],
            profile_picture_url=updated_user.get("profile_picture_url"),
            created_at=updated_user["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile picture upload failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


@router.get("/profile-pictures", response_model=ProfilePicturesListResponse)
async def list_profile_pictures(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    with_pictures_only: bool = Query(False, description="Only return users with profile pictures")
):
    """
    List all users with their profile pictures.

    This endpoint returns a paginated list of users with their usernames and profile picture URLs.
    Useful for displaying user galleries, member directories, or avatar lists.

    Query Parameters:
    - page: Page number (starts at 1)
    - page_size: Items per page (max 100)
    - with_pictures_only: If true, only returns users who have uploaded a profile picture

    Returns:
    - users: List of user profiles with username and profile_picture_url
    - total: Total number of users matching the criteria
    - page: Current page number
    - page_size: Items per page
    - has_next: Whether there are more pages available
    """
    try:
        db = get_database()

        # Build query filter
        query_filter = {}
        if with_pictures_only:
            query_filter["profile_picture_url"] = {"$ne": None, "$exists": True}

        # Get total count
        total = await db.users.count_documents(query_filter)

        # Calculate pagination
        skip = (page - 1) * page_size
        has_next = (skip + page_size) < total

        # Fetch users with pagination
        cursor = db.users.find(
            query_filter,
            {
                "_id": 1,
                "username": 1,
                "profile_picture_url": 1,
                "role": 1,
                "created_at": 1
            }
        ).sort("created_at", -1).skip(skip).limit(page_size)

        users_list = await cursor.to_list(length=page_size)

        # Convert to response model
        users = [
            UserProfilePicture(
                _id=str(user["_id"]),
                username=user["username"],
                profile_picture_url=user.get("profile_picture_url"),
                role=user["role"],
                created_at=user["created_at"]
            )
            for user in users_list
        ]

        return ProfilePicturesListResponse(
            users=users,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )

    except Exception as e:
        logger.error(f"Failed to list profile pictures: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile pictures: {str(e)}"
        )
