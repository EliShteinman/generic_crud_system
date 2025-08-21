from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
from ..base_service import AbstractAnalysisService


class UserActivitySummaryService(AbstractAnalysisService):
    """שירות ניתוח פעילות משתמשים"""

    def __init__(self):
        super().__init__("user_activity_summary")

    def analyze_with_pandas(self, data: pd.DataFrame) -> Dict[str, Any]:
        """ניתוח פעילות משתמשים באמצעות Pandas"""

        # בדיקה שהעמודות הנדרשות קיימות
        required_columns = ['user_id', 'action_type', 'timestamp']
        if not all(col in data.columns for col in required_columns):
            return {
                "error": f"Missing required columns. Required: {required_columns}",
                "available_columns": list(data.columns)
            }

        # המרת timestamp לתאריך
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['date'] = data['timestamp'].dt.date
        data['hour'] = data['timestamp'].dt.hour
        data['day_of_week'] = data['timestamp'].dt.day_name()

        # ניתוח כללי
        total_users = data['user_id'].nunique()
        total_actions = len(data)
        date_range = {
            'start': str(data['timestamp'].min()),
            'end': str(data['timestamp'].max())
        }

        # פעילות לפי סוג פעולה
        actions_by_type = data.groupby('action_type').agg({
            'user_id': ['count', 'nunique']
        })
        actions_by_type.columns = ['total_actions', 'unique_users']
        actions_by_type = actions_by_type.reset_index()
        actions_by_type['avg_per_user'] = (
                actions_by_type['total_actions'] / actions_by_type['unique_users']
        ).round(2)

        # משתמשים הכי פעילים
        top_users = data.groupby('user_id').agg({
            'action_type': 'count',
            'timestamp': ['min', 'max']
        })
        top_users.columns = ['total_actions', 'first_action', 'last_action']
        top_users = top_users.sort_values('total_actions', ascending=False).head(10)
        top_users_dict = top_users.to_dict('index')

        # המרת timestamps למחרוזות
        for user_id, user_data in top_users_dict.items():
            user_data['first_action'] = str(user_data['first_action'])
            user_data['last_action'] = str(user_data['last_action'])

        # פעילות לפי שעות
        hourly_activity = data.groupby('hour').size()
        hourly_dict = {int(hour): int(count) for hour, count in hourly_activity.items()}

        # השעות הפעילות ביותר
        peak_hours = hourly_activity.nlargest(3)
        peak_hours_list = [
            {"hour": int(hour), "actions": int(count)}
            for hour, count in peak_hours.items()
        ]

        # פעילות לפי יום בשבוע
        weekly_activity = data.groupby('day_of_week').size()
        weekly_dict = weekly_activity.to_dict()

        # פעילות לפי ימים
        daily_activity = data.groupby('date').agg({
            'user_id': ['nunique', 'count'],
            'action_type': lambda x: x.value_counts().to_dict()
        })
        daily_activity.columns = ['unique_users', 'total_actions', 'actions_breakdown']

        # סטטיסטיקות יומיות
        daily_stats = {
            'average_daily_users': round(daily_activity['unique_users'].mean(), 2),
            'average_daily_actions': round(daily_activity['total_actions'].mean(), 2),
            'max_daily_users': int(daily_activity['unique_users'].max()),
            'max_daily_actions': int(daily_activity['total_actions'].max()),
            'min_daily_users': int(daily_activity['unique_users'].min()),
            'min_daily_actions': int(daily_activity['total_actions'].min()),
            'peak_day': {
                'date': str(daily_activity['total_actions'].idxmax()),
                'actions': int(daily_activity['total_actions'].max()),
                'users': int(daily_activity.loc[daily_activity['total_actions'].idxmax(), 'unique_users'])
            }
        }

        # מגמות (Trends) - השוואה בין המחצית הראשונה והשנייה
        if len(daily_activity) > 1:
            mid_point = len(daily_activity) // 2
            first_half = daily_activity.iloc[:mid_point]
            second_half = daily_activity.iloc[mid_point:]

            trends = {
                'first_half_avg_users': round(first_half['unique_users'].mean(), 2),
                'second_half_avg_users': round(second_half['unique_users'].mean(), 2),
                'first_half_avg_actions': round(first_half['total_actions'].mean(), 2),
                'second_half_avg_actions': round(second_half['total_actions'].mean(), 2),
                'user_trend': 'increasing' if second_half['unique_users'].mean() > first_half[
                    'unique_users'].mean() else 'decreasing',
                'action_trend': 'increasing' if second_half['total_actions'].mean() > first_half[
                    'total_actions'].mean() else 'decreasing'
            }
        else:
            trends = None

        return {
            "summary": {
                "total_users": total_users,
                "total_actions": total_actions,
                "average_actions_per_user": round(total_actions / total_users, 2) if total_users > 0 else 0,
                "unique_action_types": data['action_type'].nunique(),
                "date_range": date_range
            },
            "actions_by_type": actions_by_type.to_dict('records'),
            "top_10_users": top_users_dict,
            "hourly_distribution": hourly_dict,
            "peak_hours": peak_hours_list,
            "weekly_distribution": weekly_dict,
            "daily_statistics": daily_stats,
            "trends": trends
        }

    def build_aggregation_pipeline(self, base_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """בניית פייפליין אגרגציה ל-MongoDB"""

        pipeline = []

        # הוספת שלב match אם יש תנאי סינון
        if base_query:
            pipeline.append({"$match": base_query})

        # שלב ראשון - קיבוץ מרובה עם facets
        pipeline.append({
            "$facet": {
                # סטטיסטיקות כלליות
                "summary": [
                    {
                        "$group": {
                            "_id": None,
                            "total_actions": {"$sum": 1},
                            "unique_users": {"$addToSet": "$user_id"},
                            "unique_action_types": {"$addToSet": "$action_type"},
                            "min_timestamp": {"$min": "$timestamp"},
                            "max_timestamp": {"$max": "$timestamp"}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "total_actions": 1,
                            "total_users": {"$size": "$unique_users"},
                            "total_action_types": {"$size": "$unique_action_types"},
                            "date_range": {
                                "start": "$min_timestamp",
                                "end": "$max_timestamp"
                            }
                        }
                    }
                ],

                # פעילות לפי סוג
                "by_action_type": [
                    {
                        "$group": {
                            "_id": "$action_type",
                            "total_actions": {"$sum": 1},
                            "unique_users": {"$addToSet": "$user_id"}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "action_type": "$_id",
                            "total_actions": 1,
                            "unique_users_count": {"$size": "$unique_users"}
                        }
                    },
                    {"$sort": {"total_actions": -1}}
                ],

                # משתמשים פעילים
                "top_users": [
                    {
                        "$group": {
                            "_id": "$user_id",
                            "action_count": {"$sum": 1},
                            "first_action": {"$min": "$timestamp"},
                            "last_action": {"$max": "$timestamp"},
                            "action_types": {"$addToSet": "$action_type"}
                        }
                    },
                    {"$sort": {"action_count": -1}},
                    {"$limit": 10},
                    {
                        "$project": {
                            "_id": 0,
                            "user_id": "$_id",
                            "action_count": 1,
                            "first_action": 1,
                            "last_action": 1,
                            "unique_action_types": {"$size": "$action_types"}
                        }
                    }
                ],

                # פעילות לפי שעה
                "hourly_activity": [
                    {
                        "$project": {
                            "hour": {"$hour": "$timestamp"}
                        }
                    },
                    {
                        "$group": {
                            "_id": "$hour",
                            "count": {"$sum": 1}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "hour": "$_id",
                            "count": 1
                        }
                    },
                    {"$sort": {"hour": 1}}
                ],

                # פעילות לפי יום בשבוע
                "weekly_activity": [
                    {
                        "$project": {
                            "dayOfWeek": {"$dayOfWeek": "$timestamp"}
                        }
                    },
                    {
                        "$group": {
                            "_id": "$dayOfWeek",
                            "count": {"$sum": 1}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "day": {
                                "$switch": {
                                    "branches": [
                                        {"case": {"$eq": ["$_id", 1]}, "then": "Sunday"},
                                        {"case": {"$eq": ["$_id", 2]}, "then": "Monday"},
                                        {"case": {"$eq": ["$_id", 3]}, "then": "Tuesday"},
                                        {"case": {"$eq": ["$_id", 4]}, "then": "Wednesday"},
                                        {"case": {"$eq": ["$_id", 5]}, "then": "Thursday"},
                                        {"case": {"$eq": ["$_id", 6]}, "then": "Friday"},
                                        {"case": {"$eq": ["$_id", 7]}, "then": "Saturday"}
                                    ],
                                    "default": "Unknown"
                                }
                            },
                            "count": 1
                        }
                    }
                ],

                # פעילות יומית
                "daily_activity": [
                    {
                        "$project": {
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$timestamp"
                                }
                            },
                            "user_id": 1,
                            "action_type": 1
                        }
                    },
                    {
                        "$group": {
                            "_id": "$date",
                            "unique_users": {"$addToSet": "$user_id"},
                            "total_actions": {"$sum": 1}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "date": "$_id",
                            "unique_users_count": {"$size": "$unique_users"},
                            "total_actions": 1
                        }
                    },
                    {"$sort": {"date": 1}}
                ]
            }
        })

        return pipeline

    def post_process_aggregation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """עיבוד נוסף של תוצאות האגרגציה"""

        if df.empty:
            return {"message": "No data found", "result": []}

        # הנתונים מגיעים כ-facet, נעבד אותם
        result = df.iloc[0] if not df.empty else {}

        # עיבוד התוצאות מכל facet
        summary = result.get('summary', [{}])[0] if 'summary' in result else {}

        # חישוב ממוצע פעולות למשתמש
        if summary and summary.get('total_users', 0) > 0:
            summary['average_actions_per_user'] = round(
                summary['total_actions'] / summary['total_users'], 2
            )

        # עיבוד פעילות לפי סוג
        actions_by_type = result.get('by_action_type', [])
        for action in actions_by_type:
            if action.get('unique_users_count', 0) > 0:
                action['avg_per_user'] = round(
                    action['total_actions'] / action['unique_users_count'], 2
                )

        # עיבוד משתמשים מובילים
        top_users = {
            user['user_id']: {
                'action_count': user['action_count'],
                'first_action': str(user['first_action']),
                'last_action': str(user['last_action']),
                'unique_action_types': user.get('unique_action_types', 0)
            }
            for user in result.get('top_users', [])
        }

        # עיבוד פעילות שעתית
        hourly_distribution = {
            item['hour']: item['count']
            for item in result.get('hourly_activity', [])
        }

        # מציאת שעות שיא
        hourly_sorted = sorted(
            result.get('hourly_activity', []),
            key=lambda x: x['count'],
            reverse=True
        )[:3]
        peak_hours = [
            {"hour": item['hour'], "actions": item['count']}
            for item in hourly_sorted
        ]

        # עיבוד פעילות שבועית
        weekly_distribution = {
            item['day']: item['count']
            for item in result.get('weekly_activity', [])
        }

        # עיבוד פעילות יומית
        daily_data = result.get('daily_activity', [])
        if daily_data:
            daily_df = pd.DataFrame(daily_data)
            daily_stats = {
                'average_daily_users': round(daily_df['unique_users_count'].mean(), 2),
                'average_daily_actions': round(daily_df['total_actions'].mean(), 2),
                'max_daily_users': int(daily_df['unique_users_count'].max()),
                'max_daily_actions': int(daily_df['total_actions'].max()),
                'min_daily_users': int(daily_df['unique_users_count'].min()),
                'min_daily_actions': int(daily_df['total_actions'].min())
            }

            # מציאת היום השיא
            peak_day_idx = daily_df['total_actions'].idxmax()
            if pd.notna(peak_day_idx):
                peak_day = daily_df.loc[peak_day_idx]
                daily_stats['peak_day'] = {
                    'date': peak_day['date'],
                    'actions': int(peak_day['total_actions']),
                    'users': int(peak_day['unique_users_count'])
                }
        else:
            daily_stats = {}

        return {
            "summary": summary,
            "actions_by_type": actions_by_type,
            "top_10_users": top_users,
            "hourly_distribution": hourly_distribution,
            "peak_hours": peak_hours,
            "weekly_distribution": weekly_distribution,
            "daily_statistics": daily_stats
        }