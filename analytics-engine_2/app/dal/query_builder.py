from typing import Dict, Any, List, Optional, Union
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
import logging
import re

logger = logging.getLogger(__name__)


class MongoQueryBuilder:
    """Builder Pattern לבניית שאילתות MongoDB"""

    def __init__(self, collection: Collection):
        self.collection = collection
        self.query: Dict[str, Any] = {}
        self.sort_params: Optional[List[tuple]] = None
        self.limit_count: Optional[int] = None
        self.skip_count: int = 0

    def add_filter(self, field: str, operator: str, value: Any, options: Optional[Dict] = None) -> 'MongoQueryBuilder':
        """הוספת תנאי סינון"""

        # אופרטורים בסיסיים
        if operator == "eq":
            self.query[field] = value
        elif operator == "ne":
            self.query[field] = {"$ne": value}
        elif operator == "gt":
            self.query[field] = {"$gt": value}
        elif operator == "gte":
            self.query[field] = {"$gte": value}
        elif operator == "lt":
            self.query[field] = {"$lt": value}
        elif operator == "lte":
            self.query[field] = {"$lte": value}

        # אופרטורים של רשימה
        elif operator == "in":
            self.query[field] = {"$in": value}
        elif operator == "nin":
            self.query[field] = {"$nin": value}

        # אופרטורים מבניים
        elif operator == "exists":
            self.query[field] = {"$exists": value}
        elif operator == "type":
            self.query[field] = {"$type": value}

        # חיפוש טקסט
        elif operator == "regex":
            regex_options = 0
            if options and options.get("case_insensitive"):
                regex_options = re.IGNORECASE
            self.query[field] = {"$regex": value, "$options": "i" if regex_options else ""}

        # אופרטורים על מערכים
        elif operator == "all":
            self.query[field] = {"$all": value}
        elif operator == "size":
            self.query[field] = {"$size": value}

        else:
            logger.warning(f"Unknown operator: {operator}")

        return self

    def add_elem_match(self, field: str, criteria: Dict[str, Any]) -> 'MongoQueryBuilder':
        """הוספת תנאי elemMatch למערך"""
        self.query[field] = {"$elemMatch": criteria}
        return self

    def add_or_condition(self, conditions: List[Dict[str, Any]]) -> 'MongoQueryBuilder':
        """הוספת תנאי OR"""
        if "$or" not in self.query:
            self.query["$or"] = []
        self.query["$or"].extend(conditions)
        return self

    def set_sort(self, field: str, direction: str = "asc") -> 'MongoQueryBuilder':
        """הגדרת מיון"""
        sort_direction = ASCENDING if direction.lower() == "asc" else DESCENDING
        if not self.sort_params:
            self.sort_params = []
        self.sort_params.append((field, sort_direction))
        return self

    def set_limit(self, count: int) -> 'MongoQueryBuilder':
        """הגדרת מגבלת תוצאות"""
        self.limit_count = count
        return self

    def set_skip(self, count: int) -> 'MongoQueryBuilder':
        """הגדרת דילוג על תוצאות"""
        self.skip_count = count
        return self

    def build(self) -> Dict[str, Any]:
        """בניית השאילתה הסופית"""
        return {
            "filter": self.query,
            "sort": self.sort_params,
            "limit": self.limit_count,
            "skip": self.skip_count
        }

    def execute(self) -> List[Dict[str, Any]]:
        """ביצוע השאילתה"""
        try:
            cursor = self.collection.find(self.query)

            if self.sort_params:
                cursor = cursor.sort(self.sort_params)

            if self.skip_count > 0:
                cursor = cursor.skip(self.skip_count)

            if self.limit_count:
                cursor = cursor.limit(self.limit_count)

            results = list(cursor)

            # המרת ObjectId למחרוזת
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            logger.info(f"Query executed successfully, found {len(results)} documents")
            return results

        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise

    def execute_aggregation_pipeline(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ביצוע פייפליין אגרגציה"""
        try:
            cursor = self.collection.aggregate(pipeline)
            results = list(cursor)

            # המרת ObjectId למחרוזת
            for doc in results:
                if "_id" in doc and hasattr(doc["_id"], "__str__"):
                    doc["_id"] = str(doc["_id"])

            logger.info(f"Aggregation pipeline executed successfully, returned {len(results)} documents")
            return results

        except Exception as e:
            logger.error(f"Error executing aggregation pipeline: {str(e)}")
            raise