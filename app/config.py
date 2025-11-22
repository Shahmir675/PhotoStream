from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # MongoDB Settings
    mongodb_url: str
    database_name: str = "photostream"

    # JWT Settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Cloudinary Settings
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    # Redis Settings
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 900  # 15 minutes default cache TTL (increased for better performance)

    # Application Settings
    max_upload_size: int = 10485760  # 10MB
    allowed_image_types: str = "image/jpeg,image/png,image/jpg,image/webp"

    # CORS Settings
    cors_origins: List[str] = ["*"]

    # Regional Routing Settings
    region_name: str = "us-west"
    server_us_west: str = "https://photostream-api-us-west.onrender.com"
    server_us_east: str = "https://photostream-api-us-east.onrender.com"
    server_eu: str = "https://photostream-api-eu.onrender.com"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
