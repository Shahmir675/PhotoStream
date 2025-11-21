from fastapi import HTTPException, status
from app.database import get_database
from app.models.user import User, UserRole
from app.schemas.user import UserRegister, UserLogin, Token
from app.utils.security import get_password_hash, verify_password, create_access_token
from bson import ObjectId
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.db = get_database()

    def _check_db(self):
        """Check if database is available"""
        if self.db is None:
            logger.error("Database is not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

    async def register_consumer(self, user_data: UserRegister) -> User:
        """Register a new consumer user"""
        self._check_db()

        # Check if email already exists
        existing_user = await self.db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        existing_username = await self.db.users.find_one({"username": user_data.username})
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Create new user
        from datetime import datetime
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "password_hash": get_password_hash(user_data.password),
            "role": UserRole.CONSUMER.value,  # Store string in DB
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Insert user into database
        result = await self.db.users.insert_one(user_dict)

        # Prepare data for User model (with _id for alias mapping)
        user_dict["_id"] = str(result.inserted_id)

        # Use model_validate which properly handles aliases and type conversion
        return User.model_validate(user_dict)

    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return JWT token"""
        self._check_db()

        # Find user by email
        user = await self.db.users.find_one({"email": login_data.email})

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "role": user["role"]}
        )

        return Token(access_token=access_token)

    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID"""
        self._check_db()

        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user["_id"] = str(user["_id"])
        return User.model_validate(user)

    async def upgrade_to_creator(self, user_id: str) -> User:
        """Upgrade user role to creator"""
        self._check_db()

        from datetime import datetime

        # Update user role
        result = await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "role": UserRole.CREATOR.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get updated user
        return await self.get_user_by_id(user_id)
