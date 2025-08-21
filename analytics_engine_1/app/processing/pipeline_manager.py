# app/processing/pipeline_manager.py

from typing import List, Dict, Any

# ייבוא המודלים וה-DAL
# שימו לב לייבוא המודל החדש AnalysisRequest
from ..api.models import SearchCriteria, AnalysisRequest
from ..dal.data_access_layer import AnalyticsDAL, MongoQueryBuilder

# רישום דינמי של כל שירותי העיבוד הזמינים
from .services.sales_by_region_service import SalesByRegionService
from .services.user_activity_service import UserActivitySummaryService
from .services.grouping_service import GroupingService  # השירות הגנרי החדש

AVAILABLE_SERVICES = {
    # שירותים "טיפשים" שלא מקבלים פרמטרים
    "sales_by_region": SalesByRegionService,
    "user_activity_summary": UserActivitySummaryService,

    # שירות "חכם" וגנרי שמקבל פרמטרים
    "group_and_aggregate": GroupingService,
}


class PipelineManager:
    """
    מתזמר את תהליך הניתוח כולו:
    1. מקבל את בקשת המשתמש ואת ה-DAL.
    2. בונה את שאילתת הבסיס.
    3. שולף נתונים גולמיים במידת הצורך.
    4. מפעיל את שירותי הניתוח המבוקשים עם הפרמטרים שלהם.
    5. אוסף ומחזיר את התוצאות.
    """

    # =========== שינוי מס' 1: חתימת המתודה __init__ ===========
    # במקום לקבל requested_analyses: List[str], עכשיו מקבלים List[AnalysisRequest]
    def __init__(self, dal: AnalyticsDAL, collection: str, criteria: SearchCriteria,
                 requested_analyses: List[AnalysisRequest]):
        """
        אתחול המנהל עם כל התלויות והפרמטרים הנדרשים.
        """
        self.dal = dal
        self.collection = collection
        self.criteria = criteria
        self.requested_analyses = requested_analyses
        self.results: Dict[str, Any] = {}

    def _build_base_query(self) -> MongoQueryBuilder:
        """
        פונקציה זו נשארת זהה. היא בונה את חלק הסינון של השאילתה.
        """
        builder = self.dal.get_query_builder(self.collection)

        if self.criteria.filters:
            for f in self.criteria.filters:
                builder.add_filter(f.field, f.operator, f.value)

        if self.criteria.or_conditions:
            for or_condition_group in self.criteria.or_conditions:
                builder.add_or_condition(or_condition_group)

        if self.criteria.sort:
            for s in self.criteria.sort:
                builder.set_sort(s.field, s.direction)

        builder.set_skip(self.criteria.skip)
        builder.set_limit(self.criteria.limit)

        return builder

    # =========== שינוי מס' 2: לוגיקה מעודכנת ב-run_pipeline ===========
    async def run_pipeline(self) -> Dict[str, Any]:
        """
        המתודה הראשית שמריצה את כל הניתוחים המבוקשים ומחזירה את התוצאות.
        הלוגיקה מעודכנת כדי לטפל באובייקטים של AnalysisRequest.
        """
        services_to_run = []
        # הלולאה עוברת עכשיו על רשימת אובייקטים, לא רשימת מחרוזות
        for analysis_request in self.requested_analyses:
            # מתוך כל אובייקט, אנו שולפים את השם ואת הפרמטרים
            analysis_name = analysis_request.name
            analysis_params = analysis_request.params

            service_class = AVAILABLE_SERVICES.get(analysis_name)
            if not service_class:
                raise ValueError(f"שירות אנליטיקה בשם '{analysis_name}' לא נמצא.")

            # אנו שומרים את כל המידע הנדרש: שם, פרמטרים, והמופע של הקלאס
            services_to_run.append((analysis_name, analysis_params, service_class()))

        # החלק של בדיקת 'needs_raw_data' ושליפת הנתונים נשאר זהה
        needs_raw_data = any(s.FETCH_DATA_FIRST for _, _, s in services_to_run)
        raw_data = None
        query_builder = self._build_base_query()
        if needs_raw_data:
            raw_data = await query_builder.execute()

        # הלולאה שמפעילה את השירותים מעודכנת כדי להעביר את הפרמטרים
        for name, params, service in services_to_run:
            # הוספנו את המפתח 'params' למילון kwargs שמועבר לכל שירות
            if service.FETCH_DATA_FIRST:
                self.results[name] = await service.process(data=raw_data, params=params)
            else:
                self.results[name] = await service.process(
                    data=None,
                    base_filter=query_builder._filter,
                    query_builder=query_builder,
                    params=params
                )

        return self.results