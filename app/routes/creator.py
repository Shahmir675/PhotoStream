from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException
from app.schemas.photo import PhotoCreate, PhotoUpdate, PhotoResponse
from app.services.photo_service import PhotoService
from app.middleware.auth_middleware import get_current_creator
from app.models.user import User
from app.utils.validators import validate_image_file
from typing import List, Optional
import json

router = APIRouter(prefix="/api/creator", tags=["Creator"])


@router.post("/photos", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    title: str = Form(...),
    caption: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    people_present: Optional[str] = Form("[]"),
    current_user: User = Depends(get_current_creator)
):
    """Upload a new photo (Creator only)"""
    # Validate file
    validate_image_file(file)

    # Parse people_present JSON array
    try:
        people_list = json.loads(people_present) if people_present else []
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format for people_present"
        )

    # Create photo data
    photo_data = PhotoCreate(
        title=title,
        caption=caption,
        location=location,
        people_present=people_list
    )

    # Upload photo
    photo_service = PhotoService()
    photo = await photo_service.create_photo(file, photo_data, current_user.id)

    return photo


@router.get("/photos", response_model=List[PhotoResponse])
async def get_my_photos(current_user: User = Depends(get_current_creator)):
    """Get all photos uploaded by the current creator"""
    photo_service = PhotoService()
    photos = await photo_service.get_creator_photos(current_user.id)
    return photos


@router.put("/photos/{photo_id}", response_model=PhotoResponse)
async def update_photo(
    photo_id: str,
    photo_data: PhotoUpdate,
    current_user: User = Depends(get_current_creator)
):
    """Update photo metadata (Creator only)"""
    photo_service = PhotoService()
    photo = await photo_service.update_photo(photo_id, photo_data, current_user.id)
    return photo


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: str,
    current_user: User = Depends(get_current_creator)
):
    """Delete a photo (Creator only)"""
    photo_service = PhotoService()
    await photo_service.delete_photo(photo_id, current_user.id)
    return None
