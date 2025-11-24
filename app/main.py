from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.services.cache_service import cache_service
from app.routes import auth, creator, photos, comments, ratings, likes, discovery
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="PhotoStream API",
    description="A scalable cloud-native photo sharing platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add GZip compression for faster responses
app.add_middleware(GZipMiddleware, minimum_size=500)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB and Redis on startup"""
    await connect_to_mongo()
    await cache_service.connect()
    logging.info("PhotoStream API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB and Redis connections on shutdown"""
    await close_mongo_connection()
    await cache_service.disconnect()
    logging.info("PhotoStream API shut down")


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Welcome to PhotoStream API",
        "version": "1.0.0"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    from app.database import get_database

    db_status = "disconnected"
    db_error = None
    cache_status = "disconnected"
    cache_error = None

    try:
        db = get_database()
        if db is None:
            db_status = "disconnected"
            db_error = "Database not initialized"
        else:
            # Actually test the database connection
            await db.command('ping')
            db_status = "connected"
    except Exception as e:
        db_status = "error"
        db_error = f"{type(e).__name__}: {str(e)}"
        logging.error(f"Health check database error: {db_error}")

    # Check Redis cache
    try:
        if cache_service.enabled and cache_service.redis_client:
            await cache_service.redis_client.ping()
            cache_status = "connected"
        else:
            cache_status = "disabled"
    except Exception as e:
        cache_status = "error"
        cache_error = f"{type(e).__name__}: {str(e)}"
        logging.error(f"Health check cache error: {cache_error}")

    response = {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "cache": cache_status,
        "api_version": "1.0.0"
    }

    if db_error:
        response["database_error"] = db_error
    if cache_error:
        response["cache_error"] = cache_error

    return response


# Include routers
app.include_router(auth.router)
app.include_router(creator.router)
app.include_router(photos.router)
app.include_router(comments.router)
app.include_router(ratings.router)
app.include_router(likes.router)
app.include_router(discovery.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
