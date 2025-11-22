from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import decode_access_token
from app.services.auth_service import AuthService
from app.services.cache_service import cache_service
from app.models.user import User, UserRole
from typing import Optional

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user with caching"""
    token = credentials.credentials

    # Decode token
    token_data = decode_access_token(token)

    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try to get user from cache first
    cache_key = f"user:{token_data.user_id}"
    cached_user = await cache_service.get(cache_key)

    if cached_user:
        # Reconstruct User object from cached data
        return User(**cached_user)

    # Get user from database if not in cache
    auth_service = AuthService()
    user = await auth_service.get_user_by_id(token_data.user_id)

    # Cache the user for 15 minutes
    await cache_service.set(cache_key, user.dict(), ttl=900)

    return user


async def get_current_creator(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify that the current user is a creator"""
    if current_user.role != UserRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creators can access this resource"
        )

    return current_user


async def get_current_consumer(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify that the current user is a consumer"""
    if current_user.role != UserRole.CONSUMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consumers can access this resource"
        )

    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
