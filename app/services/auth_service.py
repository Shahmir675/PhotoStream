from fastapi import HTTPException, status
from app.database import get_database
from app.models.user import User, UserRole
from app.schemas.user import UserRegister, UserLogin, Token
from app.utils.security import get_password_hash, verify_password, create_access_token
from bson import ObjectId
from datetime import timedelta


class AuthService:
    def __init__(self):
        self.db = get_database()

    async def register_consumer(self, user_data: UserRegister) -> User:
        """Register a new consumer user"""
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
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "password_hash": get_password_hash(user_data.password),
            "role": UserRole.CONSUMER.value,
        }

        # Add timestamps
        from datetime import datetime
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()

        # Insert user into database
        result = await self.db.users.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)

        return User(**user_dict)

    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return JWT token"""
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
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        except:
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
        return User(**user)
