# מדריך מתקדם: אגרגציות MongoDB + ניתוח Pandas

## איך לקבוע מתי להשתמש בכל כלי?

### כלל הזהב:
- **MongoDB Aggregation** → כשאתה רוצה לצמצם את כמות הנתונים לפני שליפה
- **Pandas** → כשאתה רוצה לנתח ולעבד נתונים שכבר נשלפו

---

## אגרגציות MongoDB מתקדמות

### 1. המבנה הסטנדרטי של פייפליין אגרגציה

```python
def build_aggregation_pipeline(match_conditions=None, 
                              group_by_field=None,
                              calculations=None,
                              sort_field=None,
                              limit_count=None):
    """בונה פייפליין אגרגציה סטנדרטי"""
    
    pipeline = []
    
    # שלב 1: סינון (תמיד ראשון!)
    if match_conditions:
        pipeline.append({"$match": match_conditions})
    
    # שלב 2: קיבוץ וחישוב
    if group_by_field and calculations:
        group_stage = {"_id": f"${group_by_field}"}
        group_stage.update(calculations)
        pipeline.append({"$group": group_stage})
    
    # שלב 3: מיון
    if sort_field:
        sort_direction = -1 if sort_field.startswith('-') else 1
        field_name = sort_field.lstrip('-')
        pipeline.append({"$sort": {field_name: sort_direction}})
    
    # שלב 4: הגבלה (תמיד אחרון!)
    if limit_count:
        pipeline.append({"$limit": limit_count})
    
    return pipeline

# דוגמה לשימוש:
pipeline = build_aggregation_pipeline(
    match_conditions={"active": True, "year": {"$gte": 2023}},
    group_by_field="course",
    calculations={
        "student_count": {"$sum": 1},
        "avg_gpa": {"$avg": "$gpa"},
        "max_gpa": {"$max": "$gpa"}
    },
    sort_field="-student_count",  # מיון יורד
    limit_count=10
)

results = dal.aggregate_data("students", pipeline)
```

### 2. אגרגציות מורכבות לתרחישי מבחן

#### תרחיש: ניתוח מכירות לפי חודש ואזור
```python
def sales_analysis_by_month_region(dal):
    """ניתוח מכירות מתקדם"""
    
    pipeline = [
        # שלב 1: סינון לשנה האחרונה
        {
            "$match": {
                "sale_date": {"$gte": "2023-01-01"},
                "status": "completed"
            }
        },
        
        # שלב 2: הוספת שדות מחושבים
        {
            "$addFields": {
                "year_month": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": {"$dateFromString": {"dateString": "$sale_date"}}
                    }
                },
                "quarter": {
                    "$concat": [
                        {"$toString": {"$year": {"$dateFromString": {"dateString": "$sale_date"}}}},
                        "-Q",
                        {"$toString": {
                            "$ceil": {
                                "$divide": [
                                    {"$month": {"$dateFromString": {"dateString": "$sale_date"}}},
                                    3
                                ]
                            }
                        }}
                    ]
                }
            }
        },
        
        # שלב 3: קיבוץ מרובה - לפי אזור וחודש
        {
            "$group": {
                "_id": {
                    "region": "$region",
                    "year_month": "$year_month",
                    "quarter": "$quarter"
                },
                "total_sales": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "avg_transaction": {"$avg": "$amount"},
                "unique_customers": {"$addToSet": "$customer_id"}
            }
        },
        
        # שלב 4: הוספת חישובים נוספים
        {
            "$addFields": {
                "customer_count": {"$size": "$unique_customers"}
            }
        },
        
        # שלב 5: מיון לפי אזור ואז לפי חודש
        {
            "$sort": {
                "_id.region": 1,
                "_id.year_month": 1
            }
        }
    ]
    
    results = dal.aggregate_data("sales", pipeline)
    
    # המרה ל-DataFrame לניתוח נוסף
    df = pd.DataFrame(results)
    
    if not df.empty:
        # פירוק השדה המקובץ
        df['region'] = df['_id'].apply(lambda x: x['region'])
        df['year_month'] = df['_id'].apply(lambda x: x['year_month'])
        df['quarter'] = df['_id'].apply(lambda x: x['quarter'])
        df = df.drop('_id', axis=1)
        
        print("📊 ניתוח מכירות לפי חודש ואזור:")
        print(df.head())
        
        # חישוב אחוזי צמיחה
        df = df.sort_values(['region', 'year_month'])
        df['growth_rate'] = df.groupby('region')['total_sales'].pct_change() * 100
        
        print("\n📈 אחוזי צמיחה לפי אזור:")
        growth_summary = df.groupby('region')['growth_rate'].agg(['mean', 'std']).round(2)
        print(growth_summary)
    
    return df

# שימוש:
sales_df = sales_analysis_by_month_region(dal)
```

