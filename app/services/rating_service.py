from fastapi import HTTPException, status
from app.database import get_database
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingResponse, PhotoRatingStats
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class RatingService:
    def __init__(self):
        self.db = get_database()

    def _check_db(self):
        """Check if database is available"""
        if self.db is None:
            logger.error("Database is not initialized in RatingService")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

    async def create_or_update_rating(
        self,
        photo_id: str,
        rating_data: RatingCreate,
        user_id: str
    ) -> RatingResponse:
        """Create or update a rating for a photo"""
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

        # Check if user already rated this photo
        existing_rating = await self.db.ratings.find_one({
            "photo_id": photo_id,
            "user_id": user_id
        })

        from datetime import datetime

        if existing_rating:
            # Update existing rating
            await self.db.ratings.update_one(
                {"_id": existing_rating["_id"]},
                {"$set": {"rating": rating_data.rating, "created_at": datetime.utcnow()}}
            )
            rating_id = existing_rating["_id"]
        else:
            # Create new rating
            rating_dict = {
                "photo_id": photo_id,
                "user_id": user_id,
                "rating": rating_data.rating,
                "created_at": datetime.utcnow()
            }

            result = await self.db.ratings.insert_one(rating_dict)
            rating_id = result.inserted_id

        # Update photo's average rating
        await self._update_photo_rating(photo_id)

        # Get the rating to return
        rating = await self.db.ratings.find_one({"_id": rating_id})
        rating["_id"] = str(rating["_id"])

        return RatingResponse(**rating)

    async def get_photo_rating_stats(self, photo_id: str) -> PhotoRatingStats:
        """Get rating statistics for a photo"""
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

        # Get all ratings for this photo
        cursor = self.db.ratings.find({"photo_id": photo_id})
        ratings = await cursor.to_list(length=None)

        # Calculate statistics
        total_ratings = len(ratings)
        if total_ratings == 0:
            return PhotoRatingStats(
                average_rating=0.0,
                total_ratings=0,
                rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            )

        # Calculate average
        total_score = sum(r["rating"] for r in ratings)
        average_rating = round(total_score / total_ratings, 2)

        # Calculate distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            rating_distribution[rating["rating"]] += 1

        return PhotoRatingStats(
            average_rating=average_rating,
            total_ratings=total_ratings,
            rating_distribution=rating_distribution
        )

    async def _update_photo_rating(self, photo_id: str):
        """Update photo's average rating and total ratings count"""
        # Get all ratings for this photo
        cursor = self.db.ratings.find({"photo_id": photo_id})
        ratings = await cursor.to_list(length=None)

        total_ratings = len(ratings)
        if total_ratings == 0:
            average_rating = 0.0
        else:
            total_score = sum(r["rating"] for r in ratings)
            average_rating = round(total_score / total_ratings, 2)

        # Update photo document
        await self.db.photos.update_one(
            {"_id": ObjectId(photo_id)},
            {"$set": {
                "average_rating": average_rating,
                "total_ratings": total_ratings
            }}
        )
