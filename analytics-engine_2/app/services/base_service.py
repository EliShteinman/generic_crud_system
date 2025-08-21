from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AbstractAnalysisService(ABC):
    """מחלקת בסיס אבסטרקטית לשירותי ניתוח"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def analyze_with_pandas(self, data: pd.DataFrame) -> Dict[str, Any]:
        """ניתוח הנתונים באמצעות Pandas (גישה א')"""
        pass

    @abstractmethod
    def build_aggregation_pipeline(self, base_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """בניית פייפליין אגרגציה ל-MongoDB (גישה ב')"""
        pass

    def process(self, data: List[Dict[str, Any]], use_aggregation: bool = False,
                query_builder=None, base_query: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        עיבוד הנתונים - בחירה בין גישה א' (Pandas) או גישה ב' (MongoDB Aggregation)
        """
        try:
            if use_aggregation and query_builder:
                # גישה ב': שימוש ב-MongoDB Aggregation
                self.logger.info(f"Using MongoDB aggregation for {self.name}")
                pipeline = self.build_aggregation_pipeline(base_query or {})
                aggregated_data = query_builder.execute_aggregation_pipeline(pipeline)

                # עיבוד קל של התוצאות עם Pandas אם נדרש
                if aggregated_data:
                    df = pd.DataFrame(aggregated_data)
                    return self.post_process_aggregation(df)
                else:
                    return {"message": "No data found", "result": []}

            else:
                # גישה א': עיבוד מלא עם Pandas
                self.logger.info(f"Using Pandas processing for {self.name}")
                if not data:
                    return {"message": "No data to analyze", "result": []}

                df = pd.DataFrame(data)
                return self.analyze_with_pandas(df)

        except Exception as e:
            self.logger.error(f"Error in {self.name}: {str(e)}")
            return {"error": str(e)}

    def post_process_aggregation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """עיבוד נוסף של תוצאות האגרגציה (ניתן לדרוס במחלקות היורשות)"""
        return df.to_dict('records')