#### תרחיש: ניתוח פעילות משתמשים עם סטטיסטיקות מתקדמות
```python
def user_activity_advanced_analysis(dal):
    """ניתוח פעילות משתמשים מתקדם"""
    
    pipeline = [
        # סינון לחודש האחרון
        {
            "$match": {
                "timestamp": {"$gte": "2024-01-01"},
                "action_type": {"$ne": "login"}  # לא כולל התחברויות
            }
        },
        
        # פירוק לפי תאריכים ושעות
        {
            "$addFields": {
                "date": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": {"$dateFromString": {"dateString": "$timestamp"}}
                    }
                },
                "hour": {
                    "$hour": {"$dateFromString": {"dateString": "$timestamp"}}
                },
                "day_of_week": {
                    "$dayOfWeek": {"$dateFromString": {"dateString": "$timestamp"}}
                }
            }
        },
        
        # קיבוץ לפי משתמש
        {
            "$group": {
                "_id": "$user_id",
                "total_actions": {"$sum": 1},
                "unique_dates": {"$addToSet": "$date"},
                "unique_action_types": {"$addToSet": "$action_type"},
                "peak_hour": {"$max": "$hour"},
                "first_action": {"$min": "$timestamp"},
                "last_action": {"$max": "$timestamp"},
                "weekend_actions": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$day_of_week", [1, 7]]},  # ראשון ושבת
                            1,
                            0
                        ]
                    }
                }
            }
        },
        
        # הוספת מטריקות מחושבות
        {
            "$addFields": {
                "active_days": {"$size": "$unique_dates"},
                "action_variety": {"$size": "$unique_action_types"},
                "weekend_ratio": {
                    "$divide": ["$weekend_actions", "$total_actions"]
                }
            }
        },
        
        # סיווג משתמשים לפי רמת פעילות
        {
            "$addFields": {
                "user_type": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$gte": ["$total_actions", 100]},
                                "then": "high_activity"
                            },
                            {
                                "case": {"$gte": ["$total_actions", 20]},
                                "then": "medium_activity"
                            }
                        ],
                        "default": "low_activity"
                    }
                }
            }
        },
        
        # מיון לפי כמות פעולות
        {"$sort": {"total_actions": -1}}
    ]
    
    results = dal.aggregate_data("user_activities", pipeline)
    df = pd.DataFrame(results)
    
    if not df.empty:
        df['user_id'] = df['_id']
        df = df.drop('_id', axis=1)
        
        print("👥 ניתוח פעילות משתמשים:")
        print(f"   סה\"כ משתמשים: {len(df)}")
        
        # התפלגות לפי סוג פעילות
        activity_dist = df['user_type'].value_counts()
        print(f"\n📊 התפלגות פעילות:")
        for activity_type, count in activity_dist.items():
            print(f"   {activity_type}: {count} משתמשים")
        
        # סטטיסטיקות מתקדמות
        print(f"\n📈 סטטיסטיקות:")
        print(f"   ממוצע פעולות למשתמש: {df['total_actions'].mean():.1f}")
        print(f"   ממוצע ימי פעילות: {df['active_days'].mean():.1f}")
        print(f"   אחוז פעילות בסופ\"ש: {df['weekend_ratio'].mean()*100:.1f}%")
        
        # משתמשים מובילים
        top_users = df.head(5)
        print(f"\n🏆 5 המשתמשים הפעילים ביותר:")
        for _, user in top_users.iterrows():
            print(f"   {user['user_id']}: {user['total_actions']} פעולות, {user['active_days']} ימים")
    
    return df

# שימוש:
activity_df = user_activity_advanced_analysis(dal)
```

