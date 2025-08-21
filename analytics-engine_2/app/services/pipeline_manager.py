from typing import List, Dict, Any, Optional
import logging
from app.services.analysis_services import get_service
from app.dal.query_builder import MongoQueryBuilder
import time

logger = logging.getLogger(__name__)


class PipelineManager:
    """מנהל הפייפליין - מפעיל שירותי ניתוח מרובים"""

    def __init__(self, use_aggregation: bool = False):
        """
        Args:
            use_aggregation: האם להשתמש באגרגציה של MongoDB (True) או בעיבוד Pandas (False)
        """
        self.use_aggregation = use_aggregation
        self.logger = logger

    def execute_analyses(
            self,
            raw_data: List[Dict[str, Any]],
            analysis_names: List[str],
            query_builder: Optional[MongoQueryBuilder] = None,
            base_query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        הפעלת רשימת ניתוחים על הנתונים

        Args:
            raw_data: הנתונים הגולמיים
            analysis_names: שמות הניתוחים להרצה
            query_builder: אובייקט QueryBuilder (נדרש עבור אגרגציה)
            base_query: השאילתה הבסיסית (לשימוש באגרגציה)

        Returns:
            מילון עם תוצאות כל הניתוחים
        """

        results = {}
        execution_times = {}

        for analysis_name in analysis_names:
            start_time = time.time()

            try:
                # קבלת השירות המתאים
                service = get_service(analysis_name)

                if not service:
                    self.logger.warning(f"Service not found: {analysis_name}")
                    results[analysis_name] = {
                        "error": f"Analysis service '{analysis_name}' not found"
                    }
                    continue

                # הפעלת השירות
                self.logger.info(f"Executing analysis: {analysis_name}")

                result = service.process(
                    data=raw_data,
                    use_aggregation=self.use_aggregation,
                    query_builder=query_builder,
                    base_query=base_query
                )

                results[analysis_name] = result
                execution_times[analysis_name] = round((time.time() - start_time) * 1000, 2)

                self.logger.info(
                    f"Analysis {analysis_name} completed in {execution_times[analysis_name]}ms"
                )

            except Exception as e:
                self.logger.error(f"Error in analysis {analysis_name}: {str(e)}")
                results[analysis_name] = {"error": str(e)}
                execution_times[analysis_name] = round((time.time() - start_time) * 1000, 2)

        return {
            "results": results,
            "execution_times_ms": execution_times,
            "total_execution_time_ms": round(sum(execution_times.values()), 2)
        }

    def validate_analyses(self, analysis_names: List[str]) -> tuple[List[str], List[str]]:
        """
        בדיקת תקינות רשימת הניתוחים

        Returns:
            tuple של (ניתוחים תקינים, ניתוחים לא תקינים)
        """
        valid = []
        invalid = []

        for name in analysis_names:
            if get_service(name):
                valid.append(name)
            else:
                invalid.append(name)

        return valid, invalid