# dependencies.py - ניהול תלויות ותצורה מרכזי
import os
import logging
from typing import Optional
from .dal import GenericDataLoader

logger = logging.getLogger(__name__)

# === קריאת הגדרות מסביבת ההפעלה ===

# הגדרות MongoDB
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "generic_crud_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "items")

# הגדרות אבטחה
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
API_KEY = os.getenv("API_KEY", "")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# הגדרות ביצועים
MAX_ITEMS_PER_REQUEST = int(os.getenv("MAX_ITEMS_PER_REQUEST", 1000))
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 50))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 300))

# הגדרות לוגים
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# === בניית URI לחיבור MongoDB ===

def build_mongo_uri() -> str:
    """
    בניית URI לחיבור MongoDB
    תומך הן בסביבת פיתוח (ללא אימות) והן בפרודקשן (עם אימות)

    Returns:
        str: URI מלא לחיבור
    """
    try:
        if MONGO_USER and MONGO_PASSWORD:
            # סביבת פרודקשן עם אימות
            uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
            logger.info(f"נבנה MongoDB URI עם אימות עבור {MONGO_HOST}:{MONGO_PORT}")
        else:
            # סביבת פיתוח ללא אימות
            uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
            logger.info(f"נבנה MongoDB URI ללא אימות עבור {MONGO_HOST}:{MONGO_PORT}")

        return uri

    except Exception as e:
        logger.error(f"שגיאה בבניית MongoDB URI: {e}")
        # URI ברירת מחדל במקרה של שגיאה
        return "mongodb://localhost:27017/"


# בניית ה-URI
MONGO_URI = build_mongo_uri()


# === יצירת מופע יחיד (Singleton) של GenericDataLoader ===

def create_data_loader() -> GenericDataLoader:
    """
    יצירת מופע של GenericDataLoader עם ההגדרות הנוכחיות

    Returns:
        GenericDataLoader: מופע מוכן לשימוש
    """
    try:
        loader = GenericDataLoader(
            mongo_uri=MONGO_URI,
            db_name=MONGO_DB_NAME,
            collection_name=MONGO_COLLECTION_NAME
        )

        # הגדרת פרמטרים נוספים
        loader.max_bulk_size = min(MAX_ITEMS_PER_REQUEST, 1000)  # הגבלה לביטחון
        loader.cache_ttl = CACHE_TTL_SECONDS

        logger.info(f"נוצר GenericDataLoader עבור DB: {MONGO_DB_NAME}, Collection: {MONGO_COLLECTION_NAME}")
        return loader

    except Exception as e:
        logger.error(f"שגיאה ביצירת GenericDataLoader: {e}")
        raise


# יצירת המופע הגלובלי
data_loader = create_data_loader()


# === פונקציות עזר לתצורה ===

def get_database_config() -> dict:
    """
    קבלת תצורת המסד הנוכחית

    Returns:
        dict: מילון עם פרטי התצורה
    """
    return {
        "host": MONGO_HOST,
        "port": MONGO_PORT,
        "database": MONGO_DB_NAME,
        "collection": MONGO_COLLECTION_NAME,
        "auth_enabled": bool(MONGO_USER and MONGO_PASSWORD),
        "max_items_per_request": MAX_ITEMS_PER_REQUEST,
        "default_page_size": DEFAULT_PAGE_SIZE,
        "cache_ttl": CACHE_TTL_SECONDS
    }


def get_security_config() -> dict:
    """
    קבלת תצורת האבטחה הנוכחית

    Returns:
        dict: מילון עם הגדרות אבטחה
    """
    return {
        "auth_enabled": ENABLE_AUTH,
        "api_key_set": bool(API_KEY),
        "cors_origins": CORS_ORIGINS,
        "log_level": LOG_LEVEL
    }


def validate_configuration() -> dict:
    """
    אימות תקינות התצורה

    Returns:
        dict: תוצאות האימות
    """
    issues = []
    warnings = []

    # בדיקת הגדרות MongoDB
    if not MONGO_HOST:
        issues.append("MONGO_HOST לא מוגדר")

    if not MONGO_DB_NAME:
        issues.append("MONGO_DB_NAME לא מוגדר")

    if not MONGO_COLLECTION_NAME:
        issues.append("MONGO_COLLECTION_NAME לא מוגדר")

    # בדיקת אבטחה
    if ENABLE_AUTH and not API_KEY:
        warnings.append("אימות מופעל אבל API_KEY לא מוגדר")

    if MONGO_USER and not MONGO_PASSWORD:
        issues.append("שם משתמש מוגדר אבל סיסמה חסרה")

    if MONGO_PASSWORD and not MONGO_USER:
        issues.append("סיסמה מוגדרת אבל שם משתמש חסר")

    # בדיקת הגדרות ביצועים
    if MAX_ITEMS_PER_REQUEST > 10000:
        warnings.append("MAX_ITEMS_PER_REQUEST גבוה מדי - עלול לגרום לבעיות ביצועים")

    if DEFAULT_PAGE_SIZE > 200:
        warnings.append("DEFAULT_PAGE_SIZE גבוה מדי - מומלץ להקטין")

    # בדיקת לוג level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL not in valid_log_levels:
        warnings.append(f"LOG_LEVEL לא תקין: {LOG_LEVEL}. תקינים: {valid_log_levels}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "total_issues": len(issues),
        "total_warnings": len(warnings)
    }


