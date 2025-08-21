import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from .api import endpoints
from .dependencies import dal  # ייבוא מופע ה-DAL המשותף

# טוען את קובץ ה-.env כדי ש-dependencies.py יוכל לקרוא ממנו
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    מנהל את מחזור החיים של האפליקציה:
    - בעלייה: מתחבר למסד הנתונים.
    - בכיבוי: מתנתק ממסד הנתונים.
    """
    logger.info("Application startup: connecting to database...")
    await dal.connect()

    yield  # כאן האפליקציה רצה

    logger.info("Application shutdown: disconnecting from database...")
    dal.disconnect()


app = FastAPI(
    title="Modular Analytics Engine",
    description="A microservice for on-demand data analysis (Improved Architecture).",
    version="2.0.0",
    lifespan=lifespan  # השימוש ב-lifespan החדש
)

app.include_router(endpoints.router)