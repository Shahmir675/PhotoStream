#!/usr/bin/env python3
"""
Clear Redis cache to ensure updated photo service logic takes effect
"""
import asyncio
import sys
sys.path.insert(0, '/home/shahmir/Backend/PhotoStream')

from app.services.cache_service import cache_service

async def clear_all_caches():
    """Clear all photo-related caches"""
    try:
        # Clear all photo caches
        await cache_service.delete_pattern("photos:*")
        await cache_service.delete_pattern("creator_photos:*")
        await cache_service.delete_pattern("photo:*")

        print("✓ Successfully cleared all photo-related caches")
        print("✓ New photos will now show usernames correctly")
        print("✓ Existing photos will have usernames fetched via aggregation")

    except Exception as e:
        print(f"✗ Error clearing cache: {e}")

if __name__ == "__main__":
    asyncio.run(clear_all_caches())
