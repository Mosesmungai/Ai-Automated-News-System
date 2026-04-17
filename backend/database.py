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

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017").strip().strip('"').strip("'")
DB_NAME     = os.getenv("DB_NAME", "kenyanews")

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
