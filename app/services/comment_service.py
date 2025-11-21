from fastapi import HTTPException, status
from app.database import get_database
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from bson import ObjectId
from typing import List
import logging

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self):
        self.db = get_database()

    def _check_db(self):
        """Check if database is available"""
        if self.db is None:
            logger.error("Database is not initialized in CommentService")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

    async def create_comment(
        self,
        photo_id: str,
        comment_data: CommentCreate,
        user_id: str,
        username: str
    ) -> CommentResponse:
        """Create a new comment"""
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

        # Create comment document
        from datetime import datetime
        comment_dict = {
            "photo_id": photo_id,
            "user_id": user_id,
            "username": username,
            "content": comment_data.content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Insert into database
        result = await self.db.comments.insert_one(comment_dict)
        comment_dict["_id"] = str(result.inserted_id)

        return CommentResponse(**comment_dict)

    async def get_photo_comments(self, photo_id: str) -> CommentListResponse:
        """Get all comments for a photo"""
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

        # Get comments
        cursor = self.db.comments.find({"photo_id": photo_id}).sort("created_at", -1)
        comments = await cursor.to_list(length=None)

        # Convert ObjectId to string
        comment_responses = []
        for comment in comments:
            comment["_id"] = str(comment["_id"])
            comment_responses.append(CommentResponse(**comment))

        return CommentListResponse(
            comments=comment_responses,
            total=len(comment_responses)
        )
