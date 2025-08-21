# main.py - קובץ ראשי למערכת CRUD גנרית מלאה
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# ייבוא המודלים והרכיבים שלנו
from .dependencies import (
    data_loader, initialize_system, shutdown_system, get_database_config,
    get_security_config, validate_configuration, get_environment_info,
    get_quick_start_guide, CORS_ORIGINS, ENABLE_AUTH, API_KEY, LOG_LEVEL
)
from .crud_api import GenericCRUDRouter
from .models import HealthCheck, DetailedErrorResponse

# הגדרת logger
logger = logging.getLogger(__name__)


# === מחלקת מידע על האפליקציה ===

class AppInfo:
    """מידע על האפליקציה"""

    NAME = "מערכת CRUD גנרית מלאה"
    DESCRIPTION = """
    מערכת CRUD מלאה וגנרית עם MongoDB ו-FastAPI

    🚀 **תכונות עיקריות:**
    - CRUD מלא (יצירה, קריאה, עדכון, מחיקה)
    - חיפוש מתקדם עם פילטרים ומיון
    - פעולות חבצות (Bulk Operations)
    - ייצוא וייבוא נתונים (JSON, CSV)
    - ניהול אינדקסים ואופטימיזציה
    - סטטיסטיקות מפורטות
    - גיבוי ושחזור
    - תמיכה בכל מבנה נתונים

    📝 **מיועד למבחנים:** מערכת גנרית שמתאימה לכל מבנה נתונים שיכול להופיע במבחן

    🔧 **טכנולוגיות:** Python, FastAPI, MongoDB, Motor (async)
    """
    VERSION = "1.0.0"
    AUTHOR = "מערכת AI לעזרה במבחנים"
    LICENSE = "MIT"
    CONTACT = {
        "name": "תמיכה טכנית",
        "email": "support@example.com"
    }


