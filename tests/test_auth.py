import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register_consumer():
    """Test consumer registration"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register-consumer",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["role"] == "consumer"


@pytest.mark.asyncio
async def test_login():
    """Test user login"""
    # First register a user
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/auth/register-consumer",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "password123"
            }
        )

        # Now login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_current_user():
    """Test getting current user info"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login
        await client.post(
            "/api/auth/register-consumer",
            json={
                "email": "current@example.com",
                "username": "currentuser",
                "password": "password123"
            }
        )

        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "current@example.com",
                "password": "password123"
            }
        )

        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "current@example.com"
        assert data["username"] == "currentuser"
