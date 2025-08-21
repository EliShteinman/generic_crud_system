# models.py - מודלים גנריים לנתונים
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# סוג המזהה של MongoDB - תמיד מחרוזת ב-JSON
PyObjectId = str

class SortOrder(str, Enum):
    """כיוון המיון - עולה או יורד"""
    ASC = "asc"   # מיון עולה (1, 2, 3...)
    DESC = "desc" # מיון יורד (3, 2, 1...)

class FieldType(str, Enum):
    """סוגי שדות שונים לצורך חיפוש מתקדם"""
    TEXT = "text"           # טקסט רגיל
    NUMBER = "number"       # מספר
    DATE = "date"          # תאריך
    BOOLEAN = "boolean"    # אמת/שקר
    EMAIL = "email"        # כתובת מייל
    PHONE = "phone"        # מספר טלפון
    URL = "url"           # כתובת אתר

class FilterOperator(str, Enum):
    """אופרטורים לחיפוש מתקדם"""
    EQUALS = "eq"              # שווה ל
    NOT_EQUALS = "ne"          # לא שווה ל
    GREATER_THAN = "gt"        # גדול מ
    GREATER_EQUAL = "gte"      # גדול או שווה ל
    LESS_THAN = "lt"          # קטן מ
    LESS_EQUAL = "lte"        # קטן או שווה ל
    CONTAINS = "contains"      # מכיל (עבור טקסט)
    STARTS_WITH = "starts"     # מתחיל ב
    ENDS_WITH = "ends"         # מסתיים ב
    IN = "in"                 # קיים ברשימה
    NOT_IN = "nin"            # לא קיים ברשימה
    REGEX = "regex"           # ביטוי רגולרי
    EXISTS = "exists"         # השדה קיים
    SIZE = "size"            # גודל מערך

# === מודלים בסיסיים לחיפוש ומיון ===

class FilterCondition(BaseModel):
    """תנאי חיפוש יחיד"""
    field: str                                    # שם השדה
    operator: FilterOperator                      # אופרטור החיפוש
    value: Optional[Union[str, int, float, bool, List[Any]]] = None  # הערך לחיפוש
    case_sensitive: bool = False                  # האם רגיש לרישיות (עבור טקסט)

class SortCondition(BaseModel):
    """תנאי מיון יחיד"""
    field: str                    # שם השדה למיון
    order: SortOrder = SortOrder.ASC  # כיוון המיון

class SearchQuery(BaseModel):
    """שאילתת חיפוש כללית"""
    text: Optional[str] = None                    # חיפוש טקסט חופשי
    fields: Optional[List[str]] = None            # שדות לחיפוש בהם (אם לא צוין - חיפוש בכל השדות)
    filters: Optional[List[FilterCondition]] = None  # תנאי חיפוש מתקדמים
    sort: Optional[List[SortCondition]] = None    # תנאי מיון
    page: int = Field(default=1, ge=1)           # מספר עמוד
    limit: int = Field(default=10, ge=1, le=100) # כמות תוצאות בעמוד
    include_count: bool = True                    # האם לכלול ספירה כוללת

class PaginatedResponse(BaseModel):
    """תגובה עם עימוד"""
    data: List[Dict[str, Any]]    # הנתונים עצמם
    total: Optional[int] = None   # סה"כ תוצאות
    page: int                     # עמוד נוכחי
    limit: int                    # תוצאות בעמוד
    pages: Optional[int] = None   # סה"כ עמודים
    has_next: bool = False        # האם יש עמוד הבא
    has_prev: bool = False        # האם יש עמוד קודם

# === מודלים גנריים ל-CRUD ===

class GenericCreate(BaseModel):
    """מודל גנרי ליצירת רשומה חדשה"""
    data: Dict[str, Any]  # הנתונים כמילון פתוח

class GenericUpdate(BaseModel):
    """מודל גנרי לעדכון רשומה"""
    data: Dict[str, Any]  # הנתונים לעדכון

class GenericItem(BaseModel):
    """מודל גנרי לרשומה מהמסד"""
    id: PyObjectId = Field(alias="_id")  # המזהה של MongoDB
    data: Dict[str, Any]                 # הנתונים עצמם
    created_at: Optional[datetime] = None  # זמן יצירה
    updated_at: Optional[datetime] = None  # זמן עדכון אחרון

    class Config:
        from_attributes = True      # יכולת יצירה מאובייקטים
        populate_by_name = True     # תמיכה בשמות שדות ו-alias

