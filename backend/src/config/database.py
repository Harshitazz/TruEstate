import os
from typing import Optional
import logging
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

class DatabaseClient:
    client: Optional[MongoClient] = None
    db: Optional[Database] = None
    collection: Optional[Collection] = None

database = DatabaseClient()

async def connect_to_mongo():
    """Connect to MongoDB Atlas"""
    try:
        mongo_uri = os.getenv(
            "MONGODB_URI"        )
        database_name = os.getenv("MONGODB_DATABASE")
        collection_name = os.getenv("MONGODB_COLLECTION")
        
        logger.info(f"Connecting to MongoDB: {database_name}.{collection_name}")
        
        database.client = MongoClient(mongo_uri)
        
        database.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        database.db = database.client[database_name]
        database.collection = database.db[collection_name]
        
        count = database.collection.count_documents({})
        logger.info(f"MongoDB connection established. Collection '{collection_name}' has {count:,} documents")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    try:
        if database.client:
            database.client.close()
            logger.info("MongoDB connection closed")
            database.client = None
            database.db = None
            database.collection = None
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {str(e)}", exc_info=True)

def get_collection() -> Collection:
    """Get the MongoDB collection"""
    if database.collection is None:
        raise ValueError("MongoDB not connected. Make sure connect_to_mongo() was called.")
    return database.collection
