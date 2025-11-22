from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    db = None


database = Database()


async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        database.client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000  # 10 second connection timeout
        )
        database.db = database.client[settings.database_name]

        # Test connection
        await database.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")

        # Create indexes
        try:
            await create_indexes()
        except Exception as index_error:
            logger.error(f"Error creating indexes: {index_error}")
            # Don't fail startup if indexes already exist or have minor issues
            # But still log the error for debugging

    except ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        database.client = None
        database.db = None
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {type(e).__name__}: {e}")
        database.client = None
        database.db = None
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    if database.client:
        database.client.close()
        logger.info("Closed MongoDB connection")


async def create_indexes():
    """Create database indexes for better performance"""
    # Users collection indexes
    await database.db.users.create_index("email", unique=True)
    await database.db.users.create_index("username", unique=True)

    # Photos collection indexes - optimized compound indexes
    await database.db.photos.create_index("creator_id")
    await database.db.photos.create_index([("upload_date", -1)])  # For sorting by latest
    await database.db.photos.create_index([("location", 1), ("upload_date", -1)])  # Location + sort
    await database.db.photos.create_index([("average_rating", -1)])  # For sorting by rating
    await database.db.photos.create_index([("title", "text"), ("caption", "text")])  # Full-text search

    # Compound index for paginated queries
    await database.db.photos.create_index([("upload_date", -1), ("_id", 1)])

    # Comments collection indexes
    await database.db.comments.create_index("photo_id")
    await database.db.comments.create_index("user_id")
    await database.db.comments.create_index([("photo_id", 1), ("created_at", -1)])  # Comments by photo, sorted

    # Ratings collection indexes
    await database.db.ratings.create_index([("photo_id", 1), ("user_id", 1)], unique=True)
    await database.db.ratings.create_index("photo_id")  # For aggregations

    logger.info("Database indexes created successfully")


def get_database():
    """Get database instance"""
    return database.db
