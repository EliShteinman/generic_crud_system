# מדריך Query Builder Pattern ל-MongoDB

## מה זה Query Builder?

Query Builder הוא תבנית עיצוב (Design Pattern) שמאפשרת לבנות שאילתות מורכבות באופן הדרגתי וקריא. במקום לכתוב שאילתת MongoDB ארוכה ומסובכת, אתה בונה אותה שלב אחרי שלב.

## ההבדל בין גישות

### גישה רגילה (ללא Builder):
```python
# שאילתה מורכבת רגילה - קשה לקריאה
query = {
    "$and": [
        {"age": {"$gte": 18, "$lte": 65}},
        {"status": "active"},
        {"$or": [
            {"department": "engineering"},
            {"department": "marketing"}
        ]}
    ]
}

cursor = collection.find(query).sort("name", 1).limit(10).skip(20)
result = list(cursor)
```

### גישה עם Builder (מהפרויקטים שלך):
```python
# אותה שאילתה עם Builder - הרבה יותר קריא
builder = MongoQueryBuilder(collection)
result = (builder
    .add_filter("age", "gte", 18)
    .add_filter("age", "lte", 65)
    .add_filter("status", "eq", "active")
    .add_or_condition([
        {"department": "engineering"},
        {"department": "marketing"}
    ])
    .set_sort("name", 1)
    .set_limit(10)
    .set_skip(20)
    .execute())
```

---

## מימוש Query Builder פשוט

הנה מימוש פשוט שאתה יכול להשתמש בו במבחן:

### הקלאס הבסיסי:
```python
from pymongo import ASCENDING, DESCENDING
import re

class MongoQueryBuilder:
    def __init__(self, collection):
        self.collection = collection
        self._filter = {}
        self._sort = None
        self._limit = None
        self._skip = None
        self._projection = {}
    
    def add_filter(self, field, operator, value):
        """הוספת תנאי סינון"""
        
        if operator == "eq":
            self._filter[field] = value
        elif operator == "ne":
            self._filter[field] = {"$ne": value}
        elif operator == "gt":
            self._filter[field] = {"$gt": value}
        elif operator == "gte":
            self._filter[field] = {"$gte": value}
        elif operator == "lt":
            self._filter[field] = {"$lt": value}
        elif operator == "lte":
            self._filter[field] = {"$lte": value}
        elif operator == "in":
            self._filter[field] = {"$in": value}
        elif operator == "nin":
            self._filter[field] = {"$nin": value}
        elif operator == "regex":
            self._filter[field] = {"$regex": value, "$options": "i"}
        elif operator == "exists":
            self._filter[field] = {"$exists": value}
        elif operator == "size":
            self._filter[field] = {"$size": value}
        elif operator == "all":
            self._filter[field] = {"$all": value}
        
        return self  # חשוב! מחזיר את עצמו בשביל שרשור
    
    def add_or_condition(self, conditions):
        """הוספת תנאי OR"""
        if "$or" not in self._filter:
            self._filter["$or"] = []
        self._filter["$or"].extend(conditions)
        return self
    
    def add_elem_match(self, field, criteria):
        """עבור חיפוש במערכים של אובייקטים"""
        self._filter[field] = {"$elemMatch": criteria}
        return self
    
    def set_sort(self, field, direction=1):
        """הגדרת מיון"""
        if self._sort is None:
            self._sort = []
        self._sort.append((field, direction))
        return self
    
    def set_limit(self, count):
        """הגדרת מגבלה"""
        self._limit = count
        return self
    
    def set_skip(self, count):
        """דילוג על רשומות"""
        self._skip = count
        return self
    
    def set_projection(self, fields):
        """בחירת שדות מסוימים"""
        self._projection = fields
        return self
    
    def execute(self):
        """ביצוע השאילתה"""
        cursor = self.collection.find(self._filter, self._projection)
        
        if self._sort:
            cursor = cursor.sort(self._sort)
        if self._skip:
            cursor = cursor.skip(self._skip)
        if self._limit:
            cursor = cursor.limit(self._limit)
            
        return list(cursor)
    
    def execute_one(self):
        """ביצוע השאילתה למציאת רשומה אחת"""
        return self.collection.find_one(self._filter, self._projection)
    
    def count(self):
        """ספירת תוצאות בלבד"""
        return self.collection.count_documents(self._filter)
    
    def get_query(self):
        """קבלת השאילתה שנבנתה (לדיבוג)"""
        return {
            "filter": self._filter,
            "sort": self._sort,
            "limit": self._limit,
            "skip": self._skip,
            "projection": self._projection
        }
```

---

## דוגמאות שימוש למבחן

