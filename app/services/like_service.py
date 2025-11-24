from fastapi import HTTPException, status
from app.database import get_database
from app.models.like import Like
from app.schemas.like import LikeResponse, PhotoLikeStats
from app.services.cache_service import cache_service
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class LikeService:
    def __init__(self):
        self.db = get_database()

    def _check_db(self):
        """Check if database is available"""
        if self.db is None:
            logger.error("Database is not initialized in LikeService")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

    async def toggle_like(
        self,
        photo_id: str,
        user_id: str
    ) -> LikeResponse:
        """Toggle like for a photo (like if not liked, unlike if already liked)"""
        # Check if photo exists
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

        # Check if user already liked this photo
        existing_like = await self.db.likes.find_one({
            "photo_id": photo_id,
            "user_id": user_id
        })

        from datetime import datetime

        if existing_like:
            # Unlike: Delete the like
            await self.db.likes.delete_one({"_id": existing_like["_id"]})
            liked = False
            like_id = existing_like["_id"]
        else:
            # Like: Create new like
            like_dict = {
                "photo_id": photo_id,
                "user_id": user_id,
                "liked": True,
                "created_at": datetime.utcnow()
            }

            result = await self.db.likes.insert_one(like_dict)
            like_id = result.inserted_id
            liked = True

        # Update photo's total likes count
        await self._update_photo_likes(photo_id)

        # Invalidate cache for photo like stats and photo details
        await cache_service.delete(f"likes:photo:{photo_id}")
        await cache_service.delete(f"photo:{photo_id}")
        await cache_service.delete_pattern(f"photos:*")

        return LikeResponse(
            _id=str(like_id),
            photo_id=photo_id,
            user_id=user_id,
            liked=liked
        )

    async def get_photo_like_stats(self, photo_id: str, user_id: str) -> PhotoLikeStats:
        """Get like statistics for a photo"""
        # Check if photo exists
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

        # Get total likes count
        total_likes = await self.db.likes.count_documents({"photo_id": photo_id})

        # Check if current user has liked this photo
        user_like = await self.db.likes.find_one({
            "photo_id": photo_id,
            "user_id": user_id
        })
        user_has_liked = user_like is not None

        stats = PhotoLikeStats(
            total_likes=total_likes,
            user_has_liked=user_has_liked
        )

        return stats

    async def _update_photo_likes(self, photo_id: str):
        """Update photo's total likes count"""
        # Get total likes for this photo
        total_likes = await self.db.likes.count_documents({"photo_id": photo_id})

        # Update photo document
        await self.db.photos.update_one(
            {"_id": ObjectId(photo_id)},
            {"$set": {"total_likes": total_likes}}
        )