def update_collection(new_collection_name: str) -> bool:
    """
    עדכון הקולקשן הפעיל

    Args:
        new_collection_name: שם הקולקשן החדש

    Returns:
        bool: האם העדכון הצליח
    """
    try:
        global data_loader
        data_loader.set_collection(new_collection_name)

        # עדכון משתנה הסביבה
        global MONGO_COLLECTION_NAME
        MONGO_COLLECTION_NAME = new_collection_name

        logger.info(f"עבר לקולקשן חדש: {new_collection_name}")
        return True

    except Exception as e:
        logger.error(f"שגיאה בעדכון קולקשן: {e}")
        return False


def reconnect_database() -> bool:
    """
    התחברות מחדש למסד הנתונים

    Returns:
        bool: האם ההתחברות הצליחה
    """
    try:
        global data_loader

        # ניתוק קיים
        await data_loader.disconnect()

        # התחברות מחדש
        success = await data_loader.connect()

        if success:
            logger.info("התחברות מחדש למסד הנתונים הצליחה")
        else:
            logger.error("התחברות מחדש למסד הנתונים נכשלה")

        return success

    except Exception as e:
        logger.error(f"שגיאה בהתחברות מחדש: {e}")
        return False


def get_environment_info() -> dict:
    """
    קבלת מידע על סביבת ההפעלה

    Returns:
        dict: מידע על הסביבה
    """
    import platform
    import sys
    from datetime import datetime

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "hostname": platform.node(),
        "current_time": datetime.now().isoformat(),
        "environment_variables": {
            "MONGO_HOST": MONGO_HOST,
            "MONGO_PORT": MONGO_PORT,
            "MONGO_DB_NAME": MONGO_DB_NAME,
            "MONGO_COLLECTION_NAME": MONGO_COLLECTION_NAME,
            "LOG_LEVEL": LOG_LEVEL,
            "ENABLE_AUTH": ENABLE_AUTH,
            # לא מציגים סיסמאות מטעמי אבטחה
            "MONGO_USER_SET": bool(MONGO_USER),
            "MONGO_PASSWORD_SET": bool(MONGO_PASSWORD),
            "API_KEY_SET": bool(API_KEY)
        }
    }


def setup_logging():
    """
    הגדרת מערכת הלוגים
    """
    try:
        # המרת level string לאובייקט logging
        numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)

        # הגדרת format מפורט
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # הגדרת handler לקונסול
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)

        # הגדרת root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # הסרת handlers קיימים למניעת כפילויות
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addHandler(console_handler)

        logger.info(f"מערכת לוגים הוגדרה ברמה: {LOG_LEVEL}")

    except Exception as e:
        print(f"שגיאה בהגדרת מערכת לוגים: {e}")


# === פונקציות אתחול ===

async def initialize_system() -> dict:
    """
    אתחול מערכת מלא

    Returns:
        dict: תוצאות האתחול
    """
    try:
        logger.info("מתחיל אתחול מערכת...")

        # הגדרת לוגים
        setup_logging()

        # אימות תצורה
        config_validation = validate_configuration()
        if not config_validation["valid"]:
            logger.error(f"תצורה לא תקינה: {config_validation['issues']}")
            return {
                "success": False,
                "message": "תצורה לא תקינה",
                "details": config_validation
            }

        if config_validation["warnings"]:
            logger.warning(f"אזהרות תצורה: {config_validation['warnings']}")

        # התחברות למסד נתונים
        db_connected = await data_loader.connect()
        if not db_connected:
            logger.error("נכשל בהתחברות למסד נתונים")
            return {
                "success": False,
                "message": "נכשל בהתחברות למסד נתונים"
            }

        logger.info("אתחול מערכת הושלם בהצלחה")
        return {
            "success": True,
            "message": "אתחול מערכת הושלם בהצלחה",
            "database_connected": True,
            "config_validation": config_validation,
            "environment": get_environment_info()
        }

    except Exception as e:
        logger.error(f"שגיאה באתחול מערכת: {e}")
        return {
            "success": False,
            "message": f"שגיאה באתחול מערכת: {str(e)}"
        }


