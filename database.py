# database.py
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config.config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

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