# === ניהול מחזור חיי האפליקציה ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ניהול מחזור חיי האפליקציה - אתחול וכיבוי
    """
    # === אתחול האפליקציה ===
    logger.info("🚀 מתחיל אתחול מערכת CRUD גנרית...")

    try:
        # אתחול מערכת מלא
        init_result = await initialize_system()

        if not init_result["success"]:
            logger.error(f"❌ אתחול נכשל: {init_result['message']}")
            # לא נכשל את האפליקציה - נמשיך לפעול במצב מוגבל
        else:
            logger.info("✅ אתחול מערכת הושלם בהצלחה")

        # הדפסת סיכום אתחול
        logger.info("=" * 50)
        logger.info("📊 סיכום אתחול מערכת:")
        logger.info(f"   📅 זמן אתחול: {datetime.now().isoformat()}")
        logger.info(f"   🗄️  מסד נתונים: {data_loader.db_name}")
        logger.info(f"   📁 קולקשן: {data_loader.collection_name}")
        logger.info(f"   🌐 חיבור: {'✅ פעיל' if init_result.get('database_connected', False) else '❌ לא פעיל'}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ שגיאה חמורה באתחול: {e}")
        # המשך לפעול למרות השגיאה

    yield  # 🔄 כאן האפליקציה פועלת ומקבלת בקשות

    # === כיבוי האפליקציה ===
    logger.info("🛑 מתחיל כיבוי מערכת...")

    try:
        await shutdown_system()
        logger.info("✅ כיבוי מערכת הושלם בהצלחה")

    except Exception as e:
        logger.error(f"❌ שגיאה בכיבוי מערכת: {e}")


# === יצירת אפליקציית FastAPI ===

app = FastAPI(
    # מידע בסיסי על האפליקציה
    title=AppInfo.NAME,
    description=AppInfo.DESCRIPTION,
    version=AppInfo.VERSION,
    contact=AppInfo.CONTACT,
    license_info={"name": AppInfo.LICENSE},

    # ניהול מחזור חיים
    lifespan=lifespan,

    # הגדרות תיעוד
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",

    # הגדרות נוספות
    terms_of_service="https://example.com/terms",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "displayOperationId": True,
        "filter": True
    }
)

# === הוספת Middleware ===

# CORS - תמיכה בקריאות מדומיינים שונים
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TrustedHost - אבטחה נוספת
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # בפרודקשן יש לציין דומיינים ספציפיים
)


# === Middleware מותאם אישית ===

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    רישום בקשות HTTP
    """
    start_time = datetime.now()

    # רישום בקשה נכנסת
    logger.debug(f"📨 בקשה נכנסת: {request.method} {request.url}")

    try:
        # ביצוע הבקשה
        response = await call_next(request)

        # חישוב זמן ביצוע
        process_time = (datetime.now() - start_time).total_seconds()

        # רישום תגובה
        logger.debug(f"📤 תגובה: {response.status_code} - {process_time:.3f}s")

        # הוספת header עם זמן ביצוע
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ שגיאה בביצוע בקשה: {e} - {process_time:.3f}s")
        raise


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Middleware לאימות (אם מופעל)
    """
    # בדיקה אם אימות מופעל
    if not ENABLE_AUTH:
        return await call_next(request)

    # נתיבים שפטורים מאימות
    exempt_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json"]

    if request.url.path in exempt_paths:
        return await call_next(request)

    # בדיקת API Key
    api_key = request.headers.get("X-API-Key")

    if not api_key or api_key != API_KEY:
        logger.warning(f"🔒 ניסיון גישה לא מורשה: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "API Key חסר או לא תקין"}
        )

    return await call_next(request)


# === יצירת ראוטר CRUD ===

# יצירת הראוטר הגנרי
crud_router = GenericCRUDRouter(
    data_loader=data_loader,
    prefix="/api/v1",
    tags=["Generic CRUD API"]
)

# הוספת הראוטר לאפליקציה
app.include_router(crud_router.get_router())


# === נקודות קצה ברמת האפליקציה ===

@app.get("/",
         summary="עמוד הבית",
         description="מחזיר מידע כללי על המערכת",
         tags=["System"])
async def root():
    """עמוד הבית של המערכת"""
    return {
        "message": "🚀 מערכת CRUD גנרית מלאה פועלת בהצלחה!",
        "app_name": AppInfo.NAME,
        "version": AppInfo.VERSION,
        "description": "מערכת CRUD מלאה עם MongoDB ו-FastAPI",
        "features": [
            "CRUD מלא",
            "חיפוש מתקדם",
            "פעולות חבצות",
            "ייצוא וייבוא",
            "סטטיסטיקות",
            "גיבוי ושחזור"
        ],
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "api_base_url": "/api/v1",
        "timestamp": datetime.now().isoformat(),
        "status": "operational"
    }


@app.get("/health",
         response_model=HealthCheck,
         summary="בדיקת בריאות מערכת",
         description="בדיקה מפורטת של מצב המערכת והמסד",
         tags=["System"])
async def system_health():
    """בדיקת בריאות מערכת ברמה גבוהה"""
    try:
        # בדיקת בריאות DAL
        dal_health = await data_loader.health_check()

        # בדיקות נוספות ברמת האפליקציה
        app_health = {
            "api_responsive": True,
            "middleware_active": True,
            "routers_loaded": len(app.routes) > 0
        }

        # קביעת סטטוס כללי
        overall_status = "healthy"
        if dal_health.status == "unhealthy":
            overall_status = "unhealthy"
        elif dal_health.status == "degraded" or not all(app_health.values()):
            overall_status = "degraded"

        # החזרת סטטוס מפורט
        health_response = HealthCheck(
            status=overall_status,
            database_connected=dal_health.database_connected,
            collections_accessible=dal_health.collections_accessible,
            response_time_ms=dal_health.response_time_ms,
            last_check=dal_health.last_check
        )

        # אם המערכת לא בריאה, החזר 503
        if overall_status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_response.dict()
            )

        return health_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"שגיאה בבדיקת בריאות מערכת: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בבדיקת בריאות המערכת"
        )


@app.get("/system/info",
         summary="מידע מערכת מפורט",
         description="מחזיר מידע מפורט על המערכת והתצורה",
         tags=["System"])
async def system_info():
    """מידע מפורט על המערכת"""
    try:
        return {
            "application": {
                "name": AppInfo.NAME,
                "version": AppInfo.VERSION,
                "author": AppInfo.AUTHOR,
                "license": AppInfo.LICENSE
            },
            "database": get_database_config(),
            "security": get_security_config(),
            "environment": get_environment_info(),
            "configuration_validation": validate_configuration(),
            "api_info": {
                "total_routes": len(app.routes),
                "crud_endpoints": len([r for r in app.routes if "/api/v1/" in str(r.path)]),
                "system_endpoints": len([r for r in app.routes if "/api/v1/" not in str(r.path)])
            },
            "runtime": {
                "uptime_check": datetime.now().isoformat(),
                "log_level": LOG_LEVEL,
                "auth_enabled": ENABLE_AUTH
            }
        }

    except Exception as e:
        logger.error(f"שגיאה בקבלת מידע מערכת: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בקבלת מידע מערכת"
        )


@app.get("/quick-start",
         summary="מדריך התחלה מהירה",
         description="מדריך התחלה מהירה לשימוש במערכת",
         tags=["Documentation"])
async def quick_start():
    """מדריך התחלה מהירה"""
    return get_quick_start_guide()


@app.get("/system/routes",
         summary="רשימת נתיבים",
         description="מחזיר רשימה של כל הנתיבים הזמינים במערכת",
         tags=["Documentation"])
async def list_routes():
    """רשימת כל הנתיבים במערכת"""
    routes = []

    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method != 'HEAD':  # מדלגים על HEAD
                    route_info = {
                        "method": method,
                        "path": route.path,
                        "name": getattr(route, 'name', 'Unknown'),
                        "summary": getattr(route, 'summary', ''),
                        "tags": getattr(route, 'tags', [])
                    }
                    routes.append(route_info)

    # מיון לפי path ואז method
    routes.sort(key=lambda x: (x['path'], x['method']))

    return {
        "total_routes": len(routes),
        "routes_by_category": {
            "system": [r for r in routes if not r['path'].startswith('/api/v1/')],
            "crud_api": [r for r in routes if r['path'].startswith('/api/v1/')]
        },
        "all_routes": routes
    }


# === טיפול בשגיאות גלובלי ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    טיפול בשגיאות HTTP
    """
    logger.warning(f"🚨 HTTP Exception: {exc.status_code} - {exc.detail} - {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    טיפול בשגיאות כלליות
    """
    logger.error(f"💥 Unhandled Exception: {type(exc).__name__}: {str(exc)} - {request.url}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "שגיאה פנימית במערכת",
            "error_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    טיפול בשגיאות אימות Pydantic
    """
    logger.warning(f"📝 Validation Error: {exc} - {request.url}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "status_code": 422,
            "message": "שגיאת אימות נתונים",
            "details": exc.errors(),
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        }
    )


