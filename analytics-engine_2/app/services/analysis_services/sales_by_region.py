from typing import Dict, Any, List
import pandas as pd
from ..base_service import AbstractAnalysisService


class SalesByRegionService(AbstractAnalysisService):
    """שירות ניתוח מכירות לפי אזור"""

    def __init__(self):
        super().__init__("sales_by_region")

    def analyze_with_pandas(self, data: pd.DataFrame) -> Dict[str, Any]:
        """ניתוח מכירות לפי אזור באמצעות Pandas"""

        # בדיקה שהעמודות הנדרשות קיימות
        required_columns = ['region', 'sales_amount']
        if not all(col in data.columns for col in required_columns):
            return {
                "error": f"Missing required columns. Required: {required_columns}",
                "available_columns": list(data.columns)
            }

        # ניתוח בסיסי
        analysis = data.groupby('region').agg({
            'sales_amount': ['sum', 'mean', 'count', 'min', 'max']
        }).round(2)

        # שיטוח העמודות
        analysis.columns = ['_'.join(col).strip() for col in analysis.columns.values]
        analysis = analysis.reset_index()

        # חישובים נוספים
        total_sales = data['sales_amount'].sum()

        # הוספת אחוזים
        analysis['percentage_of_total'] = (
            (analysis['sales_amount_sum'] / total_sales * 100).round(2)
        )

        # מיון לפי סכום מכירות
        analysis = analysis.sort_values('sales_amount_sum', ascending=False)

        return {
            "summary": {
                "total_sales": round(total_sales, 2),
                "total_regions": len(analysis),
                "average_per_region": round(total_sales / len(analysis), 2) if len(analysis) > 0 else 0
            },
            "by_region": analysis.to_dict('records'),
            "top_region": analysis.iloc[0].to_dict() if not analysis.empty else None,
            "bottom_region": analysis.iloc[-1].to_dict() if not analysis.empty else None
        }

    def build_aggregation_pipeline(self, base_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """בניית פייפליין אגרגציה ל-MongoDB"""

        pipeline = []

        # הוספת שלב match אם יש תנאי סינון
        if base_query:
            pipeline.append({"$match": base_query})

        # שלב הקיבוץ
        pipeline.append({
            "$group": {
                "_id": "$region",
                "total_sales": {"$sum": "$sales_amount"},
                "average_sales": {"$avg": "$sales_amount"},
                "count": {"$sum": 1},
                "min_sale": {"$min": "$sales_amount"},
                "max_sale": {"$max": "$sales_amount"}
            }
        })

        # חישוב האחוז מהסך הכולל
        pipeline.append({
            "$group": {
                "_id": None,
                "regions": {
                    "$push": {
                        "region": "$_id",
                        "total_sales": "$total_sales",
                        "average_sales": "$average_sales",
                        "count": "$count",
                        "min_sale": "$min_sale",
                        "max_sale": "$max_sale"
                    }
                },
                "grand_total": {"$sum": "$total_sales"}
            }
        })

        # פירוק והוספת אחוזים
        pipeline.append({
            "$unwind": "$regions"
        })

        pipeline.append({
            "$project": {
                "_id": 0,
                "region": "$regions.region",
                "total_sales": {"$round": ["$regions.total_sales", 2]},
                "average_sales": {"$round": ["$regions.average_sales", 2]},
                "count": "$regions.count",
                "min_sale": "$regions.min_sale",
                "max_sale": "$regions.max_sale",
                "percentage_of_total": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$regions.total_sales", "$grand_total"]},
                            100
                        ]},
                        2
                    ]
                }
            }
        })

        # מיון לפי סכום מכירות
        pipeline.append({
            "$sort": {"total_sales": -1}
        })

        return pipeline

    def post_process_aggregation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """עיבוד נוסף של תוצאות האגרגציה"""

        if df.empty:
            return {"message": "No data found", "result": []}

        # חישוב סיכומים
        total_sales = df['total_sales'].sum()

        return {
            "summary": {
                "total_sales": round(total_sales, 2),
                "total_regions": len(df),
                "average_per_region": round(total_sales / len(df), 2) if len(df) > 0 else 0
            },
            "by_region": df.to_dict('records'),
            "top_region": df.iloc[0].to_dict() if not df.empty else None,
            "bottom_region": df.iloc[-1].to_dict() if not df.empty else None
        }