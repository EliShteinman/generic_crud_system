import pandas as pd
from typing import List, Dict, Any, Union
from ..abstract_service import AbstractAnalysisService


class GroupingService(AbstractAnalysisService):
    FETCH_DATA_FIRST = True

    async def process(self, data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        params = kwargs.get("params", {})

        # =========== שדרוג מס' 1: קבלת רשימת עמודות לקיבוץ ===========
        group_by_columns = params.get("group_by_columns")  # שם הפרמטר שונה לרבים

        # =========== שדרוג מס' 2: קבלת מילון אגרגציות ===========
        # המבנה צפוי להיות: {"revenue": ["sum", "mean"], "units_sold": ["sum"]}
        aggregations = params.get("aggregations")

        # ולידציה בסיסית של הקלט
        if not group_by_columns or not aggregations:
            raise ValueError("GroupingService requires 'group_by_columns' (list) and 'aggregations' (dict) in params.")

        if not isinstance(group_by_columns, list) or not isinstance(aggregations, dict):
            raise ValueError("'group_by_columns' must be a list and 'aggregations' must be a dictionary.")

        if not data:
            return {"summary": "No data for analysis."}

        df = pd.DataFrame(data)

        # טיפול בערכים חסרים (אפשר להרחיב גם אותו, כרגע נשאר פשוט)
        for col in aggregations.keys():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # =========== שדרוג מס' 3: הקיבוץ והאגרגציה המשודרגים ===========
        try:
            summary = df.groupby(group_by_columns).agg(aggregations).reset_index()

            # Pandas יוצר multi-level columns. נשטיח אותם לשמות יפים.
            # למשל, ('revenue', 'sum') -> 'revenue_sum'
            summary.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in
                               summary.columns.values]

        except KeyError as e:
            raise ValueError(f"One of the specified columns does not exist in the data: {e}")
        except Exception as e:
            raise RuntimeError(f"An error occurred during Pandas aggregation: {e}")

        return summary.to_dict(orient='records')