### 3. פייפליינים מותאמים למבחן

#### פייפליין לחישוב TOP N
```python
def get_top_performers(dal, collection_name, 
                      metric_field, group_by_field=None,
                      top_n=10, filters=None):
    """פייפליין גנרי למציאת TOP N ביצועים"""
    
    pipeline = []
    
    # סינון אופציונלי
    if filters:
        pipeline.append({"$match": filters})
    
    if group_by_field:
        # עם קיבוץ
        pipeline.extend([
            {
                "$group": {
                    "_id": f"${group_by_field}",
                    "total_metric": {"$sum": f"${metric_field}"},
                    "avg_metric": {"$avg": f"${metric_field}"},
                    "count": {"$sum": 1},
                    "max_single": {"$max": f"${metric_field}"},
                    "min_single": {"$min": f"${metric_field}"}
                }
            },
            {"$sort": {"total_metric": -1}},
            {"$limit": top_n}
        ])
    else:
        # בלי קיבוץ - TOP records
        pipeline.extend([
            {"$sort": {metric_field: -1}},
            {"$limit": top_n}
        ])
    
    results = dal.aggregate_data(collection_name, pipeline)
    
    print(f"🏆 TOP {len(results)} ב-{metric_field}:")
    for i, item in enumerate(results, 1):
        if group_by_field:
            print(f"   {i}. {item['_id']}: {item['total_metric']:.2f}")
        else:
            key_field = 'name' if 'name' in item else list(item.keys())[0]
            print(f"   {i}. {item.get(key_field, 'N/A')}: {item[metric_field]}")
    
    return results

# דוגמאות שימוש:
# TOP סטודנטים לפי GPA
top_students = get_top_performers(dal, "students", "gpa", filters={"active": True})

# TOP קורסים לפי ממוצע ציונים
top_courses = get_top_performers(dal, "students", "gpa", group_by_field="course", top_n=5)

# TOP מכירות לפי אזור
top_regions = get_top_performers(dal, "sales", "amount", group_by_field="region")
```

#### פייפליין לזיהוי חריגות (Outliers)
```python
def detect_outliers_aggregation(dal, collection_name, numeric_field, group_by=None):
    """זיהוי חריגות באמצעות אגרגציה"""
    
    pipeline = [
        # חישוב סטטיסטיקות בסיסיות
        {
            "$group": {
                "_id": f"${group_by}" if group_by else None,
                "values": {"$push": f"${numeric_field}"},
                "mean": {"$avg": f"${numeric_field}"},
                "count": {"$sum": 1},
                "min": {"$min": f"${numeric_field}"},
                "max": {"$max": f"${numeric_field}"}
            }
        },
        
        # חישוב סטיית תקן (קירוב)
        {
            "$addFields": {
                "variance_prep": {
                    "$map": {
                        "input": "$values",
                        "as": "value",
                        "in": {
                            "$pow": [{"$subtract": ["$value", "$mean"]}, 2]
                        }
                    }
                }
            }
        },
        
        {
            "$addFields": {
                "variance": {"$avg": "$variance_prep"},
                "std_dev": {"$sqrt": {"$avg": "$variance_prep"}}
            }
        },
        
        # הגדרת גבולות לחריגות (mean ± 2*std)
        {
            "$addFields": {
                "lower_bound": {"$subtract": ["$mean", {"$multiply": [2, "$std_dev"]}]},
                "upper_bound": {"$add": ["$mean", {"$multiply": [2, "$std_dev"]}]},
                "outliers": {
                    "$filter": {
                        "input": "$values",
                        "as": "value",
                        "cond": {
                            "$or": [
                                {"$lt": ["$value", {"$subtract": ["$mean", {"$multiply": [2, "$std_dev"]}]}]},
                                {"$gt": ["$value", {"$add": ["$mean", {"$multiply": [2, "$std_dev"]}]}]}
                            ]
                        }
                    }
                }
            }
        },
        
        {
            "$addFields": {
                "outlier_count": {"$size": "$outliers"},
                "outlier_percentage": {
                    "$multiply": [
                        {"$divide": [{"$size": "$outliers"}, "$count"]},
                        100
                    ]
                }
            }
        }
    ]
    
    results = dal.aggregate_data(collection_name, pipeline)
    
    for result in results:
        group_name = result['_id'] if result['_id'] else "כל הנתונים"
        print(f"\n📊 חריגות ב-{numeric_field} עבור {group_name}:")
        print(f"   ממוצע: {result['mean']:.2f}")
        print(f"   סטיית תקן: {result['std_dev']:.2f}")
        print(f"   טווח נורמלי: {result['lower_bound']:.2f} - {result['upper_bound']:.2f}")
        print(f"   חריגות: {result['outlier_count']} מתוך {result['count']} ({result['outlier_percentage']:.1f}%)")
        if result['outliers']:
            print(f"   ערכי חריגות: {result['outliers']}")
    
    return results

# שימוש:
outliers = detect_outliers_aggregation(dal, "students", "gpa", group_by="course")
```

