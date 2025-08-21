# dal.py - שכבת הגישה לנתונים הגנרית המלאה
import logging
import json
import csv
import re
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone
from pymongo import AsyncMongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError, BulkWriteError
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from .models import (
    GenericCreate, GenericUpdate, GenericItem, SearchQuery, FilterCondition,
    SortCondition, FilterOperator, SortOrder, PaginatedResponse, BulkOperation,
    BulkResult, FieldInfo, SchemaInfo, StatisticsResponse, IndexInfo,
    ChangeLog, ExportFormat, ImportResult, QueryPerformance, HealthCheck
)

logger = logging.getLogger(__name__)


class GenericDataLoader:
    """
    טעינת נתונים גנרית המאפשרת CRUD מלא עם חיפוש מתקדם למונגו DB
    תומכת בכל מבנה נתונים ללא הגבלה
    """

    def __init__(self, mongo_uri: str, db_name: str, collection_name: str = "default_collection"):
        """
        אתחול המחלקה

        Args:
            mongo_uri: כתובת החיבור למונגו
            db_name: שם מסד הנתונים
            collection_name: שם הקולקשן (ברירת מחדל: "default_collection")
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name

        # חיבורים - יהיו None עד להתחברות מוצלחת
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

        # מטמון לביצועים
        self._schema_cache: Dict[str, Any] = {}
        self._query_cache: Dict[str, Any] = {}

        # הגדרות
        self.max_bulk_size = 1000  # מקסימום פריטים בפעולה חבצית
        self.cache_ttl = 300  # זמן שמירה במטמון (שניות)

    async def connect(self) -> bool:
        """
        יצירת חיבור למונגו DB

        Returns:
            bool: האם החיבור הצליח
        """
        try:
            logger.info(f"מתחבר למסד נתונים: {self.db_name}")

            # יצירת חיבור אסינכרוני עם הגדרות אופטימליות
            self.client = AsyncIOMotorClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 שניות timeout
                connectTimeoutMS=5000,  # 5 שניות timeout לחיבור
                maxPoolSize=100,  # מקסימום 100 חיבורים בפול
                retryWrites=True,  # חזרה אוטומטית על כתיבות
                retryReads=True  # חזרה אוטומטית על קריאות
            )

            # בדיקת החיבור עם ping
            await self.client.admin.command("ping")

            # קבלת גישה למסד ולקולקשן
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]

            logger.info(f"התחברות מוצלחת למסד נתונים: {self.db_name}, קולקשן: {self.collection_name}")

            # הקמת אינדקסים בסיסיים
            await self._setup_basic_indexes()

            return True

        except PyMongoError as e:
            logger.error(f"שגיאה בהתחברות למסד נתונים: {e}")
            self.client = None
            self.db = None
            self.collection = None
            return False

    async def disconnect(self):
        """ניתוק מהמסד"""
        if self.client:
            self.client.close()
            logger.info("התנתקות מהמסד הושלמה")

    def _check_connection(self):
        """בדיקה שיש חיבור פעיל למסד"""
        if self.collection is None:
            raise RuntimeError("אין חיבור פעיל למסד הנתונים")

    async def _setup_basic_indexes(self):
        """הקמת אינדקסים בסיסיים לביצועים"""
        if self.collection is None:
            return

        try:
            # אינדקס על זמן יצירה ועדכון
            await self.collection.create_index([
                ("created_at", DESCENDING),
                ("updated_at", DESCENDING)
            ], background=True)

            # אינדקס טקסט לחיפוש מלא
            try:
                await self.collection.create_index([("$**", "text")], background=True)
                logger.info("אינדקס טקסט מלא נוצר בהצלחה")
            except PyMongoError:
                logger.warning("לא ניתן ליצור אינדקס טקסט מלא - יתכן שכבר קיים")

        except PyMongoError as e:
            logger.warning(f"שגיאה ביצירת אינדקסים בסיסיים: {e}")

    def _build_mongodb_filter(self, filters: List[FilterCondition]) -> Dict[str, Any]:
        """
        בניית שאילתת MongoDB מתנאי הפילטר

        Args:
            filters: רשימת תנאי פילטר

        Returns:
            Dict: שאילתת MongoDB
        """
        query = {}

        for filter_condition in filters:
            field = filter_condition.field
            operator = filter_condition.operator
            value = filter_condition.value

            # התחלת בניית התנאי לשדה הנוכחי
            field_query = {}

            if operator == FilterOperator.EQUALS:
                query[field] = value
                continue

            elif operator == FilterOperator.NOT_EQUALS:
                field_query["$ne"] = value

            elif operator == FilterOperator.GREATER_THAN:
                field_query["$gt"] = value

            elif operator == FilterOperator.GREATER_EQUAL:
                field_query["$gte"] = value

            elif operator == FilterOperator.LESS_THAN:
                field_query["$lt"] = value

            elif operator == FilterOperator.LESS_EQUAL:
                field_query["$lte"] = value

            elif operator == FilterOperator.CONTAINS:
                if filter_condition.case_sensitive:
                    field_query["$regex"] = re.escape(str(value))
                else:
                    field_query["$regex"] = re.escape(str(value))
                    field_query["$options"] = "i"

            elif operator == FilterOperator.STARTS_WITH:
                pattern = f"^{re.escape(str(value))}"
                field_query["$regex"] = pattern
                if not filter_condition.case_sensitive:
                    field_query["$options"] = "i"

            elif operator == FilterOperator.ENDS_WITH:
                pattern = f"{re.escape(str(value))}$"
                field_query["$regex"] = pattern
                if not filter_condition.case_sensitive:
                    field_query["$options"] = "i"

            elif operator == FilterOperator.IN:
                field_query["$in"] = value if isinstance(value, list) else [value]

            elif operator == FilterOperator.NOT_IN:
                field_query["$nin"] = value if isinstance(value, list) else [value]

            elif operator == FilterOperator.REGEX:
                field_query["$regex"] = str(value)
                if not filter_condition.case_sensitive:
                    field_query["$options"] = "i"

            elif operator == FilterOperator.EXISTS:
                field_query["$exists"] = bool(value)

            elif operator == FilterOperator.SIZE:
                field_query["$size"] = int(value)

            # הוספת התנאי לשאילתה
            if field_query:
                if field in query:
                    # אם יש כבר תנאי לשדה הזה, נרכב אותם
                    if isinstance(query[field], dict):
                        query[field].update(field_query)
                    else:
                        # אם השדה כבר מוגדר בערך פשוט, נהפוך אותו לתנאי מורכב
                        query[field] = {"$eq": query[field], **field_query}
                else:
                    query[field] = field_query

        return query

    def _build_mongodb_sort(self, sort_conditions: List[SortCondition]) -> List[Tuple[str, int]]:
        """
        בניית מיון למונגו

        Args:
            sort_conditions: תנאי המיון

        Returns:
            List[Tuple]: רשימת שדות ומיון למונגו
        """
        sort_list = []

        for sort_condition in sort_conditions:
            direction = ASCENDING if sort_condition.order == SortOrder.ASC else DESCENDING
            sort_list.append((sort_condition.field, direction))

        # אם לא צוין מיון, מיון ברירת מחדל לפי זמן יצירה
        if not sort_list:
            sort_list.append(("created_at", DESCENDING))

        return sort_list

    async def create_item(self, item: GenericCreate) -> Dict[str, Any]:
        """
        יצירת פריט חדש

        Args:
            item: הנתונים ליצירה

        Returns:
            Dict: הפריט שנוצר כולל מזהה
        """
        self._check_connection()

        try:
            logger.info("יוצר פריט חדש במסד הנתונים")

            # הכנת הנתונים
            item_dict = item.data.copy()

            # הוספת חותמות זמן
            now = datetime.now(timezone.utc)
            item_dict["created_at"] = now
            item_dict["updated_at"] = now

            # הכנסה למסד
            result = await self.collection.insert_one(item_dict)

            # קבלת הפריט המלא שנוצר
            created_item = await self.collection.find_one({"_id": result.inserted_id})

            if created_item:
                # המרת ObjectId למחרוזת
                created_item["_id"] = str(created_item["_id"])
                logger.info(f"פריט נוצר בהצלחה עם מזהה: {created_item['_id']}")

            return created_item

        except DuplicateKeyError as e:
            logger.warning(f"ניסיון ליצור פריט כפול: {e}")
            raise ValueError("פריט עם מזהה זה כבר קיים במסד")

        except PyMongoError as e:
            logger.error(f"שגיאה ביצירת פריט: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        קבלת פריט לפי מזהה

        Args:
            item_id: מזהה הפריט

        Returns:
            Dict או None: הפריט אם נמצא
        """
        self._check_connection()

        try:
            from bson import ObjectId
            logger.info(f"מחפש פריט עם מזהה: {item_id}")

            # חיפוש לפי ObjectId
            item = await self.collection.find_one({"_id": ObjectId(item_id)})

            if item:
                item["_id"] = str(item["_id"])
                logger.info(f"פריט נמצא: {item_id}")
            else:
                logger.info(f"פריט לא נמצא: {item_id}")

            return item

        except Exception as e:
            logger.error(f"שגיאה בחיפוש פריט {item_id}: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def update_item(self, item_id: str, item_update: GenericUpdate) -> Optional[Dict[str, Any]]:
        """
        עדכון פריט קיים

        Args:
            item_id: מזהה הפריט
            item_update: הנתונים לעדכון

        Returns:
            Dict או None: הפריט המעודכן
        """
        self._check_connection()

        try:
            from bson import ObjectId
            logger.info(f"מעדכן פריט עם מזהה: {item_id}")

            # הכנת הנתונים לעדכון
            update_data = item_update.data.copy()

            # הוספת חותמת זמן עדכון
            update_data["updated_at"] = datetime.now(timezone.utc)

            # עדכון והחזרת הפריט המעודכן
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(item_id)},
                {"$set": update_data},
                return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                logger.info(f"פריט עודכן בהצלחה: {item_id}")
            else:
                logger.info(f"פריט לא נמצא לעדכון: {item_id}")

            return result

        except Exception as e:
            logger.error(f"שגיאה בעדכון פריט {item_id}: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def delete_item(self, item_id: str) -> bool:
        """
        מחיקת פריט

        Args:
            item_id: מזהה הפריט למחיקה

        Returns:
            bool: האם המחיקה הצליחה
        """
        self._check_connection()

        try:
            from bson import ObjectId
            logger.info(f"מוחק פריט עם מזהה: {item_id}")

            result = await self.collection.delete_one({"_id": ObjectId(item_id)})
            success = result.deleted_count > 0

            if success:
                logger.info(f"פריט נמחק בהצלחה: {item_id}")
            else:
                logger.info(f"פריט לא נמצא למחיקה: {item_id}")

            return success

        except Exception as e:
            logger.error(f"שגיאה במחיקת פריט {item_id}: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def search_items(self, search_query: SearchQuery) -> PaginatedResponse:
        """
        חיפוש מתקדם בפריטים עם עימוד

        Args:
            search_query: פרמטרי החיפוש

        Returns:
            PaginatedResponse: תוצאות החיפוש עם עימוד
        """
        self._check_connection()

        try:
            logger.info(f"מבצע חיפוש מתקדם: עמוד {search_query.page}, גבול {search_query.limit}")

            # בניית שאילתת MongoDB
            mongo_query = {}

            # חיפוש טקסט חופשי
            if search_query.text:
                if search_query.fields:
                    # חיפוש בשדות ספציפיים
                    text_conditions = []
                    for field in search_query.fields:
                        text_conditions.append({
                            field: {
                                "$regex": re.escape(search_query.text),
                                "$options": "i"
                            }
                        })
                    mongo_query["$or"] = text_conditions
                else:
                    # חיפוש טקסט מלא
                    mongo_query["$text"] = {"$search": search_query.text}

            # פילטרים מתקדמים
            if search_query.filters:
                filter_query = self._build_mongodb_filter(search_query.filters)
                mongo_query.update(filter_query)

            # מיון
            sort_conditions = []
            if search_query.sort:
                sort_conditions = self._build_mongodb_sort(search_query.sort)
            else:
                sort_conditions = [("created_at", DESCENDING)]

            # חישוב offset לעימוד
            skip = (search_query.page - 1) * search_query.limit

            # ביצוע החיפוש
            cursor = self.collection.find(mongo_query).sort(sort_conditions).skip(skip).limit(search_query.limit)

            # קבלת התוצאות
            items = []
            async for item in cursor:
                item["_id"] = str(item["_id"])
                items.append(item)

            # ספירת סה"כ תוצאות (אם נדרש)
            total = None
            pages = None
            if search_query.include_count:
                total = await self.collection.count_documents(mongo_query)
                pages = (total + search_query.limit - 1) // search_query.limit

            # בניית התגובה
            response = PaginatedResponse(
                data=items,
                total=total,
                page=search_query.page,
                limit=search_query.limit,
                pages=pages,
                has_next=search_query.page < pages if pages else False,
                has_prev=search_query.page > 1
            )

            logger.info(f"חיפוש הושלם: {len(items)} תוצאות")
            return response

        except Exception as e:
            logger.error(f"שגיאה בחיפוש: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def get_all_items(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        קבלת כל הפריטים עם הגבלה

        Args:
            limit: מקסימום פריטים להחזיר
            skip: כמה פריטים לדלג

        Returns:
            List[Dict]: רשימת הפריטים
        """
        self._check_connection()

        try:
            logger.info(f"מביא כל הפריטים: גבול {limit}, דילוג {skip}")

            items = []
            cursor = self.collection.find({}).sort("created_at", DESCENDING).skip(skip).limit(limit)

            async for item in cursor:
                item["_id"] = str(item["_id"])
                items.append(item)

            logger.info(f"הובאו {len(items)} פריטים")
            return items

        except Exception as e:
            logger.error(f"שגיאה בהבאת כל הפריטים: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def bulk_create(self, items: List[Dict[str, Any]]) -> BulkResult:
        """
        יצירה חבצית של פריטים

        Args:
            items: רשימת הפריטים ליצירה

        Returns:
            BulkResult: תוצאות הפעולה החבצית
        """
        self._check_connection()

        try:
            logger.info(f"יוצר {len(items)} פריטים בפעולה חבצית")

            # הכנת הנתונים
            now = datetime.now(timezone.utc)
            prepared_items = []

            for item in items:
                prepared_item = item.copy()
                prepared_item["created_at"] = now
                prepared_item["updated_at"] = now
                prepared_items.append(prepared_item)

            # פיצול לחבצות קטנות יותר אם נדרש
            results = BulkResult()

            for i in range(0, len(prepared_items), self.max_bulk_size):
                batch = prepared_items[i:i + self.max_bulk_size]

                try:
                    insert_result = await self.collection.insert_many(batch, ordered=False)
                    results.success_count += len(insert_result.inserted_ids)
                    results.inserted_ids.extend([str(id) for id in insert_result.inserted_ids])

                except BulkWriteError as bwe:
                    results.success_count += bwe.details.get("nInserted", 0)
                    results.error_count += len(bwe.details.get("writeErrors", []))

                    for error in bwe.details.get("writeErrors", []):
                        results.errors.append(f"שגיאה באינדקס {error['index']}: {error['errmsg']}")

            logger.info(f"פעולה חבצית הושלמה: {results.success_count} הצלחות, {results.error_count} שגיאות")
            return results

        except Exception as e:
            logger.error(f"שגיאה ביצירה חבצית: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> BulkResult:
        """
        עדכון חבצי של פריטים

        Args:
            updates: רשימת עדכונים. כל עדכון צריך להכיל 'filter' ו-'update'

        Returns:
            BulkResult: תוצאות הפעולה החבצית
        """
        self._check_connection()

        try:
            logger.info(f"מעדכן {len(updates)} פריטים בפעולה חבצית")

            from pymongo import UpdateOne

            # הכנת הפעולות
            operations = []
            now = datetime.now(timezone.utc)

            for update in updates:
                if "filter" in update and "update" in update:
                    update_data = update["update"].copy()
                    update_data["updated_at"] = now

                    operations.append(UpdateOne(
                        update["filter"],
                        {"$set": update_data}
                    ))

            # ביצוע העדכון החבצי
            if operations:
                result = await self.collection.bulk_write(operations, ordered=False)

                bulk_result = BulkResult()
                bulk_result.success_count = result.modified_count
                bulk_result.modified_count = result.modified_count

                logger.info(f"עדכון חבצי הושלם: {bulk_result.modified_count} פריטים עודכנו")
                return bulk_result
            else:
                logger.warning("לא נמצאו פעולות עדכון תקינות")
                return BulkResult()

        except Exception as e:
            logger.error(f"שגיאה בעדכון חבצי: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def bulk_delete(self, filters: List[Dict[str, Any]]) -> BulkResult:
        """
        מחיקה חבצית של פריטים

        Args:
            filters: רשימת פילטרים למחיקה

        Returns:
            BulkResult: תוצאות הפעולה החבצית
        """
        self._check_connection()

        try:
            logger.info(f"מוחק פריטים בפעולה חבצית עם {len(filters)} פילטרים")

            from pymongo import DeleteMany

            # הכנת הפעולות
            operations = []
            for filter_dict in filters:
                operations.append(DeleteMany(filter_dict))

            # ביצוע המחיקה החבצית
            if operations:
                result = await self.collection.bulk_write(operations, ordered=False)

                bulk_result = BulkResult()
                bulk_result.success_count = result.deleted_count
                bulk_result.deleted_count = result.deleted_count

                logger.info(f"מחיקה חבצית הושלמה: {bulk_result.deleted_count} פריטים נמחקו")
                return bulk_result
            else:
                logger.warning("לא נמצאו פעולות מחיקה תקינות")
                return BulkResult()

        except Exception as e:
            logger.error(f"שגיאה במחיקה חבצית: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def get_statistics(self) -> StatisticsResponse:
        """
        קבלת סטטיסטיקות על הקולקשן

        Returns:
            StatisticsResponse: סטטיסטיקות מפורטות
        """
        self._check_connection()

        try:
            logger.info("אוסף סטטיסטיקות על הקולקשן")

            # סטטיסטיקות בסיסיות
            stats = await self.db.command("collStats", self.collection_name)

            # ספירת מסמכים
            document_count = await self.collection.count_documents({})

            # מידע על אינדקסים
            indexes = await self.collection.list_indexes().to_list(length=None)

            # עדכון אחרון (אם קיים שדה updated_at)
            last_updated = None
            try:
                last_doc = await self.collection.find_one(
                    {"updated_at": {"$exists": True}},
                    sort=[("updated_at", DESCENDING)]
                )
                if last_doc and "updated_at" in last_doc:
                    last_updated = last_doc["updated_at"]
            except:
                pass

            response = StatisticsResponse(
                total_documents=document_count,
                collection_size_bytes=stats.get("size", 0),
                average_document_size=stats.get("avgObjSize", 0),
                indexes_count=len(indexes),
                last_updated=last_updated
            )

            logger.info(f"סטטיסטיקות נאספו: {document_count} מסמכים")
            return response

        except Exception as e:
            logger.error(f"שגיאה בקבלת סטטיסטיקות: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def create_index(self, index_info: IndexInfo) -> bool:
        """
        יצירת אינדקס חדש

        Args:
            index_info: מידע על האינדקס ליצירה

        Returns:
            bool: האם האינדקס נוצר בהצלחה
        """
        self._check_connection()

        try:
            logger.info(f"יוצר אינדקס: {index_info.name}")

            # המרה לפורמט של מונגו
            index_fields = [(field, direction) for field, direction in index_info.fields.items()]

            # יצירת האינדקס
            await self.collection.create_index(
                index_fields,
                name=index_info.name,
                unique=index_info.unique,
                sparse=index_info.sparse,
                background=index_info.background
            )

            logger.info(f"אינדקס נוצר בהצלחה: {index_info.name}")
            return True

        except Exception as e:
            logger.error(f"שגיאה ביצירת אינדקס {index_info.name}: {e}")
            return False

    async def drop_index(self, index_name: str) -> bool:
        """
        מחיקת אינדקס

        Args:
            index_name: שם האינדקס למחיקה

        Returns:
            bool: האם האינדקס נמחק בהצלחה
        """
        self._check_connection()

        try:
            logger.info(f"מוחק אינדקס: {index_name}")

            await self.collection.drop_index(index_name)

            logger.info(f"אינדקס נמחק בהצלחה: {index_name}")
            return True

        except Exception as e:
            logger.error(f"שגיאה במחיקת אינדקס {index_name}: {e}")
            return False

    async def get_schema_info(self) -> SchemaInfo:
        """
        קבלת מידע על מבנה הנתונים בקולקשן

        Returns:
            SchemaInfo: מידע על הסכמה
        """
        self._check_connection()

        try:
            logger.info("אוסף מידע על מבנה הנתונים")

            # דגימת מסמכים לניתוח הסכמה
            sample_docs = await self.collection.aggregate([
                {"$sample": {"size": 100}},  # דגימה של 100 מסמכים
                {"$project": {"data": "$ROOT"}}
            ]).to_list(length=None)

            # ניתוח השדות
            field_analysis = {}

            for doc in sample_docs:
                if "data" in doc:
                    self._analyze_fields(doc["data"], field_analysis)

            # המרה לרשימת FieldInfo
            fields = []
            for field_name, field_data in field_analysis.items():
                if field_name not in ["_id", "created_at", "updated_at"]:  # מדלגים על שדות מערכת
                    field_info = FieldInfo(
                        name=field_name,
                        type=self._determine_field_type(field_data["types"]),
                        required=field_data["count"] == len(sample_docs),
                        searchable=True,
                        sortable=True
                    )
                    fields.append(field_info)

            schema = SchemaInfo(
                collection_name=self.collection_name,
                fields=fields,
                description=f"סכמה שנותחה מ-{len(sample_docs)} מסמכים"
            )

            logger.info(f"ניתוח סכמה הושלם: {len(fields)} שדות")
            return schema

        except Exception as e:
            logger.error(f"שגיאה בניתוח סכמה: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    def _analyze_fields(self, doc: Dict[str, Any], field_analysis: Dict[str, Any], prefix: str = ""):
        """
        ניתוח רקורסיבי של שדות במסמך

        Args:
            doc: המסמך לניתוח
            field_analysis: המילון לאכלוס תוצאות הניתוח
            prefix: קידומת לשדות מקוננים
        """
        for key, value in doc.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if full_key not in field_analysis:
                field_analysis[full_key] = {"types": set(), "count": 0}

            field_analysis[full_key]["count"] += 1

            # זיהוי סוג השדה
            if isinstance(value, str):
                field_analysis[full_key]["types"].add("string")
            elif isinstance(value, int):
                field_analysis[full_key]["types"].add("integer")
            elif isinstance(value, float):
                field_analysis[full_key]["types"].add("float")
            elif isinstance(value, bool):
                field_analysis[full_key]["types"].add("boolean")
            elif isinstance(value, list):
                field_analysis[full_key]["types"].add("array")
            elif isinstance(value, dict):
                field_analysis[full_key]["types"].add("object")
                # ניתוח רקורסיבי של אובייקטים מקוננים
                self._analyze_fields(value, field_analysis, full_key)
            elif value is None:
                field_analysis[full_key]["types"].add("null")

    def _determine_field_type(self, types: set) -> FieldType:
        """
        קביעת סוג השדה בהתבסס על הסוגים שנמצאו

        Args:
            types: קבוצת הסוגים שנמצאו

        Returns:
            FieldType: סוג השדה המומלץ
        """
        if "string" in types:
            return FieldType.TEXT
        elif "integer" in types or "float" in types:
            return FieldType.NUMBER
        elif "boolean" in types:
            return FieldType.BOOLEAN
        else:
            return FieldType.TEXT

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ביצוע aggregation מותאם אישית

        Args:
            pipeline: pipeline של מונגו לביצוע

        Returns:
            List[Dict]: תוצאות ה-aggregation
        """
        self._check_connection()

        try:
            logger.info(f"מבצע aggregation עם {len(pipeline)} שלבים")

            results = []
            async for doc in self.collection.aggregate(pipeline):
                if "_id" in doc and doc["_id"]:
                    doc["_id"] = str(doc["_id"])
                results.append(doc)

            logger.info(f"aggregation הושלם: {len(results)} תוצאות")
            return results

        except Exception as e:
            logger.error(f"שגיאה ב-aggregation: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def export_data(self, search_query: Optional[SearchQuery] = None,
                          format: ExportFormat = ExportFormat.JSON) -> str:
        """
        ייצוא נתונים

        Args:
            search_query: שאילתה לייצוא (אם לא צוין - הכל)
            format: פורמט הייצוא

        Returns:
            str: הנתונים המיוצאים
        """
        self._check_connection()

        try:
            logger.info(f"מייצא נתונים בפורמט {format}")

            # קבלת הנתונים
            if search_query:
                response = await self.search_items(search_query)
                data = response.data
            else:
                data = await self.get_all_items(limit=10000)  # הגבלה למניעת עומס

            # ייצוא לפי הפורמט
            if format == ExportFormat.JSON:
                import json
                return json.dumps(data, ensure_ascii=False, indent=2, default=str)

            elif format == ExportFormat.CSV:
                if not data:
                    return ""

                import csv
                import io

                output = io.StringIO()

                # קבלת כותרות מהמסמך הראשון
                if data:
                    fieldnames = set()
                    for item in data:
                        fieldnames.update(self._flatten_dict(item).keys())

                    writer = csv.DictWriter(output, fieldnames=list(fieldnames))
                    writer.writeheader()

                    for item in data:
                        flattened = self._flatten_dict(item)
                        writer.writerow(flattened)

                return output.getvalue()

            else:
                raise ValueError(f"פורמט לא נתמך: {format}")

            logger.info(f"ייצוא הושלם: {len(data)} פריטים")

        except Exception as e:
            logger.error(f"שגיאה בייצוא נתונים: {e}")
            raise RuntimeError(f"שגיאה בייצוא: {e}")

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """
        פירוק מילון מקונן למילון שטוח

        Args:
            d: המילון לפירוק
            parent_key: מפתח האב
            sep: מפריד בין רמות

        Returns:
            Dict: מילון שטוח
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))  # המרת רשימות למחרוזת
            else:
                items.append((new_key, v))
        return dict(items)

    async def import_data(self, data: List[Dict[str, Any]], replace_existing: bool = False) -> ImportResult:
        """
        ייבוא נתונים

        Args:
            data: הנתונים לייבוא
            replace_existing: האם להחליף קיימים

        Returns:
            ImportResult: תוצאות הייבוא
        """
        self._check_connection()

        try:
            import time
            start_time = time.time()

            logger.info(f"מייבא {len(data)} פריטים")

            result = ImportResult()
            result.total_rows = len(data)

            if replace_existing:
                # מחיקת כל הנתונים הקיימים
                await self.collection.delete_many({})
                logger.info("נתונים קיימים נמחקו")

            # ייבוא הנתונים
            bulk_result = await self.bulk_create(data)

            result.successful_imports = bulk_result.success_count
            result.failed_imports = bulk_result.error_count
            result.errors = bulk_result.errors

            result.duration_seconds = time.time() - start_time

            logger.info(f"ייבוא הושלם: {result.successful_imports} הצלחות, {result.failed_imports} כשלונות")
            return result

        except Exception as e:
            logger.error(f"שגיאה בייבוא נתונים: {e}")
            raise RuntimeError(f"שגיאה בייבוא: {e}")

    async def health_check(self) -> HealthCheck:
        """
        בדיקת בריאות המערכת

        Returns:
            HealthCheck: סטטוס הבריאות
        """
        import time
        start_time = time.time()

        try:
            # בדיקת חיבור למסד
            if self.client is None:
                return HealthCheck(
                    status="unhealthy",
                    database_connected=False,
                    collections_accessible=False,
                    response_time_ms=0,
                    last_check=datetime.now(timezone.utc)
                )

            # בדיקת ping למסד
            await self.client.admin.command("ping")

            # בדיקת גישה לקולקשן
            collections_accessible = True
            try:
                await self.collection.find_one()
            except:
                collections_accessible = False

            response_time = (time.time() - start_time) * 1000  # המרה למילישניות

            # קביעת סטטוס כללי
            if collections_accessible and response_time < 1000:
                status = "healthy"
            elif collections_accessible:
                status = "degraded"
            else:
                status = "unhealthy"

            return HealthCheck(
                status=status,
                database_connected=True,
                collections_accessible=collections_accessible,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"שגיאה בבדיקת בריאות: {e}")
            return HealthCheck(
                status="unhealthy",
                database_connected=False,
                collections_accessible=False,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(timezone.utc)
            )

    async def get_distinct_values(self, field: str, filter_query: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        קבלת ערכים ייחודיים לשדה מסוים

        Args:
            field: שם השדה
            filter_query: פילטר אופציונלי

        Returns:
            List: רשימת ערכים ייחודיים
        """
        self._check_connection()

        try:
            logger.info(f"מביא ערכים ייחודיים עבור שדה: {field}")

            query = filter_query or {}
            distinct_values = await self.collection.distinct(field, query)

            logger.info(f"נמצאו {len(distinct_values)} ערכים ייחודיים")
            return distinct_values

        except Exception as e:
            logger.error(f"שגיאה בקבלת ערכים ייחודיים: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def count_documents(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        """
        ספירת מסמכים

        Args:
            filter_query: פילטר אופציונלי

        Returns:
            int: מספר המסמכים
        """
        self._check_connection()

        try:
            query = filter_query or {}
            count = await self.collection.count_documents(query)

            logger.info(f"נספרו {count} מסמכים")
            return count

        except Exception as e:
            logger.error(f"שגיאה בספירת מסמכים: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def find_duplicates(self, fields: List[str]) -> List[Dict[str, Any]]:
        """
        מציאת רשומות כפולות בהתבסס על שדות מסוימים

        Args:
            fields: רשימת שדות לבדיקה

        Returns:
            List[Dict]: רשימת כפולות
        """
        self._check_connection()

        try:
            logger.info(f"מחפש כפולות בשדות: {fields}")

            # בניית pipeline ל-aggregation
            group_stage = {"_id": {}}
            for field in fields:
                group_stage["_id"][field] = f"${field}"

            group_stage["count"] = {"$sum": 1}
            group_stage["docs"] = {"$push": "$ROOT"}

            pipeline = [
                {"$group": group_stage},
                {"$match": {"count": {"$gt": 1}}},
                {"$project": {
                    "duplicates": "$docs",
                    "count": 1,
                    "fields": "$_id"
                }}
            ]

            duplicates = await self.aggregate(pipeline)

            logger.info(f"נמצאו {len(duplicates)} קבוצות כפולות")
            return duplicates

        except Exception as e:
            logger.error(f"שגיאה במציאת כפולות: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def cleanup_old_records(self, days_old: int = 30, date_field: str = "created_at") -> int:
        """
        ניקוי רשומות ישנות

        Args:
            days_old: כמה ימים ישנות
            date_field: שדה התאריך לבדיקה

        Returns:
            int: כמות רשומות שנמחקו
        """
        self._check_connection()

        try:
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

            logger.info(f"מנקה רשומות ישנות מ-{cutoff_date}")

            result = await self.collection.delete_many({
                date_field: {"$lt": cutoff_date}
            })

            deleted_count = result.deleted_count
            logger.info(f"נמחקו {deleted_count} רשומות ישנות")

            return deleted_count

        except Exception as e:
            logger.error(f"שגיאה בניקוי רשומות ישנות: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def backup_collection(self, backup_path: str) -> bool:
        """
        גיבוי הקולקשן לקובץ

        Args:
            backup_path: נתיב הגיבוי

        Returns:
            bool: האם הגיבוי הצליח
        """
        try:
            logger.info(f"מתחיל גיבוי לנתיב: {backup_path}")

            # קבלת כל הנתונים
            all_data = await self.get_all_items(limit=1000000)  # הגבלה גבוהה לגיבוי

            # שמירה לקובץ JSON
            import json
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "collection": self.collection_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "count": len(all_data),
                    "data": all_data
                }, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"גיבוי הושלם: {len(all_data)} רשומות")
            return True

        except Exception as e:
            logger.error(f"שגיאה בגיבוי: {e}")
            return False

    async def restore_collection(self, backup_path: str, replace_existing: bool = False) -> ImportResult:
        """
        שחזור הקולקשן מגיבוי

        Args:
            backup_path: נתיב הגיבוי
            replace_existing: האם להחליף נתונים קיימים

        Returns:
            ImportResult: תוצאות השחזור
        """
        try:
            logger.info(f"משחזר מגיבוי: {backup_path}")

            # קריאת קובץ הגיבוי
            import json
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # חילוץ הנתונים
            if "data" not in backup_data:
                raise ValueError("קובץ גיבוי לא תקין - חסר שדה data")

            data = backup_data["data"]

            # שחזור הנתונים
            result = await self.import_data(data, replace_existing)

            logger.info(f"שחזור הושלם: {result.successful_imports} רשומות")
            return result

        except Exception as e:
            logger.error(f"שגיאה בשחזור: {e}")
            raise RuntimeError(f"שגיאה בשחזור: {e}")

    async def optimize_collection(self) -> Dict[str, Any]:
        """
        אופטימיזציה של הקולקשן

        Returns:
            Dict: תוצאות האופטימיזציה
        """
        self._check_connection()

        try:
            logger.info("מתחיל אופטימיזציה של הקולקשן")

            results = {}

            # דחיסת הקולקשן
            try:
                compress_result = await self.db.command("compact", self.collection_name)
                results["compaction"] = "הצליח"
            except Exception as e:
                results["compaction"] = f"נכשל: {e}"

            # ביצוע reIndex
            try:
                await self.collection.reindex()
                results["reindex"] = "הצליח"
            except Exception as e:
                results["reindex"] = f"נכשל: {e}"

            # קבלת סטטיסטיקות לאחר האופטימיזציה
            stats = await self.get_statistics()
            results["final_stats"] = {
                "total_documents": stats.total_documents,
                "collection_size_bytes": stats.collection_size_bytes,
                "indexes_count": stats.indexes_count
            }

            logger.info("אופטימיזציה הושלמה")
            return results

        except Exception as e:
            logger.error(f"שגיאה באופטימיזציה: {e}")
            raise RuntimeError(f"שגיאה באופטימיזציה: {e}")

    async def validate_data_integrity(self) -> Dict[str, Any]:
        """
        אימות תקינות הנתונים

        Returns:
            Dict: תוצאות האימות
        """
        self._check_connection()

        try:
            logger.info("מאמת תקינות נתונים")

            results = {
                "total_documents": 0,
                "valid_documents": 0,
                "invalid_documents": 0,
                "errors": [],
                "warnings": []
            }

            # ספירת כל המסמכים
            total_docs = await self.collection.count_documents({})
            results["total_documents"] = total_docs

            # בדיקת מסמכים עם חותמות זמן חסרות
            missing_timestamps = await self.collection.count_documents({
                "$or": [
                    {"created_at": {"$exists": False}},
                    {"updated_at": {"$exists": False}}
                ]
            })

            if missing_timestamps > 0:
                results["warnings"].append(f"{missing_timestamps} מסמכים חסרים חותמות זמן")

            # בדיקת מסמכים ריקים או פגומים
            empty_docs = await self.collection.count_documents({"data": {"$exists": False}})
            if empty_docs > 0:
                results["errors"].append(f"{empty_docs} מסמכים ללא שדה data")
                results["invalid_documents"] += empty_docs

            # בדיקת עקביות אינדקסים
            try:
                validate_result = await self.db.command("validate", self.collection_name)
                if not validate_result.get("valid", True):
                    results["errors"].append("קולקשן לא תקין על פי אימות מונגו")
            except Exception as e:
                results["warnings"].append(f"לא ניתן לאמת את הקולקשן: {e}")

            results["valid_documents"] = total_docs - results["invalid_documents"]

            logger.info(f"אימות הושלם: {results['valid_documents']}/{total_docs} מסמכים תקינים")
            return results

        except Exception as e:
            logger.error(f"שגיאה באימות נתונים: {e}")
            raise RuntimeError(f"שגיאה באימות: {e}")

    async def get_collection_info(self) -> Dict[str, Any]:
        """
        קבלת מידע מפורט על הקולקשן

        Returns:
            Dict: מידע מפורט
        """
        self._check_connection()

        try:
            logger.info("אוסף מידע מפורט על הקולקשן")

            # סטטיסטיקות בסיסיות
            stats = await self.db.command("collStats", self.collection_name)

            # רשימת אינדקסים
            indexes = await self.collection.list_indexes().to_list(length=None)

            # מידע על שרדינג (אם קיים)
            shard_info = None
            try:
                shard_info = await self.db.command("collStats", self.collection_name, verbose=True)
            except:
                pass

            # מידע על validation rules (אם קיימות)
            collection_info = await self.db.list_collections(filter={"name": self.collection_name}).to_list(length=1)
            validation_rules = None
            if collection_info and "options" in collection_info[0]:
                validation_rules = collection_info[0]["options"].get("validator")

            info = {
                "name": self.collection_name,
                "database": self.db_name,
                "document_count": stats.get("count", 0),
                "size_bytes": stats.get("size", 0),
                "storage_size_bytes": stats.get("storageSize", 0),
                "average_document_size": stats.get("avgObjSize", 0),
                "indexes": [
                    {
                        "name": idx["name"],
                        "keys": idx["key"],
                        "unique": idx.get("unique", False),
                        "sparse": idx.get("sparse", False)
                    }
                    for idx in indexes
                ],
                "total_index_size": stats.get("totalIndexSize", 0),
                "validation_rules": validation_rules,
                "shard_info": shard_info,
                "last_modified": stats.get("lastModified")
            }

            logger.info("מידע על הקולקשן נאסף בהצלחה")
            return info

        except Exception as e:
            logger.error(f"שגיאה בקבלת מידע על הקולקשן: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    def set_collection(self, collection_name: str):
        """
        החלפת הקולקשן הפעיל

        Args:
            collection_name: שם הקולקשן החדש
        """
        if self.db:
            self.collection_name = collection_name
            self.collection = self.db[collection_name]
            logger.info(f"עבר לקולקשן: {collection_name}")
        else:
            raise RuntimeError("אין חיבור פעיל למסד הנתונים")

    async def list_collections(self) -> List[str]:
        """
        קבלת רשימת כל הקולקשנים במסד

        Returns:
            List[str]: רשימת שמות הקולקשנים
        """
        self._check_connection()

        try:
            collections = await self.db.list_collection_names()
            logger.info(f"נמצאו {len(collections)} קולקשנים")
            return collections

        except Exception as e:
            logger.error(f"שגיאה בקבלת רשימת קולקשנים: {e}")
            raise RuntimeError(f"שגיאה במסד הנתונים: {e}")

    async def create_collection(self, collection_name: str, **options) -> bool:
        """
        יצירת קולקשן חדש

        Args:
            collection_name: שם הקולקשן
            **options: אפשרויות נוספות לקולקשן

        Returns:
            bool: האם היצירה הצליחה
        """
        self._check_connection()

        try:
            logger.info(f"יוצר קולקשן חדש: {collection_name}")

            await self.db.create_collection(collection_name, **options)

            logger.info(f"קולקשן נוצר בהצלחה: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"שגיאה ביצירת קולקשן {collection_name}: {e}")
            return False

    async def drop_collection(self, collection_name: str) -> bool:
        """
        מחיקת קולקשן

        Args:
            collection_name: שם הקולקשן למחיקה

        Returns:
            bool: האם המחיקה הצליחה
        """
        self._check_connection()

        try:
            logger.warning(f"מוחק קולקשן: {collection_name}")

            await self.db.drop_collection(collection_name)

            logger.info(f"קולקשן נמחק: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"שגיאה במחיקת קולקשן {collection_name}: {e}")
            return False