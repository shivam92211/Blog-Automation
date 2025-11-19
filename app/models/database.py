"""
MongoDB connection and session management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, ASCENDING, DESCENDING
from contextlib import contextmanager
from typing import Generator
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# Synchronous MongoDB client (for scripts and sync operations)
_sync_client = None
_sync_db = None

# Async MongoDB client (for FastAPI async operations)
_async_client = None
_async_db = None


def get_sync_client() -> MongoClient:
    """Get synchronous MongoDB client"""
    global _sync_client
    if _sync_client is None:
        _sync_client = MongoClient(
            settings.MONGODB_URL,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT
        )
    return _sync_client


def get_sync_db():
    """Get synchronous MongoDB database"""
    global _sync_db
    if _sync_db is None:
        client = get_sync_client()
        _sync_db = client[settings.MONGODB_DB_NAME]
    return _sync_db


def get_async_client() -> AsyncIOMotorClient:
    """Get async MongoDB client (for FastAPI)"""
    global _async_client
    if _async_client is None:
        _async_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT
        )
    return _async_client


def get_async_db():
    """Get async MongoDB database (for FastAPI)"""
    global _async_db
    if _async_db is None:
        client = get_async_client()
        _async_db = client[settings.MONGODB_DB_NAME]
    return _async_db


@contextmanager
def get_db() -> Generator:
    """
    Context manager for MongoDB database operations (synchronous)
    Used in jobs and scripts
    """
    db = get_sync_db()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise


def init_db():
    """
    Initialize MongoDB collections and indexes
    """
    logger.info("Initializing MongoDB database...")
    db = get_sync_db()

    # Create collections if they don't exist
    existing_collections = db.list_collection_names()

    collections = [
        "categories",
        "topics",
        "blogs",
        "generation_history",
        "logs"
    ]

    for collection in collections:
        if collection not in existing_collections:
            db.create_collection(collection)
            logger.info(f"✓ Created collection: {collection}")

    # Create indexes for optimal performance
    _create_indexes(db)

    logger.info("✓ MongoDB database initialized")


def _create_indexes(db):
    """Create indexes for all collections"""
    logger.info("Creating indexes...")

    # Categories indexes
    db.categories.create_index([("name", ASCENDING)], unique=True)
    db.categories.create_index([("is_active", ASCENDING)])
    db.categories.create_index([("last_used_date", ASCENDING)])

    # Topics indexes
    db.topics.create_index([("category_id", ASCENDING)])
    db.topics.create_index([("status", ASCENDING)])
    db.topics.create_index([("scheduled_date", ASCENDING)])
    db.topics.create_index([("scheduled_date", ASCENDING), ("status", ASCENDING)])

    # Blogs indexes
    db.blogs.create_index([("topic_id", ASCENDING)], unique=True)
    db.blogs.create_index([("status", ASCENDING)])
    db.blogs.create_index([("hashnode_post_id", ASCENDING)])

    # Generation History indexes
    db.generation_history.create_index([("category_id", ASCENDING)])
    db.generation_history.create_index([("topic_hash", ASCENDING)])
    db.generation_history.create_index([("generated_at", DESCENDING)])

    # Logs indexes
    db.logs.create_index([("job_type", ASCENDING)])
    db.logs.create_index([("status", ASCENDING)])
    db.logs.create_index([("created_at", DESCENDING)])

    logger.info("✓ Indexes created")


def close_connections():
    """Close all MongoDB connections"""
    global _sync_client, _async_client, _sync_db, _async_db

    if _sync_client:
        _sync_client.close()
        _sync_client = None
        _sync_db = None
        logger.info("✓ Closed sync MongoDB connection")

    if _async_client:
        _async_client.close()
        _async_client = None
        _async_db = None
        logger.info("✓ Closed async MongoDB connection")
