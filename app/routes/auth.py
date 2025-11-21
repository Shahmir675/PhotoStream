from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
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