---

## שילוב חכם של MongoDB + Pandas

### 1. אסטרטגיית "Reduce then Analyze"
```python
def smart_data_analysis(dal, collection_name, analysis_type="summary"):
    """שילוב חכם: צמצום ב-MongoDB, ניתוח ב-Pandas"""
    
    if analysis_type == "summary":
        # שלב 1: צמצום עם MongoDB
        pipeline = [
            {"$match": {"active": True}},
            {"$group": {
                "_id": {
                    "course": "$course",
                    "year": "$year"
                },
                "student_count": {"$sum": 1},
                "avg_gpa": {"$avg": "$gpa"},
                "total_credits": {"$sum": "$credits"},
                "students": {"$push": {
                    "name": "$name",
                    "gpa": "$gpa",
                    "credits": "$credits"
                }}
            }}
        ]
        
        # קבלת נתונים מצומצמים
        mongo_results = dal.aggregate_data(collection_name, pipeline)
        
        # שלב 2: המרה ל-Pandas לניתוח מתקדם
        summary_data = []
        detailed_data = []
        
        for result in mongo_results:
            # נתוני סיכום
            summary_data.append({
                'course': result['_id']['course'],
                'year': result['_id']['year'],
                'student_count': result['student_count'],
                'avg_gpa': result['avg_gpa'],
                'total_credits': result['total_credits'],
                'credits_per_student': result['total_credits'] / result['student_count']
            })
            
            # נתונים מפורטים
            for student in result['students']:
                detailed_data.append({
                    'course': result['_id']['course'],
                    'year': result['_id']['year'],
                    'name': student['name'],
                    'gpa': student['gpa'],
                    'credits': student['credits']
                })
        
        summary_df = pd.DataFrame(summary_data)
        detailed_df = pd.DataFrame(detailed_data)
        
        # שלב 3: ניתוח מתקדם ב-Pandas
        print("📊 ניתוח מתקדם:")
        
        # מציאת הקורס הטוב ביותר בכל שנה
        best_by_year = summary_df.loc[summary_df.groupby('year')['avg_gpa'].idxmax()]
        print("\n🏆 הקורס הטוב ביותר בכל שנה:")
        print(best_by_year[['year', 'course', 'avg_gpa']])
        
        # קורלציה בין גודל הקורס לממוצע
        correlation = summary_df['student_count'].corr(summary_df['avg_gpa'])
        print(f"\n📈 קורלציה בין גודל קורס לממוצע: {correlation:.3f}")
        
        # התפלגות GPA
        gpa_distribution = detailed_df['gpa'].describe()
        print(f"\n📋 התפלגות GPA:")
        print(gpa_distribution)
        
        return summary_df, detailed_df
    
    elif analysis_type == "time_series":
        # ניתוח זמני - דוגמה למכירות
        pipeline = [
            {"$match": {"status": "completed"}},
            {"$addFields": {
                "date": {"$dateFromString": {"dateString": "$sale_date"}},
                "year_month": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": {"$dateFromString": {"dateString": "$sale_date"}}
                    }
                }
            }},
            {"$group": {
                "_id": "$year_month",
                "total_sales": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "avg_transaction": {"$avg": "$amount"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        mongo_results = dal.aggregate_data(collection_name, pipeline)
        df = pd.DataFrame(mongo_results)
        
        if not df.empty:
            df['month'] = df['_id']
            df['month'] = pd.to_datetime(df['month'])
            df = df.set_index('month').drop('_id', axis=1)
            
            # חישוב מגמות
            df['sales_trend'] = df['total_sales'].pct_change()
            df['sales_ma3'] = df['total_sales'].rolling(window=3).mean()
            
            # זיהוי עונתיות
            df['month_num'] = df.index.month
            seasonal = df.groupby('month_num')['total_sales'].mean()
            
            print("📈 ניתוח זמני:")
            print(f"   צמיחה ממוצעת: {df['sales_trend'].mean()*100:.1f}%")
            print(f"   חודש הכי חזק: {seasonal.idxmax()} (ממוצע: {seasonal.max():.0f})")
            print(f"   חודש הכי חלש: {seasonal.idxmin()} (ממוצע: {seasonal.min():.0f})")
        
        return df

# שימוש:
summary_df, detailed_df = smart_data_analysis(dal, "students", "summary")
time_series_df = smart_data_analysis(dal, "sales", "time_series")
```

