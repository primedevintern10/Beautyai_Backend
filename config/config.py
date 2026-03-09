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

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_MINI = os.getenv("MODE_MINI", "gpt-4o-mini")
MODEL = os.getenv("MODEL", "gpt-4o")
MODEL_NANO = os.getenv("MODEL_NANO", "gpt-4o-mini")

if not MONGODB_URI:
    logger.critical(
        "MONGODB_URI is not set. "
        f"Expected .env file at: {Path(__file__).parent / '.env'}"
    )
    raise ValueError("MONGODB_URI environment variable is missing – check .env file")
