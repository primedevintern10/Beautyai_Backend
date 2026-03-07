# config/config.py
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv(Path(__file__).parent / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "BeautyMartDB")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "products")


if not MONGODB_URI:
    logger.critical(
        "MONGODB_URI is not set. "
        f"Expected .env file at: {Path(__file__).parent / '.env'}"
    )
    raise ValueError("MONGODB_URI environment variable is missing – check .env file")
