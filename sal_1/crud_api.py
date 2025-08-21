# crud_api.py - שכבת API גנרית מלאה עם כל הפונקציונליות
import logging
import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query, Path, Body, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import ValidationError
import io
import csv

# ייבוא המודלים והדאל
from .models import (
    GenericCreate, GenericUpdate, GenericItem, SearchQuery, FilterCondition,
    SortCondition, FilterOperator, SortOrder, PaginatedResponse, BulkOperation,
    BulkResult, FieldInfo, SchemaInfo, StatisticsResponse, IndexInfo,
    ExportFormat, ImportResult, HealthCheck, ValidationError as CustomValidationError,
    DetailedErrorResponse
)
from .dal import GenericDataLoader

logger = logging.getLogger(__name__)


class GenericCRUDRouter:
    """
    ראוטר גנרי ל-CRUD מלא עם כל הפונקציונליות האפשרית
    """

    def __init__(self, data_loader: GenericDataLoader, prefix: str = "/api/v1", tags: List[str] = None):
        """
        אתחול הראוטר הגנרי

        Args:
            data_loader: מופע של GenericDataLoader
            prefix: קידומת לכל הנתיבים
            tags: תגים לתיעוד Swagger
        """
        self.data_loader = data_loader
        self.router = APIRouter(
            prefix=prefix,
            tags=tags or ["Generic CRUD API"]
        )
        self._setup_routes()

    def _setup_routes(self):
        """הגדרת כל הנתיבים"""

        # === נתיבים בסיסיים ל-CRUD ===

        @self.router.post("/items",
                          response_model=Dict[str, Any],
                          status_code=status.HTTP_201_CREATED,
                          summary="יצירת פריט חדש",
                          description="יוצר פריט חדש במסד הנתונים עם כל הנתונים שמועברים")
        async def create_item(item: GenericCreate):
            """יצירת פריט חדש"""
            try:
                logger.info(f"יוצר פריט חדש עם נתונים: {len(item.data)} שדות")
                result = await self.data_loader.create_item(item)
                logger.info(f"פריט נוצר בהצלחה עם מזהה: {result.get('_id', 'לא ידוע')}")
                return result

            except ValueError as e:
                logger.warning(f"שגיאת אימות ביצירת פריט: {e}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(e)
                )
            except RuntimeError as e:
                logger.error(f"שגיאת מסד נתונים ביצירת פריט: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"שגיאה לא צפויה ביצירת פריט: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה לא צפויה במערכת"
                )

        @self.router.get("/items/{item_id}",
                         response_model=Dict[str, Any],
                         summary="קבלת פריט לפי מזהה",
                         description="מחזיר פריט ספציפי לפי המזהה שלו")
        async def get_item(item_id: str = Path(..., description="מזהה הפריט")):
            """קבלת פריט לפי מזהה"""
            try:
                logger.info(f"מחפש פריט עם מזהה: {item_id}")
                item = await self.data_loader.get_item_by_id(item_id)

                if item is None:
                    logger.info(f"פריט לא נמצא: {item_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"פריט עם מזהה {item_id} לא נמצא"
                    )

                logger.info(f"פריט נמצא בהצלחה: {item_id}")
                return item

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה בחיפוש פריט {item_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בחיפוש פריט"
                )

        @self.router.put("/items/{item_id}",
                         response_model=Dict[str, Any],
                         summary="עדכון פריט קיים",
                         description="מעדכן פריט קיים במסד הנתונים")
        async def update_item(
                item_id: str = Path(..., description="מזהה הפריט"),
                item_update: GenericUpdate = Body(..., description="נתונים לעדכון")
        ):
            """עדכון פריט קיים"""
            try:
                logger.info(f"מעדכן פריט: {item_id}")
                updated_item = await self.data_loader.update_item(item_id, item_update)

                if updated_item is None:
                    logger.info(f"פריט לא נמצא לעדכון: {item_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"פריט עם מזהה {item_id} לא נמצא לעדכון"
                    )

                logger.info(f"פריט עודכן בהצלחה: {item_id}")
                return updated_item

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה בעדכון פריט {item_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בעדכון פריט"
                )

        @self.router.delete("/items/{item_id}",
                            status_code=status.HTTP_204_NO_CONTENT,
                            summary="מחיקת פריט",
                            description="מוחק פריט מהמסד הנתונים")
        async def delete_item(item_id: str = Path(..., description="מזהה הפריט")):
            """מחיקת פריט"""
            try:
                logger.info(f"מוחק פריט: {item_id}")
                success = await self.data_loader.delete_item(item_id)

                if not success:
                    logger.info(f"פריט לא נמצא למחיקה: {item_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"פריט עם מזהה {item_id} לא נמצא למחיקה"
                    )

                logger.info(f"פריט נמחק בהצלחה: {item_id}")
                return

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה במחיקת פריט {item_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה במחיקת פריט"
                )

        # === חיפוש מתקדם ===

        @self.router.post("/search",
                          response_model=PaginatedResponse,
                          summary="חיפוש מתקדם",
                          description="מבצע חיפוש מתקדם עם פילטרים, מיון ועימוד")
        async def search_items(search_query: SearchQuery):
            """חיפוש מתקדם בפריטים"""
            try:
                logger.info(f"מבצע חיפוש מתקדם: עמוד {search_query.page}, גבול {search_query.limit}")
                result = await self.data_loader.search_items(search_query)
                logger.info(f"חיפוש הושלם: {len(result.data)} תוצאות")
                return result

            except Exception as e:
                logger.error(f"שגיאה בחיפוש מתקדם: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בחיפוש"
                )

        @self.router.get("/items",
                         response_model=List[Dict[str, Any]],
                         summary="קבלת כל הפריטים",
                         description="מחזיר רשימה של כל הפריטים עם אפשרות הגבלה")
        async def get_all_items(
                limit: int = Query(100, ge=1, le=1000, description="מקסימום פריטים להחזיר"),
                skip: int = Query(0, ge=0, description="כמה פריטים לדלג")
        ):
            """קבלת כל הפריטים"""
            try:
                logger.info(f"מביא כל הפריטים: גבול {limit}, דילוג {skip}")
                items = await self.data_loader.get_all_items(limit=limit, skip=skip)
                logger.info(f"הובאו {len(items)} פריטים")
                return items

            except Exception as e:
                logger.error(f"שגיאה בהבאת כל הפריטים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בהבאת פריטים"
                )

        # === פעולות חבצות (Bulk Operations) ===

        @self.router.post("/bulk/create",
                          response_model=BulkResult,
                          summary="יצירה חבצית",
                          description="יוצר מספר פריטים בפעולה אחת")
        async def bulk_create(items: List[Dict[str, Any]] = Body(..., description="רשימת פריטים ליצירה")):
            """יצירה חבצית של פריטים"""
            try:
                logger.info(f"יצירה חבצית של {len(items)} פריטים")

                if len(items) > 1000:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="מקסימום 1000 פריטים בפעולה חבצית"
                    )

                result = await self.data_loader.bulk_create(items)
                logger.info(f"יצירה חבצית הושלמה: {result.success_count} הצלחות")
                return result

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה ביצירה חבצית: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה ביצירה חבצית"
                )

        @self.router.post("/bulk/update",
                          response_model=BulkResult,
                          summary="עדכון חבצי",
                          description="מעדכן מספר פריטים בפעולה אחת")
        async def bulk_update(updates: List[Dict[str, Any]] = Body(..., description="רשימת עדכונים")):
            """עדכון חבצי של פריטים"""
            try:
                logger.info(f"עדכון חבצי של {len(updates)} פריטים")

                if len(updates) > 1000:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="מקסימום 1000 עדכונים בפעולה חבצית"
                    )

                result = await self.data_loader.bulk_update(updates)
                logger.info(f"עדכון חבצי הושלם: {result.modified_count} עודכנו")
                return result

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה בעדכון חבצי: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בעדכון חבצי"
                )

        @self.router.post("/bulk/delete",
                          response_model=BulkResult,
                          summary="מחיקה חבצית",
                          description="מוחק מספר פריטים בפעולה אחת")
        async def bulk_delete(filters: List[Dict[str, Any]] = Body(..., description="רשימת פילטרים למחיקה")):
            """מחיקה חבצית של פריטים"""
            try:
                logger.info(f"מחיקה חבצית עם {len(filters)} פילטרים")

                if len(filters) > 100:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="מקסימום 100 פילטרים למחיקה חבצית"
                    )

                result = await self.data_loader.bulk_delete(filters)
                logger.info(f"מחיקה חבצית הושלמה: {result.deleted_count} נמחקו")
                return result

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה במחיקה חבצית: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה במחיקה חבצית"
                )

        # === סטטיסטיקות ומידע ===

        @self.router.get("/statistics",
                         response_model=StatisticsResponse,
                         summary="סטטיסטיקות קולקשן",
                         description="מחזיר סטטיסטיקות מפורטות על הקולקשן")
        async def get_statistics():
            """קבלת סטטיסטיקות"""
            try:
                logger.info("אוסף סטטיסטיקות")
                stats = await self.data_loader.get_statistics()
                logger.info("סטטיסטיקות נאספו בהצלחה")
                return stats

            except Exception as e:
                logger.error(f"שגיאה בקבלת סטטיסטיקות: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בקבלת סטטיסטיקות"
                )

        @self.router.get("/schema",
                         response_model=SchemaInfo,
                         summary="מידע על הסכמה",
                         description="מחזיר מידע על מבנה הנתונים בקולקשן")
        async def get_schema():
            """קבלת מידע על הסכמה"""
            try:
                logger.info("אוסף מידע על הסכמה")
                schema = await self.data_loader.get_schema_info()
                logger.info("מידע על הסכמה נאסף בהצלחה")
                return schema

            except Exception as e:
                logger.error(f"שגיאה בקבלת מידע על הסכמה: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בקבלת מידע על הסכמה"
                )

        # === ניהול אינדקסים ===

        @self.router.post("/indexes",
                          summary="יצירת אינדקס",
                          description="יוצר אינדקס חדש לשיפור ביצועים")
        async def create_index(index_info: IndexInfo):
            """יצירת אינדקס חדש"""
            try:
                logger.info(f"יוצר אינדקס: {index_info.name}")
                success = await self.data_loader.create_index(index_info)

                if success:
                    return {"message": f"אינדקס {index_info.name} נוצר בהצלחה"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"נכשל ביצירת אינדקס {index_info.name}"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה ביצירת אינדקס: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה ביצירת אינדקס"
                )

        @self.router.delete("/indexes/{index_name}",
                            summary="מחיקת אינדקס",
                            description="מוחק אינדקס קיים")
        async def drop_index(index_name: str = Path(..., description="שם האינדקס למחיקה")):
            """מחיקת אינדקס"""
            try:
                logger.info(f"מוחק אינדקס: {index_name}")
                success = await self.data_loader.drop_index(index_name)

                if success:
                    return {"message": f"אינדקס {index_name} נמחק בהצלחה"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"אינדקס {index_name} לא נמצא"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה במחיקת אינדקס: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה במחיקת אינדקס"
                )

        # === ייצוא וייבוא נתונים ===

        @self.router.post("/export",
                          summary="ייצוא נתונים",
                          description="מייצא נתונים בפורמטים שונים")
        async def export_data(
                format: ExportFormat = Query(ExportFormat.JSON, description="פורמט הייצוא"),
                search_query: Optional[SearchQuery] = Body(None, description="שאילתה לייצוא (אופציונלי)")
        ):
            """ייצוא נתונים"""
            try:
                logger.info(f"מייצא נתונים בפורמט {format}")

                exported_data = await self.data_loader.export_data(search_query, format)

                # קביעת content type ושם קובץ
                if format == ExportFormat.JSON:
                    media_type = "application/json"
                    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                elif format == ExportFormat.CSV:
                    media_type = "text/csv"
                    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                else:
                    media_type = "application/octet-stream"
                    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

                # החזרת הקובץ כ-streaming response
                def generate():
                    yield exported_data.encode('utf-8')

                return StreamingResponse(
                    generate(),
                    media_type=media_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )

            except Exception as e:
                logger.error(f"שגיאה בייצוא נתונים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בייצוא נתונים"
                )

        @self.router.post("/import",
                          response_model=ImportResult,
                          summary="ייבוא נתונים",
                          description="מייבא נתונים מקובץ")
        async def import_data(
                file: UploadFile = File(..., description="קובץ לייבוא"),
                replace_existing: bool = Query(False, description="האם להחליף נתונים קיימים")
        ):
            """ייבוא נתונים מקובץ"""
            try:
                logger.info(f"מייבא נתונים מקובץ: {file.filename}")

                # קריאת תוכן הקובץ
                content = await file.read()

                # פרסור לפי סוג הקובץ
                if file.filename.endswith('.json'):
                    data = json.loads(content.decode('utf-8'))
                    if isinstance(data, dict) and "data" in data:
                        data = data["data"]
                    elif not isinstance(data, list):
                        data = [data]

                elif file.filename.endswith('.csv'):
                    content_str = content.decode('utf-8')
                    csv_reader = csv.DictReader(io.StringIO(content_str))
                    data = list(csv_reader)

                else:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="פורמט קובץ לא נתמך. יש להשתמש ב-JSON או CSV"
                    )

                # ביצוע הייבוא
                result = await self.data_loader.import_data(data, replace_existing)

                logger.info(f"ייבוא הושלם: {result.successful_imports} הצלחות")
                return result

            except HTTPException:
                raise
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="קובץ JSON לא תקין"
                )
            except Exception as e:
                logger.error(f"שגיאה בייבוא נתונים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בייבוא נתונים"
                )

        # === פונקציות עזר ===

        @self.router.get("/distinct/{field}",
                         response_model=List[Any],
                         summary="ערכים ייחודיים",
                         description="מחזיר רשימת ערכים ייחודיים לשדה מסוים")
        async def get_distinct_values(
                field: str = Path(..., description="שם השדה"),
                filter_query: Optional[Dict[str, Any]] = Body(None, description="פילטר אופציונלי")
        ):
            """קבלת ערכים ייחודיים לשדה"""
            try:
                logger.info(f"מביא ערכים ייחודיים עבור שדה: {field}")
                values = await self.data_loader.get_distinct_values(field, filter_query)
                logger.info(f"נמצאו {len(values)} ערכים ייחודיים")
                return values

            except Exception as e:
                logger.error(f"שגיאה בקבלת ערכים ייחודיים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בקבלת ערכים ייחודיים"
                )

        @self.router.post("/count",
                          response_model=int,
                          summary="ספירת מסמכים",
                          description="סופר מסמכים לפי פילטר")
        async def count_documents(filter_query: Optional[Dict[str, Any]] = Body(None, description="פילטר לספירה")):
            """ספירת מסמכים"""
            try:
                logger.info("סופר מסמכים")
                count = await self.data_loader.count_documents(filter_query)
                logger.info(f"נספרו {count} מסמכים")
                return count

            except Exception as e:
                logger.error(f"שגיאה בספירת מסמכים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בספירת מסמכים"
                )

        @self.router.post("/duplicates",
                          response_model=List[Dict[str, Any]],
                          summary="מציאת כפולות",
                          description="מוצא רשומות כפולות בהתבסס על שדות מסוימים")
        async def find_duplicates(fields: List[str] = Body(..., description="שדות לבדיקת כפולות")):
            """מציאת רשומות כפולות"""
            try:
                logger.info(f"מחפש כפולות בשדות: {fields}")
                duplicates = await self.data_loader.find_duplicates(fields)
                logger.info(f"נמצאו {len(duplicates)} קבוצות כפולות")
                return duplicates

            except Exception as e:
                logger.error(f"שגיאה במציאת כפולות: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה במציאת כפולות"
                )

        # === פונקציות aggregation מתקדמות ===

        @self.router.post("/aggregate",
                          response_model=List[Dict[str, Any]],
                          summary="Aggregation מותאם אישית",
                          description="מבצע aggregation מותאם אישית על הנתונים")
        async def aggregate_data(pipeline: List[Dict[str, Any]] = Body(..., description="Pipeline של MongoDB")):
            """ביצוע aggregation מותאם אישית"""
            try:
                logger.info(f"מבצע aggregation עם {len(pipeline)} שלבים")

                # הגבלת גודל pipeline למניעת עומס
                if len(pipeline) > 20:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="מקסימום 20 שלבים ב-pipeline"
                    )

                results = await self.data_loader.aggregate(pipeline)
                logger.info(f"aggregation הושלם: {len(results)} תוצאות")
                return results

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה ב-aggregation: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה ב-aggregation"
                )

        # === ניהול קולקשנים ===

        @self.router.get("/collections",
                         response_model=List[str],
                         summary="רשימת קולקשנים",
                         description="מחזיר רשימת כל הקולקשנים במסד")
        async def list_collections():
            """קבלת רשימת קולקשנים"""
            try:
                logger.info("מביא רשימת קולקשנים")
                collections = await self.data_loader.list_collections()
                logger.info(f"נמצאו {len(collections)} קולקשנים")
                return collections

            except Exception as e:
                logger.error(f"שגיאה בקבלת רשימת קולקשנים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בקבלת רשימת קולקשנים"
                )

        @self.router.post("/collections/{collection_name}",
                          summary="יצירת קולקשן",
                          description="יוצר קולקשן חדש")
        async def create_collection(
                collection_name: str = Path(..., description="שם הקולקשן החדש"),
                options: Optional[Dict[str, Any]] = Body(None, description="אפשרויות הקולקשן")
        ):
            """יצירת קולקשן חדש"""
            try:
                logger.info(f"יוצר קולקשן חדש: {collection_name}")
                success = await self.data_loader.create_collection(collection_name, **(options or {}))

                if success:
                    return {"message": f"קולקשן {collection_name} נוצר בהצלחה"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"נכשל ביצירת קולקשן {collection_name}"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה ביצירת קולקשן: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה ביצירת קולקשן"
                )

        @self.router.delete("/collections/{collection_name}",
                            summary="מחיקת קולקשן",
                            description="מוחק קולקשן (זהירות!)")
        async def drop_collection(collection_name: str = Path(..., description="שם הקולקשן למחיקה")):
            """מחיקת קולקשן"""
            try:
                logger.warning(f"בקשה למחיקת קולקשן: {collection_name}")
                success = await self.data_loader.drop_collection(collection_name)

                if success:
                    return {"message": f"קולקשן {collection_name} נמחק בהצלחה"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"קולקשן {collection_name} לא נמצא"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה במחיקת קולקשן: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה במחיקת קולקשן"
                )

        @self.router.put("/collections/switch/{collection_name}",
                         summary="החלפת קולקשן פעיל",
                         description="עובר לעבוד עם קולקשן אחר")
        async def switch_collection(collection_name: str = Path(..., description="שם הקולקשן החדש")):
            """החלפת הקולקשן הפעיל"""
            try:
                logger.info(f"עובר לקולקשן: {collection_name}")
                self.data_loader.set_collection(collection_name)
                return {"message": f"עבר לקולקשן {collection_name} בהצלחה"}

            except Exception as e:
                logger.error(f"שגיאה בהחלפת קולקשן: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בהחלפת קולקשן"
                )

        # === תחזוקה ואופטימיזציה ===

        @self.router.post("/maintenance/cleanup",
                          summary="ניקוי רשומות ישנות",
                          description="מנקה רשומות ישנות מהמסד")
        async def cleanup_old_records(
                days_old: int = Query(30, ge=1, description="כמה ימים ישנות למחיקה"),
                date_field: str = Query("created_at", description="שדה התאריך לבדיקה")
        ):
            """ניקוי רשומות ישנות"""
            try:
                logger.info(f"מנקה רשומות ישנות מ-{days_old} ימים")
                deleted_count = await self.data_loader.cleanup_old_records(days_old, date_field)
                return {"message": f"נמחקו {deleted_count} רשומות ישנות"}

            except Exception as e:
                logger.error(f"שגיאה בניקוי רשומות ישנות: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בניקוי רשומות ישנות"
                )

        @self.router.post("/maintenance/optimize",
                          summary="אופטימיזציה של הקולקשן",
                          description="מבצע אופטימיזציה מלאה של הקולקשן")
        async def optimize_collection(background_tasks: BackgroundTasks):
            """אופטימיזציה של הקולקשן"""
            try:
                logger.info("מתחיל אופטימיזציה של הקולקשן")

                # הרצה ברקע
                async def run_optimization():
                    try:
                        result = await self.data_loader.optimize_collection()
                        logger.info(f"אופטימיזציה הושלמה: {result}")
                    except Exception as e:
                        logger.error(f"שגיאה באופטימיזציה: {e}")

                background_tasks.add_task(run_optimization)
                return {"message": "אופטימיזציה החלה ברקע"}

            except Exception as e:
                logger.error(f"שגיאה בהפעלת אופטימיזציה: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בהפעלת אופטימיזציה"
                )

        @self.router.post("/maintenance/validate",
                          summary="אימות תקינות נתונים",
                          description="מאמת את תקינות הנתונים במסד")
        async def validate_data():
            """אימות תקינות הנתונים"""
            try:
                logger.info("מאמת תקינות נתונים")
                result = await self.data_loader.validate_data_integrity()
                return result

            except Exception as e:
                logger.error(f"שגיאה באימות נתונים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה באימות נתונים"
                )

        # === גיבוי ושחזור ===

        @self.router.post("/backup",
                          summary="יצירת גיבוי",
                          description="יוצר גיבוי של הקולקשן")
        async def create_backup(
                background_tasks: BackgroundTasks,
                backup_name: Optional[str] = Query(None, description="שם הגיבוי (אופציונלי)")
        ):
            """יצירת גיבוי"""
            try:
                if not backup_name:
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                backup_path = f"/tmp/{backup_name}"

                async def run_backup():
                    try:
                        success = await self.data_loader.backup_collection(backup_path)
                        if success:
                            logger.info(f"גיבוי הושלם: {backup_path}")
                        else:
                            logger.error("גיבוי נכשל")
                    except Exception as e:
                        logger.error(f"שגיאה בגיבוי: {e}")

                background_tasks.add_task(run_backup)
                return {"message": f"גיבוי החל ברקע: {backup_name}"}

            except Exception as e:
                logger.error(f"שגיאה בהפעלת גיבוי: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בהפעלת גיבוי"
                )

        # === בדיקת בריאות המערכת ===

        @self.router.get("/health",
                         response_model=HealthCheck,
                         summary="בדיקת בריאות המערכת",
                         description="בודק את מצב הבריאות של המערכת והמסד")
        async def health_check():
            """בדיקת בריאות המערכת"""
            try:
                health = await self.data_loader.health_check()

                # קביעת status code לפי מצב הבריאות
                if health.status == "unhealthy":
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=health.dict()
                    )
                elif health.status == "degraded":
                    # מחזיר 200 אבל עם אזהרה
                    logger.warning("מערכת במצב מוגדר (degraded)")

                return health

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"שגיאה בבדיקת בריאות: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בבדיקת בריאות המערכת"
                )

        @self.router.get("/info",
                         response_model=Dict[str, Any],
                         summary="מידע מפורט על הקולקשן",
                         description="מחזיר מידע מפורט ומקיף על הקולקשן הנוכחי")
        async def get_collection_info():
            """מידע מפורט על הקולקשן"""
            try:
                logger.info("אוסף מידע מפורט על הקולקשן")
                info = await self.data_loader.get_collection_info()
                return info

            except Exception as e:
                logger.error(f"שגיאה בקבלת מידע על הקולקשן: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בקבלת מידע על הקולקשן"
                )

        # === פונקציות חיפוש מתקדמות נוספות ===

        @self.router.get("/search/quick",
                         response_model=List[Dict[str, Any]],
                         summary="חיפוש מהיר",
                         description="חיפוש מהיר וקל לשימוש")
        async def quick_search(
                q: str = Query(..., description="מונח החיפוש"),
                limit: int = Query(10, ge=1, le=100, description="מקסימום תוצאות")
        ):
            """חיפוש מהיר בטקסט"""
            try:
                logger.info(f"חיפוש מהיר: {q}")

                search_query = SearchQuery(
                    text=q,
                    limit=limit,
                    include_count=False
                )

                result = await self.data_loader.search_items(search_query)
                return result.data

            except Exception as e:
                logger.error(f"שגיאה בחיפוש מהיר: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בחיפוש מהיר"
                )

        @self.router.get("/search/field/{field}/{value}",
                         response_model=List[Dict[str, Any]],
                         summary="חיפוש לפי שדה",
                         description="חיפוש פריטים לפי ערך בשדה ספציפי")
        async def search_by_field(
                field: str = Path(..., description="שם השדה"),
                value: str = Path(..., description="הערך לחיפוש"),
                limit: int = Query(50, ge=1, le=200, description="מקסימום תוצאות")
        ):
            """חיפוש לפי שדה ספציפי"""
            try:
                logger.info(f"חיפוש בשדה {field} עם ערך {value}")

                # יצירת שאילתה עם פילטר ספציפי
                filter_condition = FilterCondition(
                    field=field,
                    operator=FilterOperator.CONTAINS,
                    value=value,
                    case_sensitive=False
                )

                search_query = SearchQuery(
                    filters=[filter_condition],
                    limit=limit,
                    include_count=False
                )

                result = await self.data_loader.search_items(search_query)
                return result.data

            except Exception as e:
                logger.error(f"שגיאה בחיפוש לפי שדה: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בחיפוש לפי שדה"
                )

        # === פונקציות תאריכים ===

        @self.router.get("/search/date-range",
                         response_model=PaginatedResponse,
                         summary="חיפוש לפי טווח תאריכים",
                         description="מחזיר פריטים בטווח תאריכים מסוים")
        async def search_by_date_range(
                start_date: datetime = Query(..., description="תאריך התחלה"),
                end_date: datetime = Query(..., description="תאריך סיום"),
                date_field: str = Query("created_at", description="שדה התאריך"),
                page: int = Query(1, ge=1, description="מספר עמוד"),
                limit: int = Query(50, ge=1, le=200, description="פריטים בעמוד")
        ):
            """חיפוש לפי טווח תאריכים"""
            try:
                logger.info(f"חיפוש בטווח תאריכים: {start_date} עד {end_date}")

                # יצירת פילטרים לטווח תאריכים
                filters = [
                    FilterCondition(
                        field=date_field,
                        operator=FilterOperator.GREATER_EQUAL,
                        value=start_date.isoformat()
                    ),
                    FilterCondition(
                        field=date_field,
                        operator=FilterOperator.LESS_EQUAL,
                        value=end_date.isoformat()
                    )
                ]

                search_query = SearchQuery(
                    filters=filters,
                    page=page,
                    limit=limit
                )

                result = await self.data_loader.search_items(search_query)
                return result

            except Exception as e:
                logger.error(f"שגיאה בחיפוש לפי טווח תאריכים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בחיפוש לפי טווח תאריכים"
                )

        # === פונקציות מיון מתקדמות ===

        @self.router.get("/items/sorted",
                         response_model=List[Dict[str, Any]],
                         summary="פריטים ממוינים",
                         description="מחזיר פריטים ממוינים לפי שדה מסוים")
        async def get_sorted_items(
                sort_field: str = Query(..., description="שדה למיון"),
                sort_order: SortOrder = Query(SortOrder.ASC, description="כיוון המיון"),
                limit: int = Query(50, ge=1, le=200, description="מקסימום פריטים")
        ):
            """קבלת פריטים ממוינים"""
            try:
                logger.info(f"מביא פריטים ממוינים לפי {sort_field} {sort_order}")

                sort_condition = SortCondition(
                    field=sort_field,
                    order=sort_order
                )

                search_query = SearchQuery(
                    sort=[sort_condition],
                    limit=limit,
                    include_count=False
                )

                result = await self.data_loader.search_items(search_query)
                return result.data

            except Exception as e:
                logger.error(f"שגיאה בקבלת פריטים ממוינים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בקבלת פריטים ממוינים"
                )

        # === פונקציות לדוגמאות ובדיקות ===

        @self.router.get("/sample",
                         response_model=List[Dict[str, Any]],
                         summary="דוגמת פריטים",
                         description="מחזיר דוגמה אקראית של פריטים")
        async def get_sample_items(
                count: int = Query(5, ge=1, le=20, description="כמות פריטים בדוגמה")
        ):
            """קבלת דוגמת פריטים"""
            try:
                logger.info(f"מביא דוגמה של {count} פריטים")

                # שימוש ב-aggregation לדגימה אקראית
                pipeline = [
                    {"$sample": {"size": count}},
                    {"$project": {"_id": {"$toString": "$_id"}, "data": "$ROOT"}}
                ]

                results = await self.data_loader.aggregate(pipeline)

                # עיבוד התוצאות
                sample_items = []
                for result in results:
                    if "data" in result:
                        item = result["data"]
                        if "_id" in item:
                            item["_id"] = str(item["_id"])
                        sample_items.append(item)

                return sample_items

            except Exception as e:
                logger.error(f"שגיאה בקבלת דוגמת פריטים: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בקבלת דוגמת פריטים"
                )

        @self.router.get("/test/connectivity",
                         summary="בדיקת קישוריות",
                         description="בודק את הקישוריות למסד הנתונים")
        async def test_connectivity():
            """בדיקת קישוריות למסד"""
            try:
                # ניסיון לביצוע פעולה פשוטה
                count = await self.data_loader.count_documents()

                return {
                    "status": "connected",
                    "message": "חיבור למסד תקין",
                    "document_count": count,
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"בדיקת קישוריות נכשלה: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"אין קישוריות למסד הנתונים: {str(e)}"
                )

        # === תיעוד API ===

        @self.router.get("/docs/endpoints",
                         summary="תיעוד נקודות קצה",
                         description="מחזיר רשימה של כל נקודות הקצה הזמינות")
        async def get_api_documentation():
            """תיעוד API"""
            endpoints = []

            for route in self.router.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    for method in route.methods:
                        if method != 'HEAD':  # מדלגים על HEAD
                            endpoint_info = {
                                "method": method,
                                "path": route.path,
                                "name": getattr(route, 'name', 'Unknown'),
                                "summary": getattr(route, 'summary', ''),
                                "description": getattr(route, 'description', '')
                            }
                            endpoints.append(endpoint_info)

            return {
                "api_version": "1.0",
                "total_endpoints": len(endpoints),
                "endpoints": sorted(endpoints, key=lambda x: (x['path'], x['method']))
            }

        # === פונקציות להדגמה במבחן ===

        @self.router.post("/demo/populate",
                          summary="הדגמה - מילוי נתונים",
                          description="מילוי המסד בנתוני הדגמה (למבחן)")
        async def populate_demo_data():
            """מילוי נתוני הדגמה"""
            try:
                demo_data = [
                    {
                        "name": "דוגמה 1",
                        "type": "בדיקה",
                        "value": 100,
                        "active": True,
                        "tags": ["demo", "test"],
                        "metadata": {"created_by": "system", "version": 1}
                    },
                    {
                        "name": "דוגמה 2",
                        "type": "הדגמה",
                        "value": 200,
                        "active": False,
                        "tags": ["demo", "example"],
                        "metadata": {"created_by": "system", "version": 1}
                    },
                    {
                        "name": "דוגמה 3",
                        "type": "מבחן",
                        "value": 150,
                        "active": True,
                        "tags": ["test", "sample"],
                        "metadata": {"created_by": "system", "version": 2}
                    }
                ]

                result = await self.data_loader.bulk_create(demo_data)

                return {
                    "message": "נתוני הדגמה נוצרו בהצלחה",
                    "created_count": result.success_count,
                    "failed_count": result.error_count
                }

            except Exception as e:
                logger.error(f"שגיאה במילוי נתוני הדגמה: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה במילוי נתוני הדגמה"
                )

        @self.router.delete("/demo/cleanup",
                            summary="הדגמה - ניקוי נתונים",
                            description="ניקוי כל נתוני הדגמה")
        async def cleanup_demo_data():
            """ניקוי נתוני הדגמה"""
            try:
                # מחיקת כל הנתונים שיש להם metadata.created_by = "system"
                filter_dict = {"metadata.created_by": "system"}
                result = await self.data_loader.bulk_delete([filter_dict])

                return {
                    "message": "נתוני הדגמה נוקו בהצלחה",
                    "deleted_count": result.deleted_count
                }

            except Exception as e:
                logger.error(f"שגיאה בניקוי נתוני הדגמה: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="שגיאה בניקוי נתוני הדגמה"
                )

    def get_router(self) -> APIRouter:
        """קבלת הראוטר"""
        return self.router