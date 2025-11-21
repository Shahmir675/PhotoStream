import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.database import database


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup test database before each test"""
    # Use a test database
    test_db_name = "photostream_test"
    database.client = AsyncIOMotorClient(settings.mongodb_url)
    database.db = database.client[test_db_name]

    yield

    # Clean up after test
    await database.client.drop_database(test_db_name)
    database.client.close()
