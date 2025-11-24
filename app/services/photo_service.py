from fastapi import HTTPException, status, UploadFile
from app.database import get_database
from app.models.photo import Photo, PhotoMetadata
from app.schemas.photo import PhotoCreate, PhotoUpdate, PhotoResponse, PhotoListResponse
from app.services.cloudinary_service import CloudinaryService
from app.services.cache_service import cache_service
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

        # Fetch username from users collection
        user = await self.db.users.find_one({"_id": creator_id})
        photo_dict["username"] = user["username"] if user and "username" in user else "Unknown User"

        # Invalidate cache for creator's photos and photo listings
        await cache_service.delete_pattern(f"photos:*")
        await cache_service.delete_pattern(f"creator_photos:{creator_id}")

        return PhotoResponse(**photo_dict)

    async def get_photos(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        location: Optional[str] = None
    ) -> PhotoListResponse:
        """Get all photos with pagination and search"""
        # Create cache key based on parameters
        cache_key = f"photos:page:{page}:size:{page_size}:search:{search}:location:{location}"

        # Try to get from cache
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {cache_key}")
            return PhotoListResponse(**cached_result)

        # Build match query
        match_query = {}

        if search:
            match_query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"caption": {"$regex": search, "$options": "i"}}
            ]

        if location:
            match_query["location"] = {"$regex": location, "$options": "i"}

        # Count total documents (use estimated count for first page for better performance)
        if page == 1 and not search and not location:
            total = await self.db.photos.estimated_document_count()
        else:
            total = await self.db.photos.count_documents(match_query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        # Use aggregation pipeline to join with users collection
        pipeline = []

        if match_query:
            pipeline.append({"$match": match_query})

        pipeline.extend([
            {"$sort": {"upload_date": -1}},
            {"$skip": skip},
            {"$limit": page_size},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "creator_id",
                    "foreignField": "_id",
                    "as": "creator"
                }
            },
            {
                "$unwind": {
                    "path": "$creator",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$addFields": {
                    "username": "$creator.username"
                }
            },
            {
                "$project": {
                    "creator": 0  # Remove the creator object from response
                }
            }
        ])

        cursor = self.db.photos.aggregate(pipeline)
        photos = await cursor.to_list(length=page_size)

        # Convert ObjectId to string and handle missing usernames
        photo_responses = []
        for photo in photos:
            photo["_id"] = str(photo["_id"])
            if "username" not in photo or photo["username"] is None:
                photo["username"] = "Unknown User"
            photo_responses.append(PhotoResponse(**photo))

        result = PhotoListResponse(
            photos=photo_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

        # Cache the result
        await cache_service.set(cache_key, result.dict())
        logger.info(f"Cached result for {cache_key}")

        return result

    async def get_photo_by_id(self, photo_id: str) -> PhotoResponse:
        """Get photo by ID"""
        # Try to get from cache
        cache_key = f"photo:{photo_id}"
        cached_photo = await cache_service.get(cache_key)
        if cached_photo:
            logger.info(f"Cache hit for photo {photo_id}")
            return PhotoResponse(**cached_photo)

        # Use aggregation to join with users collection
        try:
            pipeline = [
                {"$match": {"_id": ObjectId(photo_id)}},
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "creator_id",
                        "foreignField": "_id",
                        "as": "creator"
                    }
                },
                {
                    "$unwind": {
                        "path": "$creator",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$addFields": {
                        "username": "$creator.username"
                    }
                },
                {
                    "$project": {
                        "creator": 0
                    }
                }
            ]
            cursor = self.db.photos.aggregate(pipeline)
            photos = await cursor.to_list(length=1)
            photo = photos[0] if photos else None
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
        if "username" not in photo or photo["username"] is None:
            photo["username"] = "Unknown User"
        photo_response = PhotoResponse(**photo)

        # Cache the photo
        await cache_service.set(cache_key, photo_response.dict())
        logger.info(f"Cached photo {photo_id}")

        return photo_response

    async def get_creator_photos(self, creator_id: str) -> List[PhotoResponse]:
        """Get all photos by a creator"""
        # Try to get from cache
        cache_key = f"creator_photos:{creator_id}"
        cached_photos = await cache_service.get(cache_key)
        if cached_photos:
            logger.info(f"Cache hit for creator {creator_id} photos")
            return [PhotoResponse(**photo) for photo in cached_photos]

        # Use aggregation to join with users collection
        pipeline = [
            {"$match": {"creator_id": creator_id}},
            {"$sort": {"upload_date": -1}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "creator_id",
                    "foreignField": "_id",
                    "as": "creator"
                }
            },
            {
                "$unwind": {
                    "path": "$creator",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$addFields": {
                    "username": "$creator.username"
                }
            },
            {
                "$project": {
                    "creator": 0
                }
            }
        ]

        cursor = self.db.photos.aggregate(pipeline)
        photos = await cursor.to_list(length=None)

        photo_responses = []
        for photo in photos:
            photo["_id"] = str(photo["_id"])
            if "username" not in photo or photo["username"] is None:
                photo["username"] = "Unknown User"
            photo_responses.append(PhotoResponse(**photo))

        # Cache the creator's photos
        await cache_service.set(cache_key, [photo.dict() for photo in photo_responses])
        logger.info(f"Cached creator {creator_id} photos")

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

        # Get updated photo with username using aggregation
        pipeline = [
            {"$match": {"_id": ObjectId(photo_id)}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "creator_id",
                    "foreignField": "_id",
                    "as": "creator"
                }
            },
            {
                "$unwind": {
                    "path": "$creator",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$addFields": {
                    "username": "$creator.username"
                }
            },
            {
                "$project": {
                    "creator": 0
                }
            }
        ]
        cursor = self.db.photos.aggregate(pipeline)
        photos = await cursor.to_list(length=1)
        updated_photo = photos[0] if photos else None

        if not updated_photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found after update"
            )

        updated_photo["_id"] = str(updated_photo["_id"])
        if "username" not in updated_photo or updated_photo["username"] is None:
            updated_photo["username"] = "Unknown User"

        # Invalidate cache for this photo and related listings
        await cache_service.delete(f"photo:{photo_id}")
        await cache_service.delete_pattern(f"photos:*")
        await cache_service.delete_pattern(f"creator_photos:{creator_id}")

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

        # Invalidate cache for this photo and related listings
        await cache_service.delete(f"photo:{photo_id}")
        await cache_service.delete_pattern(f"photos:*")
        await cache_service.delete_pattern(f"creator_photos:{creator_id}")
        await cache_service.delete_pattern(f"ratings:photo:{photo_id}")

        return True