# === נקודות קצה לניהול תצורה ===

@app.post("/system/config/validate",
          summary="אימות תצורה",
          description="מאמת את תקינות התצורה הנוכחית",
          tags=["System Management"])
async def validate_config():
    """אימות תצורה"""
    try:
        validation_result = validate_configuration()

        if not validation_result["valid"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "valid": False,
                    "message": "תצורה לא תקינה",
                    **validation_result
                }
            )

        return {
            "valid": True,
            "message": "תצורה תקינה",
            **validation_result
        }

    except Exception as e:
        logger.error(f"שגיאה באימות תצורה: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה באימות תצורה"
        )


@app.get("/system/collections",
         summary="רשימת קולקשנים",
         description="מחזיר רשימת כל הקולקשנים במסד הנתונים",
         tags=["System Management"])
async def list_all_collections():
    """רשימת כל הקולקשנים"""
    try:
        collections = await data_loader.list_collections()

        return {
            "total_collections": len(collections),
            "current_collection": data_loader.collection_name,
            "database": data_loader.db_name,
            "collections": collections,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"שגיאה בקבלת רשימת קולקשנים: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בקבלת רשימת קולקשנים"
        )


# === נקודות קצה לניטור וביצועים ===

@app.get("/system/metrics",
         summary="מדדי ביצועים",
         description="מחזיר מדדי ביצועים של המערכת",
         tags=["Monitoring"])