async def shutdown_system():
    """
    כיבוי מערכת נקי
    """
    try:
        logger.info("מתחיל כיבוי מערכת...")

        # ניתוק מהמסד
        await data_loader.disconnect()

        logger.info("כיבוי מערכת הושלם")

    except Exception as e:
        logger.error(f"שגיאה בכיבוי מערכת: {e}")


# === משתנים גלובליים נוספים למבחן ===

# רשימת קולקשנים נפוצים למבחן
COMMON_COLLECTIONS = [
    "students",  # סטודנטים
    "courses",  # קורסים
    "products",  # מוצרים
    "orders",  # הזמנות
    "users",  # משתמשים
    "books",  # ספרים
    "movies",  # סרטים
    "employees",  # עובדים
    "customers",  # לקוחות
    "inventory"  # מלאי
]

# טמפלייטים לנתונים במבחן
DATA_TEMPLATES = {
    "student": {
        "first_name": "שם_פרטי",
        "last_name": "שם_משפחה",
        "student_id": "מספר_סטודנט",
        "email": "אימייל",
        "phone": "טלפון",
        "grade": "ציון",
        "course": "קורס",
        "year": "שנה",
        "active": True
    },
    "product": {
        "name": "שם_מוצר",
        "category": "קטגוריה",
        "price": 0.0,
        "stock": 0,
        "description": "תיאור",
        "supplier": "ספק",
        "active": True,
        "tags": []
    },
    "employee": {
        "first_name": "שם_פרטי",
        "last_name": "שם_משפחה",
        "employee_id": "מספר_עובד",
        "department": "מחלקה",
        "position": "תפקיד",
        "salary": 0.0,
        "hire_date": "תאריך_קליטה",
        "email": "אימייל",
        "phone": "טלפון",
        "active": True
    },
    "book": {
        "title": "כותרת",
        "author": "מחבר",
        "isbn": "מספר_ISBN",
        "publisher": "הוצאה",
        "year": "שנת_הוצאה",
        "pages": 0,
        "genre": "ז'אנר",
        "price": 0.0,
        "available": True
    },
    "generic": {
        "name": "שם",
        "type": "סוג",
        "value": "ערך",
        "category": "קטגוריה",
        "description": "תיאור",
        "active": True,
        "tags": [],
        "metadata": {}
    }
}


def get_data_template(template_name: str) -> dict:
    """
    קבלת טמפלייט לנתונים

    Args:
        template_name: שם הטמפלייט

    Returns:
        dict: הטמפלייט
    """
    return DATA_TEMPLATES.get(template_name, DATA_TEMPLATES["generic"]).copy()


def create_sample_data(template_name: str, count: int = 5) -> list:
    """
    יצירת נתוני דוגמה

    Args:
        template_name: שם הטמפלייט
        count: כמות רשומות ליצירה

    Returns:
        list: רשימת נתוני דוגמה
    """
    import random
    from datetime import datetime, timedelta

    template = get_data_template(template_name)
    sample_data = []

    for i in range(count):
        data = template.copy()

        # מילוי ערכים לדוגמה
        for key, value in data.items():
            if isinstance(value, str):
                if "שם" in value or "name" in value.lower():
                    data[key] = f"{value}_{i + 1}"
                elif "מספר" in value or "id" in value.lower():
                    data[key] = f"{random.randint(1000, 9999)}{i + 1}"
                elif "אימייל" in value or "email" in value.lower():
                    data[key] = f"user{i + 1}@example.com"
                elif "טלפון" in value or "phone" in value.lower():
                    data[key] = f"05{random.randint(10000000, 99999999)}"
                elif "תאריך" in value or "date" in value.lower():
                    random_date = datetime.now() - timedelta(days=random.randint(1, 365))
                    data[key] = random_date.isoformat()
                else:
                    data[key] = f"{value}_{i + 1}"
            elif isinstance(value, (int, float)) and value == 0:
                data[key] = random.randint(1, 1000)
            elif isinstance(value, list):
                data[key] = [f"tag{j}" for j in range(random.randint(1, 3))]
            elif isinstance(value, dict):
                data[key] = {"sample_key": f"sample_value_{i + 1}"}

        sample_data.append(data)

    return sample_data


# === פונקציות למבחן ===

