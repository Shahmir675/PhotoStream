"""
Script to create a Creator user account.
Since there's no public interface for creator enrollment,
this script can be used to manually create creator accounts.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_creator(email: str, username: str, password: str):
    """Create a creator user"""
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "photostream")

    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    # Check if user already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        print(f"Error: User with email {email} already exists")
        return

    existing_username = await db.users.find_one({"username": username})
    if existing_username:
        print(f"Error: Username {username} is already taken")
        return

    # Create creator user
    user_dict = {
        "email": email,
        "username": username,
        "password_hash": pwd_context.hash(password),
        "role": "creator",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await db.users.insert_one(user_dict)
    print(f"✓ Creator user created successfully!")
    print(f"  Email: {email}")
    print(f"  Username: {username}")
    print(f"  User ID: {result.inserted_id}")

    client.close()


if __name__ == "__main__":
    print("=== PhotoStream Creator Account Creation ===\n")

    email = input("Enter email: ")
    username = input("Enter username: ")
    password = input("Enter password: ")

    asyncio.run(create_creator(email, username, password))
