# מדריך מלא: עבודה עם MongoDB בפייתון

## תוכן עניינים
1. [הקדמה ומושגי יסוד](#הקדמה-ומושגי-יסוד)
2. [התקנה וחיבור](#התקנה-וחיבור)
3. [מבנה נתונים ב-MongoDB](#מבנה-נתונים-ב-mongodb)
4. [שאילתות בסיסיות - מציאת רשומות](#שאילתות-בסיסיות---מציאת-רשומות)
5. [הוספת נתונים](#הוספת-נתונים)
6. [עדכון נתונים](#עדכון-נתונים)
7. [מחיקת נתונים](#מחיקת-נתונים)
8. [שאילתות מתקדמות](#שאילתות-מתקדמות)
9. [אגרגציה (Aggregation)](#אגרגציה-aggregation)
10. [דוגמאות למבחן](#דוגמאות-למבחן)

---

## הקדמה ומושגי יסוד

### מה זה MongoDB?
MongoDB הוא מסד נתונים NoSQL שמאחסן נתונים במבנה של **מסמכים** (documents) דמויי JSON.

### מושגים בסיסיים:
- **Database** - מסד נתונים (כמו schema ב-SQL)
- **Collection** - אוסף (כמו table ב-SQL)
- **Document** - מסמך (כמו row ב-SQL)
- **Field** - שדה (כמו column ב-SQL)

### מבנה היירכי:
```
Database
├── Collection 1
│   ├── Document 1
│   ├── Document 2
│   └── Document 3
└── Collection 2
    ├── Document 1
    └── Document 2
```

---

## התקנה וחיבור

### התקנת PyMongo
```bash
pip install pymongo
pip install motor  # לעבודה אסינכרונית
```

### חיבור בסיסי (סינכרוני)
```python
from pymongo import MongoClient

# חיבור מקומי
client = MongoClient('mongodb://localhost:27017/')

# חיבור ל-MongoDB Atlas (ענן)
client = MongoClient('mongodb+srv://username:password@cluster.mongodb.net/')

# בחירת מסד נתונים
db = client['school_db']

# בחירת אוסף
collection = db['students']
```

### חיבור אסינכרוני
```python
from motor.motor_asyncio import AsyncIOMotorClient

async def connect_to_db():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client['school_db']
    collection = db['students']
    return collection
```

### בדיקת חיבור
```python
# בדיקה פשוטה
try:
    client.admin.command('ping')
    print("החיבור למסד הנתונים הצליח!")
except Exception as e:
    print(f"שגיאה בחיבור: {e}")
```

---

## מבנה נתונים ב-MongoDB

### מסמך (Document) - דוגמה
```python
student = {
    "_id": "student_001",  # מזהה ייחודי (אופציונלי)
    "name": "יוסי כהן",
    "age": 22,
    "grades": [85, 92, 78],
    "address": {
        "city": "תל אביב",
        "street": "רחוב הרצל 10"
    },
    "active": True,
    "enrollment_date": "2023-09-01"
}
```

### סוגי נתונים נפוצים
```python
document = {
    "text_field": "טקסט",              # מחרוזת
    "number_field": 42,                # מספר שלם
    "float_field": 3.14,              # מספר עשרוני
    "boolean_field": True,             # בוליאני
    "array_field": [1, 2, 3],         # מערך
    "object_field": {"key": "value"}, # אובייקט מקונן
    "null_field": None                # ערך ריק
}
```

---

## שאילתות בסיסיות - מציאת רשומות

### 1. מציאת רשומה אחת

#### שאילתה הפשוטה ביותר
```python
# מציאת הרשומה הראשונה באוסף
first_student = collection.find_one()
print(first_student)
```

#### מציאה לפי מזהה
```python
# מציאה לפי _id
student = collection.find_one({"_id": "student_001"})
```

#### מציאה לפי שדה יחיד
```python
# מציאת הסטודנט הראשון בשם "יוסי כהן"
student = collection.find_one({"name": "יוסי כהן"})

# מציאת הסטודנט הראשון בגיל 22
student = collection.find_one({"age": 22})
```

### 2. מציאת מספר רשומות

#### מציאת כל הרשומות
```python
# מציאת כל הסטודנטים
all_students = collection.find()

# המרה לרשימה
students_list = list(all_students)

# הדפסה
for student in students_list:
    print(student)
```

#### מציאה עם תנאי
```python
# כל הסטודנטים בגיל 22
students_22 = collection.find({"age": 22})

# כל הסטודנטים הפעילים
active_students = collection.find({"active": True})
```

#### הגבלת מספר התוצאות
```python
# רק 5 סטודנטים ראשונים
limited_students = collection.find().limit(5)

# דילוג על 10 ראשונים ולקיחת 5 הבאים
skip_students = collection.find().skip(10).limit(5)
```

### 3. מיון תוצאות

```python
from pymongo import ASCENDING, DESCENDING

# מיון לפי גיל (עולה)
sorted_by_age = collection.find().sort("age", ASCENDING)

# מיון לפי שם (יורד)
sorted_by_name = collection.find().sort("name", DESCENDING)

# מיון מרובה: תחילה לפי גיל, אחר כך לפי שם
multi_sort = collection.find().sort([
    ("age", ASCENDING),
    ("name", ASCENDING)
])
```

### 4. בחירת שדות ספציפיים (Projection)

```python
# רק שם וגיל
name_age_only = collection.find({}, {"name": 1, "age": 1})

# הכל חוץ מכתובת
without_address = collection.find({}, {"address": 0})

# הסתרת _id
without_id = collection.find({}, {"_id": 0, "name": 1, "age": 1})
```

---

## הוספת נתונים

### 1. הוספת מסמך יחיד

```python
# יצירת מסמך חדש
new_student = {
    "name": "מרים לוי",
    "age": 21,
    "grades": [88, 95, 82],
    "active": True
}

# הוספה למסד
result = collection.insert_one(new_student)

# קבלת המזהה שנוצר
print(f"נוצר מסמך עם מזהה: {result.inserted_id}")
```

### 2. הוספת מספר מסמכים

```python
# רשימת סטודנטים
students_list = [
    {"name": "דוד שמש", "age": 23, "active": True},
    {"name": "רחל כהן", "age": 20, "active": False},
    {"name": "אבי גרין", "age": 24, "active": True}
]

# הוספה חבצית
result = collection.insert_many(students_list)

# קבלת כל המזהים
print(f"נוצרו {len(result.inserted_ids)} מסמכים")
print(f"מזהים: {result.inserted_ids}")
```

### 3. הוספה עם מזהה מותאם

```python
# מסמך עם מזהה מותאם אישית
custom_student = {
    "_id": "STUDENT_999",
    "name": "שרה דוד",
    "age": 19,
    "active": True
}

collection.insert_one(custom_student)
```

---

## עדכון נתונים

### 1. עדכון מסמך יחיד

```python
# עדכון פשוט - שינוי גיל
collection.update_one(
    {"name": "יוסי כהן"},                    # תנאי החיפוש
    {"$set": {"age": 23}}                    # השינוי
)

# עדכון מספר שדות
collection.update_one(
    {"name": "מרים לוי"},
    {"$set": {
        "age": 22,
        "active": False,
        "graduation_year": 2024
    }}
)
```

### 2. עדכון מספר מסמכים

```python
# עדכון כל הסטודנטים הלא פעילים
result = collection.update_many(
    {"active": False},                       # תנאי
    {"$set": {"status": "graduated"}}        # שינוי
)

print(f"עודכנו {result.modified_count} מסמכים")
```

### 3. אופרטורי עדכון שונים

```python
# הוספת ערך למספר ($inc)
collection.update_one(
    {"name": "יוסי כהן"},
    {"$inc": {"age": 1}}  # הוספת 1 לגיל
)

# הוספת פריט למערך ($push)
collection.update_one(
    {"name": "מרים לוי"},
    {"$push": {"grades": 90}}  # הוספת ציון למערך
)

# הסרת פריט מהמערך ($pull)
collection.update_one(
    {"name": "מרים לוי"},
    {"$pull": {"grades": 82}}  # הסרת ציון 82
)

# הגדרת ערך מינימלי ($min) או מקסימלי ($max)
collection.update_one(
    {"name": "דוד שמש"},
    {"$max": {"best_grade": 95}}  # עדכון רק אם 95 גדול מהערך הנוכחי
)
```

### 4. Upsert - עדכון או יצירה

```python
# אם לא קיים - יוצר חדש, אם קיים - מעדכן
collection.update_one(
    {"name": "תלמיד חדש"},
    {"$set": {"age": 20, "active": True}},
    upsert=True  # זה הפרמטר החשוב
)
```

---

## מחיקת נתונים

### 1. מחיקת מסמך יחיד

```python
# מחיקה לפי שם
result = collection.delete_one({"name": "מרים לוי"})

print(f"נמחקו {result.deleted_count} מסמכים")
```

### 2. מחיקת מספר מסמכים

```python
# מחיקת כל הסטודנטים הלא פעילים
result = collection.delete_many({"active": False})

print(f"נמחקו {result.deleted_count} מסמכים")
```

### 3. מחיקת כל המסמכים באוסף

```python
# מחיקת הכל (זהירות!)
result = collection.delete_many({})

print(f"נמחקו כל {result.deleted_count} המסמכים")
```

---

## שאילתות מתקדמות

### 1. אופרטורי השוואה

```python
# גדול מ- ($gt)
older_than_21 = collection.find({"age": {"$gt": 21}})

# קטן מ- ($lt)
younger_than_25 = collection.find({"age": {"$lt": 25}})

# בטווח ($gte ו-$lte)
age_range = collection.find({
    "age": {
        "$gte": 20,  # גדול או שווה ל-20
        "$lte": 25   # קטן או שווה ל-25
    }
})

# לא שווה ($ne)
not_22 = collection.find({"age": {"$ne": 22}})
```

### 2. אופרטורים על מערכים

```python
# קיים ברשימה ($in)
specific_ages = collection.find({"age": {"$in": [20, 21, 22]}})

# לא קיים ברשימה ($nin)
not_these_ages = collection.find({"age": {"$nin": [23, 24, 25]}})

# מערך מכיל ערך
has_grade_90 = collection.find({"grades": 90})

# מערך מכיל כל הערכים ($all)
has_all_grades = collection.find({"grades": {"$all": [85, 90]}})

# גודל מערך ($size)
three_grades = collection.find({"grades": {"$size": 3}})
```

### 3. חיפוש בשדות מקוננים

```python
# חיפוש בשדה מקונן
tel_aviv_students = collection.find({"address.city": "תל אביב"})

# חיפוש עם נקודות
main_street = collection.find({"address.street": {"$regex": "ראשי"}})
```

### 4. אופרטורים לוגיים

```python
# AND (ברירת מחדל)
young_active = collection.find({
    "age": {"$lt": 25},
    "active": True
})

# OR מפורש ($or)
young_or_old = collection.find({
    "$or": [
        {"age": {"$lt": 20}},
        {"age": {"$gt": 30}}
    ]
})

# NOT ($not)
not_young = collection.find({
    "age": {"$not": {"$lt": 21}}
})

# NOR - לא זה ולא זה ($nor)
neither_young_nor_active = collection.find({
    "$nor": [
        {"age": {"$lt": 21}},
        {"active": True}
    ]
})
```

### 5. ביטויים רגולריים

```python
# מתחיל במילה מסוימת
starts_with_david = collection.find({"name": {"$regex": "^דוד"}})

# מכיל מילה
contains_cohen = collection.find({"name": {"$regex": "כהן"}})

# לא תלוי ברישיות
case_insensitive = collection.find({
    "name": {"$regex": "יוסי", "$options": "i"}
})
```

### 6. בדיקת קיום שדות

```python
# יש שדה grades
has_grades = collection.find({"grades": {"$exists": True}})

# אין שדה graduation_year
no_graduation = collection.find({"graduation_year": {"$exists": False}})

# שדה לא ריק
not_null_name = collection.find({"name": {"$ne": None}})
```

---

## אגרגציה (Aggregation)

האגרגציה היא הכלי החזק ביותר ב-MongoDB לביצוע חישובים מורכבים.

### 1. מבנה בסיסי של פייפליין אגרגציה

```python
pipeline = [
    {"$match": {...}},      # סינון
    {"$group": {...}},      # קיבוץ
    {"$sort": {...}},       # מיון
    {"$limit": 10}          # הגבלה
]

result = collection.aggregate(pipeline)
```

### 2. דוגמאות בסיסיות

#### ספירת מסמכים לפי קטגוריה
```python
# ספירת סטודנטים לפי סטטוס
pipeline = [
    {"$group": {
        "_id": "$active",           # קיבוץ לפי שדה active
        "count": {"$sum": 1}        # ספירה
    }}
]

result = list(collection.aggregate(pipeline))
# תוצאה: [{"_id": True, "count": 15}, {"_id": False, "count": 5}]
```

#### חישוב ממוצע
```python
# ממוצע גילאים
pipeline = [
    {"$group": {
        "_id": None,                    # קיבוץ של הכל יחד
        "average_age": {"$avg": "$age"}
    }}
]

result = list(collection.aggregate(pipeline))
```

#### מציאת מינימום ומקסימום
```python
# הגיל הצעיר והמבוגר ביותר
pipeline = [
    {"$group": {
        "_id": None,
        "min_age": {"$min": "$age"},
        "max_age": {"$max": "$age"},
        "total_students": {"$sum": 1}
    }}
]
```

### 3. דוגמאות מתקדמות

#### קיבוץ מורכב עם מספר חישובים
```python
# סטטיסטיקות לפי עיר
pipeline = [
    {"$match": {"active": True}},           # רק סטודנטים פעילים
    {"$group": {
        "_id": "$address.city",             # קיבוץ לפי עיר
        "student_count": {"$sum": 1},
        "avg_age": {"$avg": "$age"},
        "oldest": {"$max": "$age"},
        "youngest": {"$min": "$age"}
    }},
    {"$sort": {"student_count": -1}},       # מיון לפי כמות סטודנטים
    {"$limit": 5}                          # רק 5 ערים הגדולות
]

result = list(collection.aggregate(pipeline))
```

#### עבודה עם מערכים
```python
# פירוק מערך הציונים וחישוב ממוצע
pipeline = [
    {"$unwind": "$grades"},                 # פירוק מערך לרשומות נפרדות
    {"$group": {
        "_id": "$name",                     # קיבוץ לפי שם סטודנט
        "average_grade": {"$avg": "$grades"},
        "total_grades": {"$sum": 1}
    }},
    {"$match": {"average_grade": {"$gte": 85}}}  # רק ממוצע מעל 85
]
```

#### הוספת שדות מחושבים
```python
# הוספת שדה "דרגת גיל"
pipeline = [
    {"$addFields": {
        "age_category": {
            "$switch": {
                "branches": [
                    {"case": {"$lt": ["$age", 20]}, "then": "צעיר"},
                    {"case": {"$lt": ["$age", 25]}, "then": "בינוני"},
                    {"case": {"$gte": ["$age", 25]}, "then": "מבוגר"}
                ],
                "default": "לא ידוע"
            }
        }
    }},
    {"$group": {
        "_id": "$age_category",
        "count": {"$sum": 1}
    }}
]
```

### 4. אופרטורי אגרגציה חשובים

```python
# אופרטורי חישוב
{"$sum": "$field"}          # סכום
{"$avg": "$field"}          # ממוצע
{"$min": "$field"}          # מינימום
{"$max": "$field"}          # מקסימום
{"$count": {}}              # ספירה

# אופרטורי מערך
{"$push": "$field"}         # אוסף כל הערכים למערך
{"$addToSet": "$field"}     # אוסף ערכים ייחודיים
{"$first": "$field"}        # הערך הראשון
{"$last": "$field"}         # הערך האחרון

# אופרטורי תאריך
{"$year": "$date_field"}    # שנה
{"$month": "$date_field"}   # חודש
{"$dayOfWeek": "$date_field"} # יום בשבוע
```

---

## דוגמאות למבחן

### תרחיש 1: מערכת ניהול סטודנטים

```python
# הכנת נתונים לדוגמה
students = [
    {
        "student_id": "12345",
        "name": "יוסי כהן", 
        "age": 22,
        "course": "מדעי המחשב",
        "year": 3,
        "grades": [85, 92, 78, 88],
        "active": True,
        "address": {"city": "תל אביב", "zip": "12345"}
    },
    {
        "student_id": "12346",
        "name": "מרים לוי",
        "age": 21,
        "course": "פיזיקה", 
        "year": 2,
        "grades": [95, 87, 91],
        "active": True,
        "address": {"city": "חיפה", "zip": "54321"}
    }
    # ... עוד סטודנטים
]

collection.insert_many(students)
```

#### שאלות נפוצות למבחן:

**1. מצא את כל הסטודנטים בשנה השלישית:**
```python
third_year = collection.find({"year": 3})
```

**2. מצא סטודנטים עם ממוצע מעל 85:**
```python
# עם אגרגציה
pipeline = [
    {"$addFields": {"avg_grade": {"$avg": "$grades"}}},
    {"$match": {"avg_grade": {"$gt": 85}}}
]
high_achievers = list(collection.aggregate(pipeline))
```

**3. ספור כמה סטודנטים יש בכל קורס:**
```python
pipeline = [
    {"$group": {
        "_id": "$course",
        "student_count": {"$sum": 1}
    }},
    {"$sort": {"student_count": -1}}
]
course_stats = list(collection.aggregate(pipeline))
```

**4. מצא את הציון הגבוה ביותר של כל סטודנט:**
```python
pipeline = [
    {"$addFields": {"highest_grade": {"$max": "$grades"}}},
    {"$project": {"name": 1, "highest_grade": 1}}
]
```

### תרחיש 2: מערכת ניהול מוצרים

```python
# מוצרים לדוגמה
products = [
    {
        "product_id": "P001",
        "name": "מחשב נייד",
        "category": "אלקטרוניקה",
        "price": 3500,
        "stock": 15,
        "supplier": "טכנולוגיה בע\"מ",
        "tags": ["מחשב", "נייד", "עבודה"]
    },
    {
        "product_id": "P002", 
        "name": "עכבר",
        "category": "אלקטרוניקה",
        "price": 45,
        "stock": 100,
        "supplier": "אביזרים בע\"מ",
        "tags": ["עכבר", "משחקים", "משרד"]
    }
]

products_collection = db['products']
products_collection.insert_many(products)
```

#### שאלות נפוצות:

**1. מצא מוצרים במחיר בין 100-1000 שקל:**
```python
price_range = products_collection.find({
    "price": {"$gte": 100, "$lte": 1000}
})
```

**2. חשב ערך מלאי כולל לפי קטגוריה:**
```python
pipeline = [
    {"$group": {
        "_id": "$category",
        "total_value": {"$sum": {"$multiply": ["$price", "$stock"]}},
        "total_items": {"$sum": "$stock"}
    }}
]
inventory_value = list(products_collection.aggregate(pipeline))
```

**3. מצא מוצרים חסרים במלאי (פחות מ-10):**
```python
low_stock = products_collection.find({"stock": {"$lt": 10}})
```

### תרחיש 3: מערכת הזמנות

```python
# הזמנות לדוגמה
orders = [
    {
        "order_id": "ORD001",
        "customer_id": "CUST123",
        "items": [
            {"product_id": "P001", "quantity": 2, "price": 3500},
            {"product_id": "P002", "quantity": 1, "price": 45}
        ],
        "total_amount": 7045,
        "order_date": "2024-01-15",
        "status": "completed"
    }
]

orders_collection = db['orders']
orders_collection.insert_many(orders)
```

**חישוב סה"כ מכירות לפי חודש:**
```python
from datetime import datetime

pipeline = [
    {"$addFields": {
        "order_month": {
            "$dateToString": {
                "format": "%Y-%m",
                "date": {"$dateFromString": {"dateString": "$order_date"}}
            }
        }
    }},
    {"$group": {
        "_id": "$order_month",
        "total_sales": {"$sum": "$total_amount"},
        "order_count": {"$sum": 1}
    }},
    {"$sort": {"_id": 1}}
]

monthly_sales = list(orders_collection.aggregate(pipeline))
```

### כלים למבחן מהיר

#### 1. בדיקת מבנה הנתונים
```python
# ראה דוגמה של מסמך
sample = collection.find_one()
print(sample)

# ראה את כל השדות שקיימים
pipeline = [
    {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
    {"$unwind": "$arrayofkeyvalue"},
    {"$group": {"_id": None, "allkeys": {"$addToSet": "$arrayofkeyvalue.k"}}}
]
all_fields = list(collection.aggregate(pipeline))
```

#### 2. ספירה מהירה
```python
# כמה מסמכים יש
total_count = collection.count_documents({})

# ספירה עם תנאי
active_count = collection.count_documents({"active": True})
```

#### 3. בדיקת ערכים ייחודיים
```python
# כל הערכים הייחודיים בשדה מסוים
unique_values = collection.distinct("category")
print(unique_values)
```

#### 4. תבנית לאגרגציה מהירה
```python
def quick_aggregation(group_field, value_field=None, operation="count"):
    """תבנית לאגרגציה מהירה"""
    
    if operation == "count":
        group_stage = {
            "_id": f"${group_field}",
            "count": {"$sum": 1}
        }
    elif operation == "sum":
        group_stage = {
            "_id": f"${group_field}", 
            "total": {"$sum": f"${value_field}"}
        }
    elif operation == "avg":
        group_stage = {
            "_id": f"${group_field}",
            "average": {"$avg": f"${value_field}"}
        }
    
    pipeline = [
        {"$group": group_stage},
        {"$sort": {"_id": 1}}
    ]
    
    return list(collection.aggregate(pipeline))

# שימוש:
# ספירה לפי קטגוריה
count_by_category = quick_aggregation("category")

# סכום מכירות לפי חודש
sales_by_month = quick_aggregation("month", "total_amount", "sum")

# ממוצע ציונים לפי קורס
avg_by_course = quick_aggregation("course", "grade", "avg")
```

---

## סיכום: ההבדלים החשובים שצריך לדעת למבחן

### 1. מתי להשתמש בכל שיטה?

#### find_one() - למציאת רשומה אחת
```python
# כשאתה יודע שיש רק תוצאה אחת או שאתה רוצה רק את הראשונה
user = collection.find_one({"email": "user@example.com"})
if user:
    print(f"נמצא משתמש: {user['name']}")
```

#### find() - למציאת מספר רשומות
```python
# כשאתה רוצה כמה תוצאות או כולן
users = collection.find({"age": {"$gte": 18}})
for user in users:
    print(user['name'])
```

#### aggregate() - לחישובים מורכבים
```python
# כשאתה צריך לחשב, לקבץ, או לבצע פעולות מתקדמות
pipeline = [
    {"$group": {"_id": "$department", "avg_salary": {"$avg": "$salary"}}}
]
results = collection.aggregate(pipeline)
```

### 2. שגיאות נפוצות שחשוב להימנע מהן

#### שגיאה: שכחת list() באגרגציה
```python
# לא נכון - לא יעבוד
result = collection.aggregate(pipeline)
print(result)  # יראה <pymongo.command_cursor.CommandCursor>

# נכון
result = list(collection.aggregate(pipeline))
print(result)  # יראה את הנתונים
```

#### שגיאה: בלבול בין $ ל-"
```python
# לא נכון
{"$group": {"_id": "category", "count": {"$sum": 1}}}

# נכון
{"$group": {"_id": "$category", "count": {"$sum": 1}}}
```

#### שגיאה: שכחת את התנאי ב-find
```python
# זה ימצא הכל (יכול להיות מסוכן!)
all_users = collection.find()

# טוב יותר להיות מפורש
active_users = collection.find({"active": True})
```

### 3. תבניות מהירות למבחן

#### תבנית לחיפוש בסיסי
```python
def search_documents(collection, filters=None, fields=None, sort_by=None, limit=None):
    """תבנית גנרית לחיפוש"""
    query = filters or {}
    projection = fields or {}
    
    cursor = collection.find(query, projection)
    
    if sort_by:
        cursor = cursor.sort(sort_by)
    if limit:
        cursor = cursor.limit(limit)
        
    return list(cursor)

# דוגמה לשימוש:
students = search_documents(
    collection=db.students,
    filters={"course": "מדעי המחשב", "active": True},
    fields={"name": 1, "age": 1, "_id": 0},
    sort_by=[("age", 1)],
    limit=10
)
```

#### תבנית לעדכון בטוח
```python
def safe_update(collection, filter_dict, update_dict, upsert=False):
    """תבנית לעדכון בטוח עם דיווח"""
    try:
        result = collection.update_one(
            filter_dict,
            {"$set": update_dict},
            upsert=upsert
        )
        
        if result.matched_count > 0:
            print(f"עודכן {result.modified_count} מסמכים")
        elif upsert and result.upserted_id:
            print(f"נוצר מסמך חדש עם מזהה: {result.upserted_id}")
        else:
            print("לא נמצא מסמך תואם")
            
        return result
        
    except Exception as e:
        print(f"שגיאה בעדכון: {e}")
        return None

# שימוש:
safe_update(
    db.students,
    {"student_id": "12345"},
    {"grade": 95, "last_updated": "2024-01-15"}
)
```

#### תבנית לסטטיסטיקות מהירות
```python
def get_basic_stats(collection, field_name):
    """קבלת סטטיסטיקות בסיסיות על שדה מספרי"""
    pipeline = [
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "min": {"$min": f"${field_name}"},
            "max": {"$max": f"${field_name}"},
            "avg": {"$avg": f"${field_name}"},
            "sum": {"$sum": f"${field_name}"}
        }}
    ]
    
    result = list(collection.aggregate(pipeline))
    return result[0] if result else None

# שימוש:
age_stats = get_basic_stats(db.students, "age")
print(f"ממוצע גילאים: {age_stats['avg']:.1f}")
```

### 4. טיפים אחרונים למבחן

#### בדוק תמיד את הנתונים קודם
```python
# ראה דוגמה של המבנה
sample = collection.find_one()
pprint(sample)  # או print(json.dumps(sample, indent=2))

# בדוק כמה רשומות יש
count = collection.count_documents({})
print(f"סה\"כ רשומות: {count}")
```

#### השתמש ב-explain() לדיבוג
```python
# בדוק איך השאילתה רצה
explain = collection.find({"age": {"$gt": 25}}).explain()
print(explain['executionStats'])
```

#### תמיד טפל בשגיאות
```python
try:
    result = collection.find_one({"_id": some_id})
    if result:
        print("נמצא!")
    else:
        print("לא נמצא")
except Exception as e:
    print(f"שגיאה: {e}")
```

#### זכור את הסדר באגרגציה
```python
# הסדר חשוב! תמיד:
# 1. $match (סינון) - ראשון
# 2. $group (קיבוץ) 
# 3. $sort (מיון)
# 4. $limit (הגבלה) - אחרון

pipeline = [
    {"$match": {"active": True}},      # ראשון - סנן
    {"$group": {"_id": "$category", "count": {"$sum": 1}}},  # קבץ
    {"$sort": {"count": -1}},          # מיין
    {"$limit": 10}                     # הגבל - אחרון
]
```

---

## לסיכום - חוק הזהב למבחן

**אם אתה זוכר רק דבר אחד, זכור את זה:**

1. **חיפוש פשוט** → `find()` או `find_one()`
2. **חישובים וקיבוצים** → `aggregate()`
3. **שינוי נתונים** → `update_one()` או `update_many()`
4. **הוספת נתונים** → `insert_one()` או `insert_many()`
5. **מחיקת נתונים** → `delete_one()` או `delete_many()`

**ותמיד בדוק את המבנה של הנתונים בתחילת המבחן!**

```python
# השורה הראשונה שכותבים בכל מבחן:
sample = collection.find_one()
print(sample)
```

בהצלחה במבחן! 🚀