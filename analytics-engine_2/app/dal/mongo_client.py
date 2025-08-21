from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    """מחלקה לניהול החיבור ל-MongoDB"""

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db = None
        self._collection = None

    def connect(self) -> bool:
        """התחברות למסד הנתונים"""
        try:
            self._client = MongoClient(
                settings.MONGODB_URI,
                maxPoolSize=settings.MAX_POOL_SIZE,
                minPoolSize=settings.MIN_POOL_SIZE,
                serverSelectionTimeoutMS=settings.SERVER_SELECTION_TIMEOUT_MS,
                connectTimeoutMS=settings.CONNECT_TIMEOUT_MS
            )

            # בדיקת חיבור
            self._client.admin.command('ping')

            self._db = self._client[settings.DATABASE_NAME]
            self._collection = self._db[settings.COLLECTION_NAME]

            logger.info(f"Successfully connected to MongoDB Atlas: {settings.DATABASE_NAME}")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            return False

    def disconnect(self):
        """ניתוק מהמסד"""
        if self._client:
            self._client.close()
            logger.info("Disconnected from MongoDB")

    def is_connected(self) -> bool:
        """בדיקה האם יש חיבור פעיל"""
        try:
            if self._client:
                self._client.admin.command('ping')
                return True
        except:
            pass
        return False

    @property
    def collection(self):
        """גישה לקולקשן"""
        if not self._collection:
            raise RuntimeError("MongoDB client not connected")
        return self._collection

    @property
    def database(self):
        """גישה למסד הנתונים"""
        if not self._db:
            raise RuntimeError("MongoDB client not connected")
        return self._db


# יצירת אינסטנס יחיד
mongo_client = MongoDBClient()