class BulkOperation(BaseModel):
    """פעולה בכמות גדולה"""
    operation: str  # סוג הפעולה: "create", "update", "delete"
    items: List[Dict[str, Any]]  # הפריטים לפעולה

class BulkResult(BaseModel):
    """תוצאת פעולה בכמות גדולה"""
    success_count: int = 0      # כמות הצלחות
    error_count: int = 0        # כמות שגיאות
    errors: List[str] = []      # רשימת שגיאות
    inserted_ids: List[str] = [] # מזהים שנוצרו (ליצירה)
    modified_count: int = 0     # כמות שעודכנו
    deleted_count: int = 0      # כמות שנמחקו

class FieldInfo(BaseModel):
    """מידע על שדה בנתונים"""
    name: str                        # שם השדה
    type: FieldType                  # סוג השדה
    required: bool = False           # האם חובה
    unique: bool = False             # האם ייחודי
    searchable: bool = True          # האם ניתן לחיפוש
    sortable: bool = True            # האם ניתן למיון
    description: Optional[str] = None # תיאור השדה

class SchemaInfo(BaseModel):
    """מידע על מבנה הנתונים"""
    collection_name: str             # שם הקולקשן
    fields: List[FieldInfo]          # רשימת השדות
    description: Optional[str] = None # תיאור הקולקשן

class StatisticsResponse(BaseModel):
    """סטטיסטיקות על הקולקשן"""
    total_documents: int = 0         # סה"כ מסמכים
    collection_size_bytes: int = 0   # גודל בבייטים
    average_document_size: float = 0 # גודל ממוצע של מסמך
    indexes_count: int = 0           # כמות אינדקסים
    last_updated: Optional[datetime] = None  # עדכון אחרון

class ValidationRule(BaseModel):
    """כלל אימות לשדה"""
    field: str                       # שם השדה
    rule_type: str                   # סוג הכלל (required, min_length, max_value וכו')
    value: Any                       # ערך הכלל
    message: str                     # הודעת שגיאה

class IndexInfo(BaseModel):
    """מידע על אינדקס"""
    name: str                        # שם האינדקס
    fields: Dict[str, int]           # שדות ומיון (1 עולה, -1 יורד)
    unique: bool = False             # האם ייחודי
    sparse: bool = False             # האם דליל (מתעלם מ-null)
    background: bool = True          # האם ייבנה ברקע

# === מודלים למעקב אחר שינויים ===

class ChangeLog(BaseModel):
    """רישום שינוי"""
    document_id: str                 # מזהה המסמך
    action: str                      # פעולה: create, update, delete
    old_data: Optional[Dict[str, Any]] = None  # נתונים ישנים
    new_data: Optional[Dict[str, Any]] = None  # נתונים חדשים
    timestamp: datetime              # זמן השינוי
    user_id: Optional[str] = None    # מזהה המשתמש שביצע

