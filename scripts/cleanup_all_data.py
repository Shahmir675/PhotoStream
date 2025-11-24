#!/usr/bin/env python3
"""
Script to clean all data from PhotoStream application
- Removes all MongoDB collections (users, photos, comments, ratings)
- Deletes all images from Cloudinary
- Clears Redis cache
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import cloudinary
import cloudinary.api
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def clear_mongodb():
    """Clear all MongoDB collections"""
    print("\n=== Clearing MongoDB ===")

    mongodb_url = os.getenv('MONGODB_URL')
    database_name = os.getenv('DATABASE_NAME', 'photostream')

    if not mongodb_url:
        print("❌ MONGODB_URL not found in environment variables")
        return False

    try:
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=5000)
        db = client[database_name]

        # Test connection
        await client.admin.command('ping')
        print(f"✓ Connected to MongoDB database: {database_name}")

        # Get all collections
        collections = await db.list_collection_names()
        print(f"Found {len(collections)} collections: {', '.join(collections)}")

        # Drop each collection
        for collection_name in collections:
            count = await db[collection_name].count_documents({})
            if count > 0:
                await db[collection_name].delete_many({})
                print(f"✓ Cleared {count} documents from '{collection_name}'")
            else:
                print(f"✓ Collection '{collection_name}' was already empty")

        client.close()
        print("✓ MongoDB cleanup completed")
        return True

    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    except Exception as e:
        print(f"❌ Error clearing MongoDB: {e}")
        return False


def clear_cloudinary():
    """Delete all images from Cloudinary"""
    print("\n=== Clearing Cloudinary ===")

    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')

    if not all([cloud_name, api_key, api_secret]):
        print("❌ Cloudinary credentials not found in environment variables")
        return False

    try:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )

        # Get all resources
        resources = cloudinary.api.resources(max_results=500, type='upload')
        total = resources.get('total_count', 0)

        print(f"Found {total} images in Cloudinary")

        if total == 0:
            print("✓ Cloudinary is already empty")
            return True

        # Delete all resources
        deleted_count = 0
        while True:
            resources = cloudinary.api.resources(max_results=100, type='upload')
            if not resources.get('resources'):
                break

            for resource in resources['resources']:
                public_id = resource['public_id']
                cloudinary.uploader.destroy(public_id)
                deleted_count += 1
                print(f"✓ Deleted image: {public_id} ({deleted_count}/{total})")

        print(f"✓ Deleted {deleted_count} images from Cloudinary")
        return True

    except Exception as e:
        print(f"❌ Error clearing Cloudinary: {e}")
        return False


def clear_redis():
    """Clear Redis cache"""
    print("\n=== Clearing Redis ===")

    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

    try:
        # Parse Redis URL
        r = redis.from_url(redis_url)

        # Test connection
        r.ping()
        print(f"✓ Connected to Redis: {redis_url}")

        # Get number of keys
        keys_count = r.dbsize()
        print(f"Found {keys_count} keys in Redis")

        if keys_count > 0:
            r.flushdb()
            print(f"✓ Cleared {keys_count} keys from Redis")
        else:
            print("✓ Redis was already empty")

        r.close()
        return True

    except redis.exceptions.ConnectionError as e:
        print(f"⚠️  Could not connect to Redis: {e}")
        print("   (This is OK if Redis is not running)")
        return True
    except Exception as e:
        print(f"❌ Error clearing Redis: {e}")
        return False


async def main():
    """Main cleanup function"""
    print("=" * 60)
    print("PhotoStream Data Cleanup Script")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete ALL data from:")
    print("   - All MongoDB collections (users, photos, comments, ratings)")
    print("   - All images from Cloudinary")
    print("   - All Redis cache")
    print("\nThis action CANNOT be undone!")
    print("=" * 60)

    # Confirm action
    response = input("\nType 'DELETE ALL' to confirm: ")
    if response != 'DELETE ALL':
        print("\n❌ Cleanup cancelled")
        return

    print("\n🚀 Starting cleanup process...\n")

    # Run cleanup tasks
    results = []

    # Clear MongoDB
    results.append(await clear_mongodb())

    # Clear Cloudinary
    results.append(clear_cloudinary())

    # Clear Redis
    results.append(clear_redis())

    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL DATA HAS BEEN SUCCESSFULLY DELETED")
        print("✓ Your PhotoStream application now has a clean slate")
    else:
        print("⚠️  Cleanup completed with some errors (see above)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