### דוגמה 1: חיפוש סטודנטים
```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['university']
collection = db['students']

# יצירת Builder
builder = MongoQueryBuilder(collection)

# חיפוש סטודנטים פעילים בגיל 20-25 מקורס מדעי המחשב
students = (builder
    .add_filter("active", "eq", True)
    .add_filter("age", "gte", 20)
    .add_filter("age", "lte", 25)
    .add_filter("course", "eq", "מדעי המחשב")
    .set_sort("name", ASCENDING)
    .set_limit(50)
    .execute())

print(f"נמצאו {len(students)} סטודנטים")
for student in students:
    print(f"{student['name']} - גיל {student['age']}")
```

### דוגמה 2: חיפוש מוצרים עם תנאי OR
```python
# מוצרים באלקטרוניקה או ספרים, עם מחיר מתחת ל-500
builder = MongoQueryBuilder(db.products)

products = (builder
    .add_or_condition([
        {"category": "אלקטרוניקה"},
        {"category": "ספרים"}
    ])
    .add_filter("price", "lt", 500)
    .add_filter("in_stock", "eq", True)
    .set_sort("price", ASCENDING)
    .execute())
```

### דוגמה 3: חיפוש עם ביטוי רגולרי
```python
# חיפוש משתמשים שהשם שלהם מתחיל ב"אבר"
users = (MongoQueryBuilder(db.users)
    .add_filter("name", "regex", "^אבר")
    .add_filter("active", "eq", True)
    .set_projection({"name": 1, "email": 1, "_id": 0})
    .execute())
```

### דוגמה 4: עבודה עם מערכים
```python
# סטודנטים שיש להם בדיוק 4 ציונים וכולם מעל 80
students_with_high_grades = (MongoQueryBuilder(db.students)
    .add_filter("grades", "size", 4)
    .add_filter("grades", "all", [80, 85, 90, 95])  # כל הציונים האלה
    .execute())

# הזמנות שמכילות מוצר ספציפי
orders_with_product = (MongoQueryBuilder(db.orders)
    .add_elem_match("items", {"product_id": "PROD123", "quantity": {"$gte": 2}})
    .execute())
```

---

## Builder מתקדם עם אגרגציה

לפעמים תצטרך לבצע חישובים מורכבים. הנה הרחבה של ה-Builder:

```python
class AdvancedMongoQueryBuilder(MongoQueryBuilder):
    def __init__(self, collection):
        super().__init__(collection)
        self._pipeline = []
    
    def add_match_stage(self):
        """הוספת שלב match לפייפליין"""
        if self._filter:
            self._pipeline.append({"$match": self._filter})
        return self
    
    def add_group_stage(self, group_by, aggregations):
        """הוספת שלב group"""
        group_stage = {"_id": f"${group_by}"}
        group_stage.update(aggregations)
        self._pipeline.append({"$group": group_stage})
        return self
    
    def add_sort_stage(self, field, direction=1):
        """הוספת שלב sort"""
        self._pipeline.append({"$sort": {field: direction}})
        return self
    
    def add_limit_stage(self, count):
        """הוספת שלב limit"""
        self._pipeline.append({"$limit": count})
        return self
    
    def add_project_stage(self, fields):
        """הוספת שלב project"""
        self._pipeline.append({"$project": fields})
        return self
    
    def add_unwind_stage(self, field):
        """פירוק מערך"""
        self._pipeline.append({"$unwind": f"${field}"})
        return self
    
    def execute_aggregation(self):
        """ביצוע אגרגציה"""
        return list(self.collection.aggregate(self._pipeline))
    
    def get_pipeline(self):
        """קבלת הפייפליין שנבנה"""
        return self._pipeline

# דוגמה לשימוש:
builder = AdvancedMongoQueryBuilder(db.sales)

# סטטיסטיקות מכירות לפי אזור
sales_stats = (builder
    .add_filter("status", "eq", "completed")
    .add_filter("date", "gte", "2024-01-01")
    .add_match_stage()
    .add_group_stage("region", {
        "total_sales": {"$sum": "$amount"},
        "count": {"$sum": 1},
        "avg_sale": {"$avg": "$amount"}
    })
    .add_sort_stage("total_sales", -1)
    .add_limit_stage(10)
    .execute_aggregation())
```

---

## מתי להשתמש בכל שיטה?

### Query Builder רגיל (find):
- כשאתה רוצה לקבל רשומות כפי שהן
- כשהסינון פשוט יחסית
- כשאתה צריך pagination (דיפדוף)

```python
# טוב ל:
students = (MongoQueryBuilder(db.students)
    .add_filter("course", "eq", "מתמטיקה")
    .add_filter("year", "in", [2, 3, 4])
    .set_sort("gpa", -1)
    .set_limit(20)
    .execute())
```