class ExportFormat(str, Enum):
    """פורמטים לייצוא"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"
    XML = "xml"

class ExportRequest(BaseModel):
    """בקשת ייצוא נתונים"""
    format: ExportFormat             # פורמט הייצוא
    query: Optional[SearchQuery] = None  # שאילתה לייצוא (אם לא צוין - הכל)
    fields: Optional[List[str]] = None   # שדות לייצוא (אם לא צוין - הכל)
    filename: Optional[str] = None       # שם הקובץ

class ImportResult(BaseModel):
    """תוצאת ייבוא"""
    total_rows: int = 0              # סה"כ שורות
    successful_imports: int = 0      # ייבואים מוצלחים
    failed_imports: int = 0          # ייבואים שנכשלו
    errors: List[str] = []           # רשימת שגיאות
    warnings: List[str] = []         # רשימת אזהרות
    duration_seconds: float = 0      # זמן הייבוא

# === מודלים לתצוגות מותאמות אישית ===

class CustomView(BaseModel):
    """תצוגה מותאמת אישית"""
    name: str                        # שם התצוגה
    description: Optional[str] = None # תיאור
    query: SearchQuery               # השאילתה
    fields: Optional[List[str]] = None # שדות להצגה
    created_by: Optional[str] = None  # יוצר התצוגה
    created_at: datetime             # זמן יצירה
    is_public: bool = False          # האם ציבורית

class SavedSearch(BaseModel):
    """חיפוש שמור"""
    name: str                        # שם החיפוש
    query: SearchQuery               # השאילתה השמורה
    created_by: Optional[str] = None  # יוצר החיפוש
    created_at: datetime             # זמן יצירה

# === מודלים לביצועים ומונטורינג ===

class QueryPerformance(BaseModel):
    """ביצועי שאילתה"""
    query_hash: str                  # האש של השאילתה
    execution_time_ms: float         # זמן ביצוע במילישניות
    documents_examined: int          # מסמכים שנבדקו
    documents_returned: int          # מסמכים שהוחזרו
    index_used: Optional[str] = None # האינדקס שנוצל
    timestamp: datetime              # זמן הביצוע

class HealthCheck(BaseModel):
    """בדיקת בריאות המערכת"""
    status: str                      # סטטוס: healthy, degraded, unhealthy
    database_connected: bool         # האם מחובר למסד נתונים
    collections_accessible: bool     # האם הקולקשנים נגישים
    response_time_ms: float          # זמן תגובה
    last_check: datetime             # בדיקה אחרונה

# === מודלים לאבטחה והרשאות ===

class Permission(BaseModel):
    """הרשאה"""
    action: str                      # פעולה: read, write, delete, admin
    resource: str                    # משאב: collection_name או *
    granted: bool = True             # האם מוענקת

class UserRole(BaseModel):
    """תפקיד משתמש"""
    user_id: str                     # מזהה משתמש
    role: str                        # שם התפקיד
    permissions: List[Permission]    # הרשאות
    valid_until: Optional[datetime] = None  # תוקף

class AuditLog(BaseModel):
    """יומן ביקורת"""
    user_id: Optional[str] = None    # מזהה משתמש
    action: str                      # פעולה שבוצעה
    resource: str                    # משאב שהושפע
    details: Dict[str, Any]          # פרטים נוספים
    ip_address: Optional[str] = None # כתובת IP
    user_agent: Optional[str] = None # User Agent
    timestamp: datetime              # זמן הפעולה
    success: bool = True             # האם הפעולה הצליחה

# === הודעות מערכת ===

class SystemMessage(BaseModel):
    """הודעת מערכת"""
    level: str                       # רמת חומרה: info, warning, error, critical
    message: str                     # תוכן ההודעה
    category: str                    # קטגוריה: database, security, performance
    timestamp: datetime              # זמן ההודעה
    resolved: bool = False           # האם נפתרה

class BackupInfo(BaseModel):
    """מידע על גיבוי"""
    backup_id: str                   # מזהה הגיבוי
    collection_name: str             # שם הקולקשן
    created_at: datetime             # זמן יצירת הגיבוי
    size_bytes: int                  # גודל הגיבוי
    document_count: int              # כמות מסמכים
    compression_ratio: float = 1.0   # יחס דחיסה
    status: str                      # סטטוס: created, verified, corrupted

# === תגובות שגיאה מפורטות ===

class ValidationError(BaseModel):
    """שגיאת אימות מפורטת"""
    field: str                       # שדה עם השגיאה
    message: str                     # הודעת השגיאה
    invalid_value: Any               # הערך השגוי
    expected_type: Optional[str] = None  # הסוג הצפוי

class DetailedErrorResponse(BaseModel):
    """תגובת שגיאה מפורטת"""
    error_code: str                  # קוד השגיאה
    message: str                     # הודעה כללית
    details: Optional[str] = None    # פרטים נוספים
    validation_errors: Optional[List[ValidationError]] = None  # שגיאות אימות
    timestamp: datetime              # זמן השגיאה
    request_id: Optional[str] = None # מזהה הבקשה

# === מודלים לתצורה ===

class DatabaseConfig(BaseModel):
    """תצורת מסד נתונים"""
    max_connections: int = 100       # מקסימום חיבורים
    connection_timeout: int = 5000   # timeout בחיבור (מילישניות)
    max_idle_time: int = 30000      # זמן מקסימלי לחיבור idle
    replica_set: Optional[str] = None # שם replica set
    read_preference: str = "primary" # העדפת קריאה

class CacheConfig(BaseModel):
    """תצורת מטמון"""
    enabled: bool = True             # האם המטמון פעיל
    ttl_seconds: int = 300          # זמן שמירה במטמון
    max_size: int = 1000            # גודל מקסימלי
    key_prefix: str = "crud_cache"   # קידומת למפתחות

class SecurityConfig(BaseModel):
    """תצורת אבטחה"""
    require_authentication: bool = False  # האם נדרש אימות
    rate_limit_per_minute: int = 60       # הגבלת קצב בדקה
    enable_audit_log: bool = True         # האם לכתוב יומן ביקורת
    allowed_origins: List[str] = ["*"]    # כתובות מותרות ל-CORS
    max_upload_size_mb: int = 10         # גודל מקסימלי להעלאה