### 2. טכניקת "Progressive Loading"
```python
def progressive_data_loading(dal, collection_name, 
                           initial_filters=None,
                           drill_down_fields=None):
    """טעינה הדרגתית - מקריע לפרטי"""
    
    print("🔍 שלב 1: סקירה כללית")
    
    # שלב 1: מידע כללי
    total_count = dal.count_documents(collection_name, initial_filters)
    sample = dal.find_one_document(collection_name, initial_filters or {})
    
    print(f"   סה\"כ רשומות: {total_count:,}")
    print(f"   שדות זמינים: {list(sample.keys()) if sample else 'N/A'}")
    
    # שלב 2: התפלגויות בסיסיות
    if drill_down_fields:
        print("\n📊 שלב 2: התפלגויות")
        
        distributions = {}
        for field in drill_down_fields:
            if sample and field in sample:
                unique_values = dal.get_distinct_values(collection_name, field)
                distributions[field] = unique_values
                print(f"   {field}: {len(unique_values)} ערכים ייחודיים")
                if len(unique_values) <= 10:
                    print(f"      ערכים: {unique_values}")
    
    # שלב 3: בחירה חכמה של נתונים לטעינה
    print("\n📦 שלב 3: בחירת נתונים לטעינה מפורטת")
    
    if total_count > 10000:
        print("   מערך נתונים גדול - בוחר דגימה מייצגת")
        
        # אגרגציה לדגימה מייצגת
        sampling_pipeline = [
            {"$match": initial_filters or {}},
            {"$sample": {"size": 5000}},  # דגימה אקראית
            {"$project": {"_id": 1}}  # רק מזהים
        ]
        
        sample_ids = [doc['_id'] for doc in dal.aggregate_data(collection_name, sampling_pipeline)]
        
        # טעינת הדגימה
        detailed_data = dal.find_documents(
            collection_name,
            {"_id": {"$in": sample_ids}}
        )
        
        print(f"   נטענה דגימה של {len(detailed_data)} רשומות")
        
    else:
        print("   מערך נתונים קטן - טוען הכל")
        detailed_data = dal.find_documents(collection_name, initial_filters)
    
    # שלב 4: המרה ל-DataFrame וניתוח ראשוני
    df = pd.DataFrame(detailed_data)
    
    if not df.empty:
        print(f"\n🐼 שלב 4: DataFrame מוכן עם {len(df)} שורות")
        
        # ניתוח אוטומטי של השדות
        numeric_fields = df.select_dtypes(include=['number']).columns.tolist()
        text_fields = df.select_dtypes(include=['object']).columns.tolist()
        
        print(f"   שדות מספריים: {numeric_fields}")
        print(f"   שדות טקסט: {text_fields}")
        
        # סטטיסטיקות מהירות לשדות מספריים
        if numeric_fields:
            print(f"\n📈 סטטיסטיקות מהירות:")
            for field in numeric_fields[:3]:  # רק 3 הראשונים
                mean_val = df[field].mean()
                median_val = df[field].median()
                std_val = df[field].std()
                print(f"   {field}: ממוצע={mean_val:.2f}, חציון={median_val:.2f}, סטיית תקן={std_val:.2f}")
    
    return df, distributions if drill_down_fields else {}

# שימוש:
df, distributions = progressive_data_loading(
    dal, 
    "students",
    initial_filters={"active": True},
    drill_down_fields=["course", "year", "status"]
)
```