### Advanced Builder (aggregation):
- כשאתה צריך חישובים (סכומים, ממוצעים)
- כשאתה צריך לקבץ נתונים
- כשאתה עובד עם מערכים מורכבים

```python
# טוב ל:
grade_stats = (AdvancedMongoQueryBuilder(db.students)
    .add_filter("active", "eq", True)
    .add_match_stage()
    .add_unwind_stage("grades")
    .add_group_stage("course", {
        "avg_grade": {"$avg": "$grades"},
        "student_count": {"$sum": 1}
    })
    .execute_aggregation())
```

---

## טיפים למבחן

### 1. בנה את השאילתה שלב אחרי שלב
```python
# התחל פשוט
builder = MongoQueryBuilder(collection)
results = builder.add_filter("status", "eq", "active").execute()
print(f"נמצאו {len(results)} רשומות פעילות")

# הוסף עוד תנאים בהדרגה
results = (builder
    .add_filter("age", "gte", 18)
    .execute())
print(f"נמצאו {len(results)} רשומות פעילות מעל גיל 18")
```

### 2. השתמש בדיבוג
```python
builder = MongoQueryBuilder(collection)
builder.add_filter("name", "regex", "יוסי")
builder.add_filter("active", "eq", True)

# ראה מה השאילתה שנבנתה
print("השאילתה שנבנתה:")
print(builder.get_query())

# בצע
results = builder.execute()
```

### 3. שמור Builders שימושיים
```python
def get_active_students_builder(collection):
    """Builder למציאת סטודנטים פעילים"""
    return (MongoQueryBuilder(collection)
        .add_filter("active", "eq", True)
        .add_filter("enrollment_status", "eq", "enrolled"))

def get_recent_orders_builder(collection, days_back=30):
    """Builder להזמנות אחרונות"""
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    return (MongoQueryBuilder(collection)
        .add_filter("order_date", "gte", cutoff_date.isoformat())
        .add_filter("status", "ne", "cancelled"))

# שימוש במבחן:
# מצא סטודנטים פעילים בקורס מסוים
cs_students = (get_active_students_builder(db.students)
    .add_filter("course", "eq", "מדעי המחשב")
    .set_sort("gpa", -1)
    .execute())

# מצא הזמנות אחרונות מעל 100 שקל
recent_big_orders = (get_recent_orders_builder(db.orders, 7)
    .add_filter("total_amount", "gt", 100)
    .execute())
```

### 4. טפל בשגיאות
```python
def safe_query_execute(builder):
    """ביצוע שאילתה בטוח עם טיפול בשגיאות"""
    try:
        results = builder.execute()
        print(f"השאילתה הצליחה, נמצאו {len(results)} תוצאות")
        return results
    except Exception as e:
        print(f"שגיאה בביצוע השאילתה: {e}")
        print(f"השאילתה שנבנתה: {builder.get_query()}")
        return []

# שימוש:
builder = MongoQueryBuilder(db.students)
builder.add_filter("invalid_field", "eq", "some_value")
results = safe_query_execute(builder)
```

---

## לסיכום: יותבי Query Builder במבחן

### יתרונות:
1. **קריאות** - השאילתה ברורה ומובנת
2. **גמישות** - קל לשנות ולהתאים
3. **בניה הדרגתית** - אפשר לבנות שלב אחרי שלב
4. **דיבוג קל** - תמיד יכול לראות מה נבנה
5. **שימוש חוזר** - אפשר לשמור בנאי חלקיים

### מתי להשתמש במבחן:
- כשהשאילתה מורכבת (יותר מ-3 תנאים)
- כשאתה צריך לבנות שאילתות דינמיות
- כשאתה רוצה לבדוק התקדמות שלב אחרי שלב
- כשיש סיכוי שתצטרך לשנות את השאילתה

### המחלקה המינימלית שצריך לזכור:
```python
class SimpleBuilder:
    def __init__(self, collection):
        self.collection = collection
        self.query = {}
    
    def where(self, field, operator, value):
        if operator == "eq":
            self.query[field] = value
        elif operator == "gt":
            self.query[field] = {"$gt": value}
        # ... עוד אופרטורים
        return self
    
    def execute(self):
        return list(self.collection.find(self.query))

# שימוש במבחן:
results = (SimpleBuilder(collection)
    .where("age", "gt", 18)
    .where("status", "eq", "active")
    .execute())
```

זהו! עם המדריכים האלה אתה אמור להיות מוכן לכל תרחיש במבחן. ה-Query Builder יעזור לך לבנות שאילתות מורכבות בצורה מובנת וקלה לתחזוקה.

בהצלחה! 🚀