import pandas as pd
from typing import List, Dict, Any
from ..abstract_service import AbstractAnalysisService


class SalesByRegionService(AbstractAnalysisService):
    """
    גישה א': עיבוד מלא בצד האפליקציה עם Pandas.
    מקבל את הנתונים הגולמיים ומבצע אגרגציה בזיכרון.
    """
    FETCH_DATA_FIRST = True

    async def process(self, data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        if not data:
            return {"summary": "No data provided for analysis."}

        df = pd.DataFrame(data)

        # טיפול בערכים חסרים
        df['sales_amount'] = pd.to_numeric(df['sales_amount'], errors='coerce').fillna(0)
        df['units_sold'] = pd.to_numeric(df['units_sold'], errors='coerce').fillna(0)

        if 'region' not in df.columns:
            return {"error": "Field 'region' not found in data."}

        # ביצוע אגרגציה עם groupby
        summary = df.groupby('region').agg(
            total_sales=('sales_amount', 'sum'),
            average_sales=('sales_amount', 'mean'),
            total_units=('units_sold', 'sum'),
            transaction_count=('region', 'size')
        ).reset_index()

        return summary.to_dict(orient='records')