### 3. מתכונים מוכנים לניתוח
```python
class MongoAnalysisRecipes:
    """מתכונים מוכנים לניתוחים נפוצים"""
    
    def __init__(self, dal):
        self.dal = dal
    
    def customer_segmentation(self, collection_name="customers"):
        """סיגמנטציה של לקוחות"""
        
        pipeline = [
            {"$group": {
                "_id": "$customer_id",
                "total_purchases": {"$sum": "$amount"},
                "purchase_count": {"$sum": 1},
                "avg_purchase": {"$avg": "$amount"},
                "first_purchase": {"$min": "$purchase_date"},
                "last_purchase": {"$max": "$purchase_date"}
            }},
            {"$addFields": {
                "days_since_last": {
                    "$divide": [
                        {"$subtract": [{"$dateFromString": {"dateString": "2024-01-01"}}, 
                                     {"$dateFromString": {"dateString": "$last_purchase"}}]},
                        86400000  # מילישניות ליום
                    ]
                }
            }}
        ]
        
        mongo_results = self.dal.aggregate_data(collection_name, pipeline)
        df = pd.DataFrame(mongo_results)
        
        if not df.empty:
            df['customer_id'] = df['_id']
            df = df.drop('_id', axis=1)
            
            # יצירת סיגמנטים
            df['value_segment'] = pd.qcut(df['total_purchases'], 
                                        q=3, 
                                        labels=['Low', 'Medium', 'High'])
            
            df['frequency_segment'] = pd.qcut(df['purchase_count'], 
                                            q=3, 
                                            labels=['Rare', 'Regular', 'Frequent'])
            
            df['recency_segment'] = pd.qcut(df['days_since_last'], 
                                          q=3, 
                                          labels=['Recent', 'Moderate', 'Old'])
            
            # יצירת סיגמנט משולב
            df['customer_segment'] = (df['value_segment'].astype(str) + '_' + 
                                    df['frequency_segment'].astype(str) + '_' + 
                                    df['recency_segment'].astype(str))
            
            # סיכום סיגמנטים
            segment_summary = df.groupby('customer_segment').agg({
                'customer_id': 'count',
                'total_purchases': 'mean',
                'purchase_count': 'mean'
            }).round(2)
            
            print("👥 סיגמנטציה של לקוחות:")
            print(segment_summary)
        
        return df
    
    def sales_cohort_analysis(self, collection_name="sales"):
        """ניתוח קוהורט של מכירות"""
        
        # MongoDB אגרגציה לקבלת נתוני בסיס
        pipeline = [
            {"$addFields": {
                "purchase_date": {"$dateFromString": {"dateString": "$purchase_date"}},
                "customer_id": "$customer_id"
            }},
            {"$group": {
                "_id": "$customer_id",
                "first_purchase": {"$min": "$purchase_date"},
                "purchases": {"$push": {
                    "date": "$purchase_date",
                    "amount": "$amount"
                }}
            }},
            {"$addFields": {
                "first_purchase_month": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$first_purchase"
                    }
                }
            }}
        ]
        
        mongo_results = self.dal.aggregate_data(collection_name, pipeline)
        
        # עיבוד ב-Pandas
        cohort_data = []
        
        for customer in mongo_results:
            first_month = customer['first_purchase_month']
            first_date = pd.to_datetime(customer['first_purchase'])
            
            for purchase in customer['purchases']:
                purchase_date = pd.to_datetime(purchase['date'])
                months_since = ((purchase_date.year - first_date.year) * 12 + 
                              purchase_date.month - first_date.month)
                
                cohort_data.append({
                    'customer_id': customer['_id'],
                    'cohort_month': first_month,
                    'period_number': months_since,
                    'amount': purchase['amount']
                })
        
        df = pd.DataFrame(cohort_data)
        
        if not df.empty:
            # יצירת טבלת קוהורט
            cohort_table = df.groupby(['cohort_month', 'period_number'])['customer_id'].nunique().reset_index()
            cohort_table = cohort_table.pivot(index='cohort_month', 
                                             columns='period_number', 
                                             values='customer_id')
            
            # חישוב שיעורי החזרה
            cohort_sizes = cohort_table.iloc[:, 0]
            retention_table = cohort_table.divide(cohort_sizes, axis=0)
            
            print("📈 ניתוח קוהורט - שיעורי החזרה:")
            print(retention_table.round(3))
        
        return df, cohort_table
    
    def product_recommendation_data(self, collection_name="order_items"):
        """הכנת נתונים להמלצות מוצרים"""
        
        # חיפוש מוצרים שנקנו יחד
        pipeline = [
            {"$group": {
                "_id": "$order_id",
                "products": {"$addToSet": "$product_id"}
            }},
            {"$match": {
                "products": {"$size": {"$gte": 2}}  # רק הזמנות עם 2+ מוצרים
            }},
            {"$unwind": "$products"},
            {"$group": {
                "_id": "$products",
                "co_purchased_with": {"$addToSet": "$_id"}
            }}
        ]
        
        # זה מורכב מדי ל-MongoDB, עדיף ב-Pandas
        # נקח את הנתונים הגולמיים
        raw_data = self.dal.find_documents(collection_name)
        df = pd.DataFrame(raw_data)
        
        if not df.empty:
            # יצירת מטריצת co-occurrence
            order_product = df.groupby('order_id')['product_id'].apply(list).reset_index()
            
            from itertools import combinations
            
            co_occurrence = {}
            for _, row in order_product.iterrows():
                products = row['product_id']
                if len(products) > 1:
                    for combo in combinations(products, 2):
                        key = tuple(sorted(combo))
                        co_occurrence[key] = co_occurrence.get(key, 0) + 1
            
            # המרה ל-DataFrame
            co_df = pd.DataFrame([
                {'product_a': k[0], 'product_b': k[1], 'frequency': v}
                for k, v in co_occurrence.items()
            ])
            
            # מיון לפי תכיפות
            co_df = co_df.sort_values('frequency', ascending=False)
            
            print("🛒 מוצרים הנקנים יחד (TOP 10):")
            print(co_df.head(10))
        
        return co_df

# שימוש:
recipes = MongoAnalysisRecipes(dal)

# סיגמנטציה
customer_segments = recipes.customer_segmentation("purchases")

# ניתוח קוהורט
cohort_df, cohort_table = recipes.sales_cohort_analysis("sales")

# המלצות מוצרים
recommendations = recipes.product_recommendation_data("order_items")
```

