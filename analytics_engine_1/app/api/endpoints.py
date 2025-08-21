# app/api/endpoints.py

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Body, status

# ייבוא המודלים של Pydantic נשאר זהה
from .models import QueryRequest, HealthStatus

# ---- שינויים מרכזיים כאן ----
# 1. במקום לייבא מנהל חיבור, אנו מייבאים את מופע ה-DAL המשותף והמוכן.
from ..dependencies import dal

# 2. מייבאים את מנהל הלוגיקה העסקית
from ..processing.pipeline_manager import PipelineManager
# -----------------------------

# הגדרת לוגר לקובץ הנוכחי
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", tags=["Health"])
async def liveness_check():
    """בדיקת Liveness בסיסית - האם השרת חי ומגיב לבקשות HTTP."""
    return {"status": "alive"}


@router.get("/health", response_model=HealthStatus, tags=["Health"])
async def readiness_check():
    """
    בדיקת Readiness מפורטת.
    הבדיקה בודקת אם החיבור למסד הנתונים, שאותחל בעת עליית השרת, אכן הצליח.
    """
    # בדיקה פשוטה ויעילה: האם אובייקט מסד הנתונים ב-DAL קיים?
    # הוא יתקיים רק אם מתודת ה-connect() הצליחה ב-lifespan.
    db_status = "connected" if dal.db is not None else "disconnected"

    if db_status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection failed or is not established."
        )

    return HealthStatus(status="ready", mongodb_connection=db_status)


@router.post("/api/analyze", tags=["Analytics"])
async def analyze_data(request: QueryRequest = Body(...)) -> Dict[str, Any]:
    """
    נקודת הקצה הראשית.
    תפקידה לקבל בקשה, להעביר אותה למנהל הפייפליין לביצוע, ולטפל בשגיאות.
    """
    # בדיקה מקדימה: אם אין חיבור ל-DB, אין טעם להמשיך. נכשל מהר.
    if dal.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready, database connection is unavailable."
        )

    try:
        # יצירת מנהל הלוגיקה, והעברת מופע ה-DAL המשותף אליו.
        # ה-endpoint לא צריך לדעת איך ה-DAL עובד, רק להעביר אותו הלאה.
        pipeline_manager = PipelineManager(
            dal=dal,
            collection=request.collection,
            criteria=request.criteria,
            requested_analyses=request.analyses
        )

        results = await pipeline_manager.run_pipeline()
        return results

    except (ValueError, RuntimeError) as e:
        # תופס שגיאות ידועות מהלוגיקה (למשל "שירות אנליטיקה לא נמצא")
        # ומחזיר שגיאת 400 עם פירוט.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # רשת ביטחון: תופס כל שגיאה אחרת, רושם אותה ללוג,
        # ומחזיר שגיאת 500 כללית כדי לא לחשוף פרטים פנימיים.
        logger.error(f"An unexpected error occurred during analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during analysis."
        )