from fastapi import APIRouter, Depends, Query
from app.schemas.photo import PhotoResponse, PhotoListResponse
from app.services.photo_service import PhotoService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter(prefix="/api/photos", tags=["Photos"])


@router.get("", response_model=PhotoListResponse)
async def get_all_photos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get all photos with pagination and search (requires authentication)"""
    photo_service = PhotoService()
    photos = await photo_service.get_photos(
        page=page,
        page_size=page_size,
        search=search,
        location=location
    )
    return photos


@router.get("/search", response_model=PhotoListResponse)
async def search_photos(
    q: Optional[str] = Query(None, description="Search query for title or caption"),
    location: Optional[str] = Query(None, description="Filter by location"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Search photos by title, caption, or location"""
    photo_service = PhotoService()
    photos = await photo_service.get_photos(
        page=page,
        page_size=page_size,
        search=q,
        location=location
    )
    return photos


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single photo by ID"""
    photo_service = PhotoService()
    photo = await photo_service.get_photo_by_id(photo_id)
    return photo
