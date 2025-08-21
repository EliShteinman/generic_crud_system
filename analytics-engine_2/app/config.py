import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """הגדרות המערכת"""

    # MongoDB Settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "analytics_db")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "data")

    # API Settings
    API_V1_STR = "/api/v1"
    PROJECT_NAME = "Analytics Engine"
    VERSION = "1.0.0"

    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Connection Pool Settings
    MAX_POOL_SIZE = int(os.getenv("MAX_POOL_SIZE", 100))
    MIN_POOL_SIZE = int(os.getenv("MIN_POOL_SIZE", 10))

    # Timeout Settings
    SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("SERVER_SELECTION_TIMEOUT_MS", 5000))
    CONNECT_TIMEOUT_MS = int(os.getenv("CONNECT_TIMEOUT_MS", 10000))


settings = Settings()