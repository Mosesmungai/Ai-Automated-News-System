"""
KenyaNews — backend/database.py
Async MongoDB connection using Motor (motor==3.4.0).
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_raw_uri = os.getenv("MONGODB_URI", "")
MONGODB_URI = _raw_uri.strip().strip('"').strip("'")
DB_NAME     = os.getenv("DB_NAME", "kenyanews")

if not MONGODB_URI:
    logger.error("CRITICAL: MONGODB_URI is empty or not set in Environment Variables.")
    # Fallback for local dev only if not on Render
    if not os.getenv("RENDER"):
        MONGODB_URI = "mongodb://localhost:27017"

if MONGODB_URI and not (MONGODB_URI.startswith("mongodb://") or MONGODB_URI.startswith("mongodb+srv://")):
    logger.error(f"CRITICAL: MONGODB_URI has an invalid scheme. It starts with: {MONGODB_URI[:10]}...")

client: AsyncIOMotorClient = None


async def connect_db():
    global client
    client = AsyncIOMotorClient(MONGODB_URI)
    logger.info("Connected to MongoDB Atlas.")


async def close_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")


def get_db():
    return client[DB_NAME]


def stories_collection():
    return get_db()["stories"]


def subscribers_collection():
    return get_db()["subscribers"]