async def system_metrics():
    """מדדי ביצועים של המערכת"""
    try:
        import psutil
        import sys
        from datetime import datetime

        # מידע על המערכת
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # מידע על התהליך הנוכחי
        process = psutil.Process()

        return {
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                    "available_gb": round(memory.available / (1024 ** 3), 2),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024 ** 3), 2),
                    "free_gb": round(disk.free / (1024 ** 3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 1)
                }
            },
            "process": {
                "memory_mb": round(process.memory_info().rss / (1024 ** 2), 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable
            },
            "database": await data_loader.get_statistics() if data_loader.collection else None,
            "timestamp": datetime.now().isoformat()
        }

    except ImportError:
        # אם psutil לא מותקן
        return {
            "message": "מדדי מערכת לא זמינים - psutil לא מותקן",
            "basic_info": {
                "python_version": sys.version,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"שגיאה בקבלת מדדי ביצועים: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בקבלת מדדי ביצועים"
        )


# === נקודות קצה לבדיקות ומבחן ===

@app.get("/test/ping",
         summary="בדיקת ping פשוטה",
         description="בדיקה פשוטה שהשרת מגיב",
         tags=["Testing"])
async def ping():
    """בדיקת ping פשוטה"""
    return {
        "message": "pong",
        "timestamp": datetime.now().isoformat(),
        "status": "ok"
    }


@app.get("/test/echo/{message}",
         summary="Echo test",
         description="מחזיר את ההודעה שנשלחה",
         tags=["Testing"])
async def echo(message: str):
    """החזרת הודעה (Echo)"""
    return {
        "original_message": message,
        "echo": f"Echo: {message}",
        "length": len(message),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/test/validate-json",
          summary="אימות JSON",
          description="מאמת שהנתונים שנשלחו הם JSON תקין",
          tags=["Testing"])
async def validate_json(data: Dict[Any, Any]):
    """אימות JSON"""
    return {
        "valid": True,
        "message": "JSON תקין",
        "keys_count": len(data),
        "data_type": type(data).__name__,
        "keys": list(data.keys()) if isinstance(data, dict) else None,
        "timestamp": datetime.now().isoformat()
    }


# === הרצת השרת ===

def run_server(
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = True,
        log_level: str = "info"
):
    """
    הרצת השרת

    Args:
        host: כתובת ההוסט
        port: פורט
        reload: האם לטעון מחדש אוטומטית
        log_level: רמת לוגים
    """
    logger.info(f"🚀 מפעיל שרת על {host}:{port}")
    logger.info(f"📚 תיעוד זמין ב: http://{host}:{port}/docs")
    logger.info(f"🔍 בדיקת בריאות: http://{host}:{port}/health")

    uvicorn.run(
        "main:app",  # צריך להיות מותאם לנתיב הקובץ
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
        access_log=True
    )


# === הגדרות פיתוח ===

if __name__ == "__main__":
    import argparse

    # פרסור פרמטרים מהטרמינל
    parser = argparse.ArgumentParser(description="מערכת CRUD גנרית מלאה")
    parser.add_argument("--host", default="0.0.0.0", help="כתובת ההוסט")
    parser.add_argument("--port", type=int, default=8000, help="פורט השרת")
    parser.add_argument("--reload", action="store_true", help="טעינה מחדש אוטומטית")
    parser.add_argument("--log-level", default="info", help="רמת לוגים")

    args = parser.parse_args()

    # הרצת השרת עם הפרמטרים
    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

# === הערות לשימוש במבחן ===

"""
🎯 הוראות שימוש במבחן:

1. התקנת חבילות:
   pip install fastapi uvicorn motor pymongo python-multipart

2. הרצת השרת:
   python main.py --reload

3. גישה לתיעוד:
   http://localhost:8000/docs

4. בדיקות בסיסיות:
   - GET /health - בדיקת בריאות
   - GET /quick-start - מדריך מהיר
   - POST /api/v1/demo/populate - מילוי נתוני דוגמה

5. שימוש עם קולקשנים שונים:
   - PUT /api/v1/collections/switch/{collection_name}

6. פעולות CRUD בסיסיות:
   - POST /api/v1/items - יצירה
   - GET /api/v1/items/{id} - קריאה
   - PUT /api/v1/items/{id} - עדכון  
   - DELETE /api/v1/items/{id} - מחיקה

7. חיפוש מתקדם:
   - POST /api/v1/search - חיפוש עם פילטרים ומיון

8. פעולות חבצות:
   - POST /api/v1/bulk/create - יצירה חבצית
   - POST /api/v1/bulk/update - עדכון חבצי
   - POST /api/v1/bulk/delete - מחיקה חבצית

9. ייצוא וייבוא:
   - POST /api/v1/export - ייצוא נתונים
   - POST /api/v1/import - ייבוא נתונים

10. סטטיסטיקות:
    - GET /api/v1/statistics - סטטיסטיקות קולקשן
    - GET /api/v1/schema - מידע על מבנה הנתונים

💡 טיפים למבחן:
- המערכת גנרית לחלוטין - עובדת עם כל מבנה נתונים
- כל הנתונים נשמרים ב-field בשם "data" 
- תמיכה מלאה בחיפוש, מיון ופילטרים
- ניתן לעבוד עם מספר קולקשנים במקביל
- תיעוד מלא זמין ב-Swagger UI

🔧 הגדרות סביבה:
- MONGO_HOST=localhost
- MONGO_PORT=27017  
- MONGO_DB_NAME=test_db
- MONGO_COLLECTION_NAME=test_collection
- LOG_LEVEL=INFO
"""