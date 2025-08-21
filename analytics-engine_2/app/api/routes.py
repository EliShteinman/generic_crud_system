from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import time
import logging
from app.models.request_models import (
    QueryRequest,
    AnalysisResponse,
    HealthResponse,
    FilterCondition,
    OrCondition
)
from app.dal.mongo_client import mongo_client
from app.dal.query_builder import MongoQueryBuilder
from app.services.pipeline_manager import PipelineManager
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, str])
async def root():
    """בדיקת חיות בסיסית"""
    return {
        "status": "alive",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """בדיקת בריאות מפורטת"""

    db_connected = mongo_client.is_connected()

    health_status = HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        version=settings.VERSION,
        database_connected=db_connected,
        details={
            "database": settings.DATABASE_NAME,
            "collection": settings.COLLECTION_NAME
        }
    )

    if not db_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )

    return health_status


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(request: QueryRequest):
    """נקודת הקצה הראשית לניתוח נתונים"""

    start_time = time.time()

    try:
        # בדיקת חיבור למסד נתונים
        if not mongo_client.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )

        # בניית השאילתה
        query_builder = MongoQueryBuilder(mongo_client.collection)

        # הוספת תנאי סינון
        for filter_item in request.criteria.filters:
            if isinstance(filter_item, FilterCondition):
                query_builder.add_filter(
                    field=filter_item.field,
                    operator=filter_item.operator.value,
                    value=filter_item.value,
                    options=filter_item.options
                )
            elif isinstance(filter_item, OrCondition):
                or_conditions = []
                for condition in filter_item.conditions:
                    or_dict = {condition.field: condition.value}
                    if condition.operator != "eq":
                        or_dict = {condition.field: {f"${condition.operator.value}": condition.value}}
                    or_conditions.append(or_dict)
                query_builder.add_or_condition(or_conditions)

        # הוספת מיון
        if request.criteria.sort_field:
            query_builder.set_sort(
                request.criteria.sort_field,
                request.criteria.sort_direction.value
            )

        # הוספת דיפדוף ומגבלה
        if request.criteria.skip:
            query_builder.set_skip(request.criteria.skip)
        if request.criteria.limit:
            query_builder.set_limit(request.criteria.limit)

        # ביצוע השאילתה
        logger.info(f"Executing query with criteria: {request.criteria}")
        raw_data = query_builder.execute()

        # הפעלת ניתוחים אם נדרש
        analyses_results = {}
        if request.analyses:
            # בדיקת תקינות הניתוחים המבוקשים
            pipeline_manager = PipelineManager(use_aggregation=False)  # ניתן לשנות ל-True עבור אגרגציה
            valid_analyses, invalid_analyses = pipeline_manager.validate_analyses(request.analyses)

            if invalid_analyses:
                logger.warning(f"Invalid analyses requested: {invalid_analyses}")

            if valid_analyses:
                # הפעלת הניתוחים התקינים
                analysis_result = pipeline_manager.execute_analyses(
                    raw_data=raw_data,
                    analysis_names=valid_analyses,
                    query_builder=query_builder,
                    base_query=query_builder.query
                )
                analyses_results = analysis_result.get("results", {})

        # חישוב זמן ביצוע
        execution_time = (time.time() - start_time) * 1000

        response = AnalysisResponse(
            raw_data_count=len(raw_data),
            analyses_results=analyses_results,
            execution_time_ms=round(execution_time, 2)
        )

        logger.info(f"Request completed successfully in {execution_time:.2f}ms")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.get("/available-analyses")
async def get_available_analyses():
    """קבלת רשימת הניתוחים הזמינים"""
    from app.services.analysis_services import AVAILABLE_SERVICES

    return {
        "available_analyses": list(AVAILABLE_SERVICES.keys()),
        "count": len(AVAILABLE_SERVICES)
    }