async def setup_test_environment(collection_name: str = "test_collection") -> dict:
    """
    הכנת סביבת מבחן

    Args:
        collection_name: שם הקולקשן למבחן

    Returns:
        dict: תוצאות ההכנה
    """
    try:
        logger.info(f"מכין סביבת מבחן עבור קולקשן: {collection_name}")

        # עדכון קולקשן פעיל
        success = update_collection(collection_name)
        if not success:
            return {"success": False, "message": "נכשל בעדכון קולקשן"}

        # יצירת הקולקשן אם לא קיים
        collections = await data_loader.list_collections()
        if collection_name not in collections:
            created = await data_loader.create_collection(collection_name)
            if not created:
                return {"success": False, "message": "נכשל ביצירת קולקשן"}

        # מילוי בנתוני דוגמה
        sample_data = create_sample_data("generic", 10)
        result = await data_loader.bulk_create(sample_data)

        return {
            "success": True,
            "message": "סביבת מבחן הוכנה בהצלחה",
            "collection": collection_name,
            "sample_data_created": result.success_count,
            "template_used": "generic"
        }

    except Exception as e:
        logger.error(f"שגיאה בהכנת סביבת מבחן: {e}")
        return {"success": False, "message": f"שגיאה: {str(e)}"}


async def cleanup_test_environment(collection_name: str = "test_collection") -> dict:
    """
    ניקוי סביבת מבחן

    Args:
        collection_name: שם הקולקשן לניקוי

    Returns:
        dict: תוצאות הניקוי
    """
    try:
        logger.info(f"מנקה סביבת מבחן עבור קולקשן: {collection_name}")

        # עדכון קולקשן פעיל
        update_collection(collection_name)

        # ספירת רשומות לפני מחיקה
        count_before = await data_loader.count_documents()

        # מחיקת כל הרשומות בקולקשן
        result = await data_loader.bulk_delete([{}])  # פילטר ריק = הכל

        return {
            "success": True,
            "message": "סביבת מבחן נוקתה בהצלחה",
            "collection": collection_name,
            "records_before": count_before,
            "records_deleted": result.deleted_count
        }

    except Exception as e:
        logger.error(f"שגיאה בניקוי סביבת מבחן: {e}")
        return {"success": False, "message": f"שגיאה: {str(e)}"}


def get_quick_start_guide() -> dict:
    """
    מדריך התחלה מהירה למבחן

    Returns:
        dict: המדריך
    """
    return {
        "title": "מדריך התחלה מהירה - מערכת CRUD גנרית",
        "description": "מערכת CRUD מלאה עם MongoDB ו-FastAPI",
        "quick_steps": [
            "1. הפעל את השרת עם: uvicorn main:app --reload",
            "2. גש לתיעוד API ב: http://localhost:8000/docs",
            "3. בדוק חיבור עם: GET /api/v1/health",
            "4. צור נתוני דוגמה עם: POST /api/v1/demo/populate",
            "5. חפש נתונים עם: POST /api/v1/search",
            "6. נקה נתונים עם: DELETE /api/v1/demo/cleanup"
        ],
        "common_endpoints": {
            "create_item": "POST /api/v1/items",
            "get_item": "GET /api/v1/items/{id}",
            "update_item": "PUT /api/v1/items/{id}",
            "delete_item": "DELETE /api/v1/items/{id}",
            "search": "POST /api/v1/search",
            "bulk_create": "POST /api/v1/bulk/create",
            "export": "POST /api/v1/export",
            "statistics": "GET /api/v1/statistics"
        },
        "data_templates": list(DATA_TEMPLATES.keys()),
        "common_collections": COMMON_COLLECTIONS,
        "environment_variables": {
            "MONGO_HOST": "כתובת MongoDB (ברירת מחדל: localhost)",
            "MONGO_PORT": "פורט MongoDB (ברירת מחדל: 27017)",
            "MONGO_DB_NAME": "שם מסד הנתונים (ברירת מחדל: generic_crud_db)",
            "MONGO_COLLECTION_NAME": "שם הקולקשן (ברירת מחדל: items)",
            "LOG_LEVEL": "רמת לוגים (ברירת מחדל: INFO)"
        }
    }


# === הדפסת מידע אתחול ===

def print_startup_info():
    """
    הדפסת מידע אתחול למסך
    """
    print("=" * 60)
    print("🚀 מערכת CRUD גנרית מלאה עם MongoDB")
    print("=" * 60)
    print(f"📊 מסד נתונים: {MONGO_DB_NAME}")
    print(f"📁 קולקשן: {MONGO_COLLECTION_NAME}")
    print(f"🌐 שרת MongoDB: {MONGO_HOST}:{MONGO_PORT}")
    print(f"🔒 אימות: {'מופעל' if MONGO_USER else 'כבוי'}")
    print(f"📋 רמת לוגים: {LOG_LEVEL}")
    print("=" * 60)
    print("📚 תיעוד API זמין ב: http://localhost:8000/docs")
    print("🔍 בדיקת בריאות: http://localhost:8000/api/v1/health")
    print("=" * 60)


# אתחול אוטומטי כשמייבאים את המודול
if __name__ != "__main__":
    print_startup_info()