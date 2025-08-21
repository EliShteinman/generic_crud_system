import logging
from typing import List, Dict, Any, Optional

from pymongo import AsyncMongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError

logger = logging.getLogger(__name__)


class MongoQueryBuilder:
    """
    הקלאס הזה נשאר זהה ברובו, כי הוא עונה על דרישת ה-Builder מהפרומפט המקורי.
    הוא כלי עזר שיוחזר על ידי ה-DAL.
    """

    def __init__(self, collection):
        self.collection = collection
        self._filter: Dict[str, Any] = {}
        self._sort: Optional[List[tuple]] = None
        self._limit: Optional[int] = None
        self._skip: Optional[int] = None
        self._projection: Optional[Dict[str, int]] = None

    # ... כל המתודות של ה-Builder (add_filter, set_sort, etc.) נשארות כאן ...
    def add_filter(self, field: str, operator: str, value: Any) -> 'MongoQueryBuilder':
        op_map = {
            "eq": "$eq", "ne": "$ne", "gt": "$gt", "gte": "$gte", "lt": "$lt", "lte": "$lte",
            "in": "$in", "nin": "$nin", "exists": "$exists", "type": "$type", "all": "$all", "size": "$size"
        }
        if operator == "regex":
            self._filter.setdefault(field, {})['$regex'] = value.get("pattern", "")
            if "options" in value: self._filter[field]['$options'] = value["options"]
        elif operator in op_map:
            self._filter.setdefault(field, {})[op_map[operator]] = value
        else:
            raise ValueError(f"אופרטור לא נתמך: {operator}")
        return self

    def add_elem_match(self, field: str, criteria_dict: Dict[str, Any]) -> 'MongoQueryBuilder':
        self._filter.setdefault(field, {})['$elemMatch'] = criteria_dict
        return self

    def add_or_condition(self, conditions: List[Dict[str, Any]]) -> 'MongoQueryBuilder':
        if "$or" in self._filter:
            self._filter["$or"].extend(conditions)
        else:
            self._filter["$or"] = conditions
        return self

    def set_sort(self, field: str, direction: int) -> 'MongoQueryBuilder':
        if self._sort is None: self._sort = []
        self._sort.append((field, direction))
        return self

    def set_limit(self, count: int) -> 'MongoQueryBuilder':
        self._limit = count
        return self

    def set_skip(self, count: int) -> 'MongoQueryBuilder':
        self._skip = count
        return self

    async def execute(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find(self._filter, self._projection)
        if self._sort: cursor = cursor.sort(self._sort)
        if self._skip: cursor = cursor.skip(self._skip)
        if self._limit: cursor = cursor.limit(self._limit)
        return await cursor.to_list(length=self._limit)

    async def execute_aggregation_pipeline(self, pipeline_stages: List[Dict]) -> List[Dict]:
        cursor = self.collection.aggregate(pipeline_stages)
        return await cursor.to_list(length=None)


class AnalyticsDAL:
    """
    שכבת הגישה לנתונים החדשה, בהשראת הדוגמה שלך.
    היא מנהלת את החיבור ומספקת Query Builders לפי דרישה.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[Database] = None

    async def connect(self):
        """יוצר חיבור א-סינכרוני למסד הנתונים."""
        try:
            self.client = AsyncMongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            await self.client.admin.command("ping")
            # שם מסד הנתונים יכול להגיע ממשתנה סביבה או להיות קבוע
            self.db = self.client.get_database("analytics_db")
            logger.info("Successfully connected to MongoDB.")
        except PyMongoError as e:
            logger.error(f"DATABASE CONNECTION FAILED: {e}")
            self.client = None
            self.db = None

    def disconnect(self):
        """סוגר את החיבור למסד הנתונים."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB.")

    def get_query_builder(self, collection_name: str) -> MongoQueryBuilder:
        """
        מחזיר מופע של Query Builder עבור קולקשן ספציפי.
        זוהי נקודת הכניסה של שאר האפליקציה לביצוע שאילתות.
        """
        if self.db is None:
            raise RuntimeError("Database connection is not available.")
        return MongoQueryBuilder(self.db[collection_name])