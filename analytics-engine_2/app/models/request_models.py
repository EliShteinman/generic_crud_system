from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class SortDirection(str, Enum):
    """כיוון המיון"""
    ASC = "asc"
    DESC = "desc"

class FilterOperator(str, Enum):
    """אופרטורים לסינון"""
    EQ = "eq"      # שווה
    NE = "ne"      # לא שווה
    GT = "gt"      # גדול מ
    GTE = "gte"    # גדול או שווה
    LT = "lt"      # קטן מ
    LTE = "lte"    # קטן או שווה
    IN = "in"      # נמצא ברשימה
    NIN = "nin"    # לא נמצא ברשימה
    EXISTS = "exists"  # קיים
    TYPE = "type"      # סוג השדה
    REGEX = "regex"    # ביטוי רגולרי
    ALL = "all"        # כל הערכים במערך
    SIZE = "size"      # גודל המערך
    ELEM_MATCH = "elem_match"  # התאמת אלמנט במערך

class FilterCondition(BaseModel):
    """תנאי סינון בודד"""
    field: str = Field(..., description="שם השדה")
    operator: FilterOperator = Field(..., description="אופרטור הסינון")
    value: Any = Field(..., description="הערך לסינון")
    options: Optional[Dict[str, Any]] = Field(None, description="אופציות נוספות (למשל עבור regex)")

class OrCondition(BaseModel):
    """תנאי OR מורכב"""
    conditions: List[FilterCondition] = Field(..., description="רשימת תנאי OR")

class SearchCriteria(BaseModel):
    """קריטריונים לחיפוש"""
    filters: List[Union[FilterCondition, OrCondition]] = Field(
        default_factory=list,
        description="רשימת תנאי סינון"
    )
    sort_field: Optional[str] = Field(None, description="שדה למיון")
    sort_direction: Optional[SortDirection] = Field(SortDirection.ASC, description="כיוון המיון")
    limit: Optional[int] = Field(None, description="מספר מקסימלי של תוצאות", ge=1, le=10000)
    skip: Optional[int] = Field(0, description="מספר תוצאות לדילוג", ge=0)

class QueryRequest(BaseModel):
    """בקשת שאילתה ראשית"""
    criteria: SearchCriteria = Field(..., description="קריטריונים לסינון הנתונים")
    analyses: List[str] = Field(
        default_factory=list,
        description="רשימת ניתוחים להרצה"
    )

class HealthResponse(BaseModel):
    """תגובת בדיקת בריאות"""
    status: str
    version: str
    database_connected: bool
    details: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    """תגובת ניתוח"""
    raw_data_count: int = Field(..., description="מספר הרשומות שנמצאו")
    analyses_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="תוצאות הניתוחים"
    )
    execution_time_ms: float = Field(..., description="זמן ביצוע במילישניות")