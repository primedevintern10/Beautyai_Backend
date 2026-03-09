# config/database.py
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config.config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME
from typing import List

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
product_collection = db[COLLECTION_NAME]


async def get_products_collection():
    """FastAPI dependency to inject the products collection into route handlers."""
    return product_collection


async def connect_db():
    """Ping MongoDB to verify the connection. Call this on app startup."""
    try:
        await client.admin.command("ping")
        logger.info(f"Successfully connected to Database: {DATABASE_NAME}")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise


async def close_db():
    """Close the MongoDB connection. Call this on app shutdown."""
    client.close()
    logger.info("MongoDB connection closed.")

# Global cache – fetch only once
_CACHED_CATEGORIES: List[str] = []

async def get_all_categories() -> List[str]:
    """
    Returns all unique values from the 'category' field.
    Caches result after first call.
    """
    global _CACHED_CATEGORIES
    
    if _CACHED_CATEGORIES:
        return _CACHED_CATEGORIES
    
    try:
        collection = await get_products_collection()
        pipeline = [
            {"$group": {"_id": "$category"}},
            {"$sort": {"_id": 1}}
        ]
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        categories = [doc["_id"] for doc in results if doc["_id"] is not None]
        _CACHED_CATEGORIES = sorted(categories)
        
        logger.info(f"Loaded {len(_CACHED_CATEGORIES)} unique categories: {_CACHED_CATEGORIES}")
        return _CACHED_CATEGORIES
        
    except Exception as e:
        logger.error(f"Failed to load categories: {e}")
        return ["face", "hair", "body", "baby"]
