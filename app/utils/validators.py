from fastapi import HTTPException, UploadFile
from typing import List
from app.config import settings


def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file type
    allowed_types = settings.allowed_image_types.split(',')

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Note: File size will be checked during upload to avoid loading entire file in memory
    # This is handled in the upload service


def validate_file_size(file_size: int) -> None:
    """Validate file size"""
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.max_upload_size / 1024 / 1024}MB"
        )
