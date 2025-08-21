import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api.routes import router
from app.dal.mongo_client import mongo_client

# הגדרת logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ניהול מחזור חיי האפליקציה"""
    # Startup
    logger.info("Starting Analytics Engine...")

    # התחברות ל-MongoDB
    if mongo_client.connect():
        logger.info("Successfully connected to MongoDB")
    else:
        logger.error("Failed to connect to MongoDB")

    yield

    # Shutdown
    logger.info("Shutting down Analytics Engine...")
    mongo_client.disconnect()


# יצירת האפליקציה
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# הגדרת CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# הוספת הנתיבים
app.include_router(router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )