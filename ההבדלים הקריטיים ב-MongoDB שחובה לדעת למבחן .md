# ההבדלים הקריטיים ב-MongoDB שחובה לדעת למבחן

## 1. מתי להשתמש בכל פונקציה?

### השאלה הראשונה: כמה תוצאות אני רוצה?

| מה אתה רוצה | פונקציה | דוגמה |
|-------------|---------|--------|
| **רשומה אחת בלבד** | `find_one()` | `collection.find_one({"email": "user@example.com"})` |
| **מספר רשומות** | `find()` | `collection.find({"age": {"$gte": 18}})` |
| **רק לספור** | `count_documents()` | `collection.count_documents({"active": True})` |
| **לחשב/לקבץ** | `aggregate()` | `collection.aggregate([{"$group": {...}}])` |

### דוגמאות ברורות:

```python
# רשומה אחת - למציאת משתמש ספציפי
user = collection.find_one({"username": "admin"})
if user:
    print(f"המשתמש קיים: {user['name']}")

# מספר רשומות - למציאת כל הסטודנטים בקורס
students = list(collection.find({"course": "מתמטיקה"}))
print(f"נמצאו {len(students)} סטודנטים")

# ספירה - רק למספר, לא צריך את הנתונים
count = collection.count_documents({"grade": {"$gte": 90}})
print(f"יש {count} סטודנטים עם ציון מעל 90")

# חישוב - לממוצע ציונים לפי קורס
pipeline = [
    {"$group": {
        "_id": "$course",
        "avg_grade": {"$avg": "$grade"}
    }}
]
results = list(collection.aggregate(pipeline))
```

---

## 2. ההבדל בין find() ל-aggregate()

### find() - למציאת רשומות כפי שהן
```python
# מה שנכנס = מה שיוצא (בתוספת סינון/מיון)
students = collection.find(
    {"course": "פיזיקה"},      # סינון
    {"name": 1, "grade": 1}    # איזה שדות
).sort("grade", -1).limit(10)

# התוצאה: רשימה של מסמכי סטודנטים
```

### aggregate() - לחישובים ושינוי מבנה
```python
# כאן אתה משנה את המבנה ומחשב
pipeline = [
    {"$match": {"course": "פיזיקה"}},      # סינון
    {"$group": {                           # קיבוץ וחישוב
        "_id": "$teacher",
        "student_count": {"$sum": 1},
        "avg_grade": {"$avg": "$grade"}
    }},
    {"$sort": {"avg_grade": -1}}
]

# התוצאה: מבנה חדש לגמרי עם סטטיסטיקות
```

### מתי להשתמש בכל אחת?

| צריך | השתמש ב |
|------|--------|
| רשימת סטודנטים | `find()` |
| ממוצע ציונים לפי קורס | `aggregate()` |
| 10 הסטודנטים הטובים | `find().sort().limit()` |
| כמה סטודנטים בכל קורס | `aggregate()` |
| פרטי סטודנט ספציפי | `find_one()` |

---

## 3. שגיאות נפוצות שהורגות במבחן

### שגיאה #1: שכחת list() באגרגציה
```python
# 🚫 לא יעבוד - תקבל cursor object
result = collection.aggregate(pipeline)
print(result)  # <pymongo.command_cursor.CommandCursor object>

# ✅ נכון
result = list(collection.aggregate(pipeline))
print(result)  # הנתונים האמיתיים
```

### שגיאה #2: בלבול בין $ ל-"
```python
# 🚫 שגוי
{"$group": {"_id": "course", "count": {"$sum": 1}}}

# ✅ נכון - עם $ לפני שם השדה
{"$group": {"_id": "$course", "count": {"$sum": 1}}}
```

### שגיאה #3: בלבול בסדר באגרגציה
```python
# 🚫 סדר שגוי - לא יעבוד כמו שצריך
pipeline = [
    {"$limit": 10},        # קודם מגביל
    {"$match": {"active": True}}  # אחר כך מסנן
]

# ✅ סדר נכון
pipeline = [
    {"$match": {"active": True}},  # ראשון - סנן
    {"$limit": 10}                 # אחרון - הגבל
]
```

---

## 4. המדריך המהיר לאגרגציה

### הסדר הנכון תמיד:
1. `$match` - סינון (ראשון!)
2. `$unwind` - פירוק מערכים  
3. `$group` - קיבוץ וחישוב
4. `$sort` - מיון
5. `$limit` / `$skip` - הגבלה (אחרון!)

### דוגמה מושלמת:
```python
# חישוב ממוצע ציונים לפי קורס (רק סטודנטים פעילים)
pipeline = [
    # 1. סנן ראשון
    {"$match": {"active": True}},
    
    # 2. פרק מערך ציונים (אם יש)
    {"$unwind": "$grades"},
    
    # 3. קבץ וחשב
    {"$group": {
        "_id": "$course",
        "avg_grade": {"$avg": "$grades"},
        "student_count": {"$sum": 1}
    }},
    
    # 4. מיין
    {"$sort": {"avg_grade": -1}},
    
    # 5. הגבל אחרון
    {"$limit": 5}
]

results = list(collection.aggregate(pipeline))
```

---

## 5. התבניות החשובות למבחן

### תבנית 1: חיפוש פשוט עם תנאים
```python
def find_with_conditions(collection, **conditions):
    """תבנית לחיפוש עם תנאים משתנים"""
    query = {}
    
    for field, value in conditions.items():
        if isinstance(value, dict):
            query[field] = value
        else:
            query[field] = value
    
    return list(collection.find(query))

# שימוש:
students = find_with_conditions(
    db.students,
    course="מתמטיקה",
    age={"$gte": 20},
    active=True
)
```

### תבנית 2: אגרגציה לסטטיסטיקות
```python
def get_stats_by_field(collection, group_field, value_field=None):
    """חישוב סטטיסטיקות לפי שדה מסוים"""
    
    if value_field:
        # עם חישובים מספריים
        group_stage = {
            "_id": f"${group_field}",
            "count": {"$sum": 1},
            "total": {"$sum": f"${value_field}"},
            "average": {"$avg": f"${value_field}"},
            "min": {"$min": f"${value_field}"},
            "max": {"$max": f"${value_field}"}
        }
    else:
        # רק ספירה
        group_stage = {
            "_id": f"${group_field}",
            "count": {"$sum": 1}
        }
    
    pipeline = [
        {"$group": group_stage},
        {"$sort": {"count": -1}}
    ]
    
    return list(collection.aggregate(pipeline))

# שימוש:
# ספירה לפי קורס
course_counts = get_stats_by_field(db.students, "course")

# סטטיסטיקות ציונים לפי קורס  
grade_stats = get_stats_by_field(db.students, "course", "grade")
```

### תבנית 3: חיפוש עם מיון ודיפדוף
```python
def paginated_search(collection, query={}, sort_field="name", 
                     sort_direction=1, page=1, per_page=10):
    """חיפוש עם דיפדוף"""
    
    skip = (page - 1) * per_page
    
    cursor = (collection
              .find(query)
              .sort(sort_field, sort_direction)
              .skip(skip)
              .limit(per_page))
    
    results = list(cursor)
    total = collection.count_documents(query)
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

# שימוש:
page_data = paginated_search(
    db.students,
    query={"course": "מדעי המחשב"},
    sort_field="grade",
    sort_direction=-1,  # יורד
    page=2,
    per_page=20
)
```

---

## 6. מה באמת חשוב לזכור למבחן?

### הרשימה המינימלית:

1. **find_one()** - רשומה אחת
2. **find()** - מספר רשומות  
3. **aggregate()** - חישובים
4. **תמיד list() עם aggregate**
5. **$ לפני שמות שדות באגרגציה**
6. **הסדר באגרגציה: match → group → sort → limit**

### השאלות שתמיד כדאי לשאול:

1. **כמה תוצאות אני צריך?** (אחת = find_one, כמה = find)
2. **אני צריך לחשב משהו?** (כן = aggregate, לא = find)
3. **איך הנתונים נראים?** (תמיד תבדוק find_one קודם)
4. **האם אני זוכר את הסדר הנכון?** (match ראשון, limit אחרון)

### קוד המינימום למבחן:
```python
from pymongo import MongoClient

# חיבור
client = MongoClient('mongodb://localhost:27017/')
db = client['database_name']
collection = db['collection_name']

# חיפוש בסיסי
results = collection.find({"field": "value"})

# ספירה
count = collection.count_documents({"field": "value"})

# אגרגציה בסיסית
pipeline = [
    {"$match": {"field": "value"}},
    {"$group": {"_id": "$group_field", "count": {"$sum": 1}}}
]
stats = list(collection.aggregate(pipeline))

# הדפסת דוגמה לבדיקה
sample = collection.find_one()
print(sample)
```

---

## 7. דף הצ'יט שיט למבחן

| רוצה | פקודה | דוגמה |
|------|-------|--------|
| רשומה אחת | `find_one({})` | `user = col.find_one({"id": 123})` |
| כל הרשומות | `find({})` | `users = list(col.find({}))` |
| עם תנאי | `find({"field": "value"})` | `active = list(col.find({"active": True}))` |
| ספירה | `count_documents({})` | `count = col.count_documents({"active": True})` |
| ממוצע | `aggregate([{$group: {_id: null, avg: {$avg: "$field"}}}])` | `pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$grade"}}}]` |
| קיבוץ | `aggregate([{$group: {_id: "$field", count: {$sum: 1}}}])` | `pipeline = [{"$group": {"_id": "$course", "count": {"$sum": 1}}}]` |
| מיון | `find({}).sort("field", 1)` | `sorted_users = col.find({}).sort("name", 1)` |
| הגבלה | `find({}).limit(10)` | `first_10 = col.find({}).limit(10)` |

**זכור: תמיד `list()` עם `aggregate()` ו-`find()`!**

---

## 8. הבדיקה האחרונה לפני המבחן

נסה את הקוד הזה ותוודא שאתה מבין מה קורה:

```python
# 1. בדיקה בסיסית
sample = collection.find_one()
print("מבנה הנתונים:", sample)

# 2. ספירה פשוטה  
total = collection.count_documents({})
print("סה\"כ רשומות:", total)

# 3. חיפוש עם תנאי
results = list(collection.find({"active": True}).limit(3))
print("3 רשומות פעילות:", len(results))

# 4. אגרגציה פשוטה
pipeline = [
    {"$group": {"_id": "$status", "count": {"$sum": 1}}}
]
stats = list(collection.aggregate(pipeline))
print("סטטיסטיקות:", stats)
```

אם הכל עובד - אתה מוכן למבחן! 🚀

**זכור: במבחן, תמיד תתחיל עם `find_one()` כדי לראות איך הנתונים נראים!**