from fastapi import HTTPException, status, UploadFile
from app.database import get_database
from app.models.photo import Photo, PhotoMetadata
from app.schemas.photo import PhotoCreate, PhotoUpdate, PhotoResponse, PhotoListResponse
from app.services.cloudinary_service import CloudinaryService
from bson import ObjectId
from typing import List, Optional
import math
import logging

logger = logging.getLogger(__name__)


class PhotoService:
    def __init__(self):
        self.db = get_database()
        self.cloudinary_service = CloudinaryService()

    def _check_db(self):
        """Check if database is available"""
        if self.db is None:
            logger.error("Database is not initialized in PhotoService")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

    async def create_photo(
        self,
        file: UploadFile,
        photo_data: PhotoCreate,
        creator_id: str
    ) -> PhotoResponse:
        """Create a new photo"""
        # Upload to Cloudinary
        upload_result = await self.cloudinary_service.upload_image(file)

        # Create photo document
        photo_dict = {
            "creator_id": creator_id,
            "title": photo_data.title,
            "caption": photo_data.caption,
            "location": photo_data.location,
            "people_present": photo_data.people_present,
            "cloudinary_public_id": upload_result["public_id"],
            "cloudinary_url": upload_result["url"],
            "thumbnail_url": upload_result["thumbnail_url"],
            "average_rating": 0.0,
            "total_ratings": 0,
            "metadata": {
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "format": upload_result.get("format"),
                "size": upload_result.get("size")
            }
        }

        # Add timestamp
        from datetime import datetime
        photo_dict["upload_date"] = datetime.utcnow()

        # Insert into database
        result = await self.db.photos.insert_one(photo_dict)
        photo_dict["_id"] = str(result.inserted_id)

        return PhotoResponse(**photo_dict)

    async def get_photos(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        location: Optional[str] = None
    ) -> PhotoListResponse:
        """Get all photos with pagination and search"""
        # Build query
        query = {}

        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"caption": {"$regex": search, "$options": "i"}}
            ]

        if location:
            query["location"] = {"$regex": location, "$options": "i"}

        # Count total documents
        total = await self.db.photos.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = math.ceil(total / page_size)

        # Get photos
        cursor = self.db.photos.find(query).sort("upload_date", -1).skip(skip).limit(page_size)
        photos = await cursor.to_list(length=page_size)

        # Convert ObjectId to string
        photo_responses = []
        for photo in photos:
            photo["_id"] = str(photo["_id"])
            photo_responses.append(PhotoResponse(**photo))

        return PhotoListResponse(
            photos=photo_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_photo_by_id(self, photo_id: str) -> PhotoResponse:
        """Get photo by ID"""
        try:
            photo = await self.db.photos.find_one({"_id": ObjectId(photo_id)})
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        photo["_id"] = str(photo["_id"])
        return PhotoResponse(**photo)

    async def get_creator_photos(self, creator_id: str) -> List[PhotoResponse]:
        """Get all photos by a creator"""
        cursor = self.db.photos.find({"creator_id": creator_id}).sort("upload_date", -1)
        photos = await cursor.to_list(length=None)

        photo_responses = []
        for photo in photos:
            photo["_id"] = str(photo["_id"])
            photo_responses.append(PhotoResponse(**photo))

        return photo_responses

    async def update_photo(
        self,
        photo_id: str,
        photo_data: PhotoUpdate,
        creator_id: str
    ) -> PhotoResponse:
        """Update photo metadata"""
        # Check if photo exists and belongs to creator
        try:
            photo = await self.db.photos.find_one({"_id": ObjectId(photo_id)})
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        if photo["creator_id"] != creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this photo"
            )

        # Update only provided fields
        update_data = photo_data.dict(exclude_unset=True)

        if update_data:
            await self.db.photos.update_one(
                {"_id": ObjectId(photo_id)},
                {"$set": update_data}
            )

        # Get updated photo
        updated_photo = await self.db.photos.find_one({"_id": ObjectId(photo_id)})
        updated_photo["_id"] = str(updated_photo["_id"])

        return PhotoResponse(**updated_photo)

    async def delete_photo(self, photo_id: str, creator_id: str) -> bool:
        """Delete a photo"""
        # Check if photo exists and belongs to creator
        try:
            photo = await self.db.photos.find_one({"_id": ObjectId(photo_id)})
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        if photo["creator_id"] != creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this photo"
            )

        # Delete from Cloudinary
        await self.cloudinary_service.delete_image(photo["cloudinary_public_id"])

        # Delete from database
        await self.db.photos.delete_one({"_id": ObjectId(photo_id)})

        # Delete associated comments and ratings
        await self.db.comments.delete_many({"photo_id": photo_id})
        await self.db.ratings.delete_many({"photo_id": photo_id})

        return True
