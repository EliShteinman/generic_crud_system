# app/processing/services/user_activity_service.py

from ..abstract_service import AbstractAnalysisService
from ...dal.data_access_layer import MongoQueryBuilder # שינוי בייבוא
from typing import Any, Dict

class UserActivitySummaryService(AbstractAnalysisService):
    FETCH_DATA_FIRST = False

    async def process(self, data: Any, **kwargs) -> Dict[str, Any]:
        # הוצאת הפרמטרים החדשים מ-kwargs
        base_filter = kwargs.get("base_filter", {})
        query_builder: MongoQueryBuilder = kwargs.get("query_builder")

        if not query_builder:
            raise RuntimeError("UserActivitySummaryService requires a query_builder instance.")

        # 1. בניית פייפליין האגרגציה (זהה לקודם)
        pipeline = []
        if base_filter:
            pipeline.append({"$match": base_filter})

        pipeline.append({
            "$group": {
                "_id": "$user_id",
                "event_count": {"$sum": 1},
                "event_types": {"$addToSet": "$event_type"}
            }
        })
        pipeline.append({"$sort": {"event_count": -1}})

        # 2. שימוש ב-QueryBuilder שהתקבל כדי להריץ את האגרגציה
        #    (במקום ליצור אחד חדש)
        aggregation_result = await query_builder.execute_aggregation_pipeline(pipeline)

        return aggregation_result