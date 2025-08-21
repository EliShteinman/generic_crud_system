# app/api/models.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


# ===================================================================
# ===  חלק 1: מודלים להגדרת הסינון, המיון והדיפדוף (Criteria)  ====
# ===================================================================
# מודלים אלו נשארים ללא שינוי. הם מגדירים את החלק של ה"איפה" בשאילתה.

class FilterCriterion(BaseModel):
    """מייצג תנאי סינון בודד, למשל: שדה 'revenue' גדול מ- 500."""
    field: str = Field(..., description="השדה עליו יתבצע הסינון")
    operator: str = Field(..., description="האופרטור לסינון (eq, gt, regex, in, וכו')")
    value: Any = Field(..., description="הערך להשוואה")


class SortCriterion(BaseModel):
    """מייצג תנאי מיון בודד, למשל: למיין לפי שדה 'revenue' בסדר יורד."""
    field: str = Field(..., description="השדה לפיו יתבצע המיון")
    direction: int = Field(1, description="כיוון המיון: 1 לעולה, -1 ליורד")


class SearchCriteria(BaseModel):
    """אוסף את כל קריטריוני השליפה מה-DB."""
    filters: Optional[List[FilterCriterion]] = None
    or_conditions: Optional[List[Dict[str, Any]]] = None
    sort: Optional[List[SortCriterion]] = None
    limit: Optional[int] = 100
    skip: Optional[int] = 0


# ===================================================================
# ===   חלק 2: מודלים להגדרת הניתוחים והבקשה כולה (Analysis)   ====
# ===================================================================
# כאן נמצא השדרוג המרכזי.

class AnalysisRequest(BaseModel):
    """
    מייצג בקשה להרצת ניתוח אחד ספציפי, כולל הפרמטרים שלו.
    זה מאפשר להפוך את שירותי הניתוח לגנריים ודינמיים.
    """
    name: str = Field(..., description="שם הניתוח הרשום להרצה (למשל, 'group_and_aggregate')")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="מילון גמיש של פרמטרים ספציפיים לניתוח. למשל: {'group_by_column': 'city'}"
    )


class QueryRequest(BaseModel):
    """
    המודל הראשי והסופי של גוף הבקשה (Request Body).
    הוא מחבר את כל החלקים יחד.
    """
    collection: str = Field(..., description="שם האוסף (collection) ב-MongoDB שעליו תרוץ השאילתה")
    criteria: SearchCriteria = Field(default_factory=SearchCriteria,
                                     description="קריטריונים לסינון, מיון ודפדוף הנתונים לפני הניתוח")

    # השדרוג המרכזי:
    # במקום רשימה פשוטה של שמות, זוהי רשימה של אובייקטי AnalysisRequest.
    analyses: List[AnalysisRequest] = Field(..., description="רשימת הניתוחים להרצה על הנתונים המסוננים")


# ===================================================================
# ===                  חלק 3: מודלים נוספים (Health)             ====
# ===================================================================
# מודל זה נשאר ללא שינוי.

class HealthStatus(BaseModel):
    """מייצג את מבנה התשובה של נקודת הקצה /health."""
    status: str
    mongodb_connection: str