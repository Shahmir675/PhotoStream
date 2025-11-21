from fastapi import APIRouter, Depends, status
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register-consumer", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_consumer(user_data: UserRegister):
    """Register a new consumer user"""
    auth_service = AuthService()
    user = await auth_service.register_consumer(user_data)

    return UserResponse(
        _id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login and get JWT token"""
    auth_service = AuthService()
    token = await auth_service.authenticate_user(login_data)
    return token


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