---

## סיכום: מתי להשתמש במה?

### 🎯 כלל החלטה מהיר:

| התרחיש | כלי מומלץ | סיבה |
|---------|-----------|-------|
| סכימת רשומות גדולה (>50K) | MongoDB Aggregation | צמצום נתונים לפני שליפה |
| חישובים פשטים (סכום, ממוצע) | MongoDB Aggregation | מהיר ויעיל |
| ניתוח סטטיסטי מורכב | Pandas | גמישות וכלים מתקדמים |
| קורלציות ורגרסיות | Pandas | מותאם לניתוח מתמטי |
| מאגר נתונים קטן (<10K) | Pandas | פשוט יותר |
| דוחות בזמן אמת | MongoDB Aggregation | מהירות |
| עיבוד נתונים חד-פעמי | Pandas | גמישות |

### 🔧 הקוד המינימלי למבחן:

```python
# 1. חיבור וטעינה מהירה
dal = AtlasDAL("connection_string", "db_name")
dal.connect()

# 2. בדיקה ראשונית
sample = dal.find_one_document("collection", {})
count = dal.count_documents("collection")
print(f"מבנה: {list(sample.keys())}, סה\"כ: {count}")

# 3. אגרגציה מהירה (אם צריך צמצום)
if count > 10000:
    pipeline = [
        {"$match": {"active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    summary = dal.aggregate_data("collection", pipeline)
    df = pd.DataFrame(summary)
else:
    # 4. טעינה ישירה (אם קטן)
    data = dal.find_documents("collection", {"active": True})
    df = pd.DataFrame(data)

# 5. ניתוח ב-Pandas
print(df.describe())
print(df.groupby('category').size())

dal.disconnect()
```

**זכור: תמיד תתחיל עם בדיקה ראשונית לפני שתחליט איך להמשיך!** 🎯