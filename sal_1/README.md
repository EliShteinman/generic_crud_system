# 🚀 מערכת CRUD גנרית מלאה עם MongoDB ו-FastAPI

מערכת CRUD מלאה וגנרית המאפשרת ניהול נתונים בכל מבנה אפשרי. מיועדת במיוחד למבחנים בהם המבנה הנתונים לא ידוע מראש.

## 📋 תוכן עניינים

- [התקנה מהירה](#התקנה-מהירה)
- [הפעלת המערכת](#הפעלת-המערכת)
- [שימוש בסיסי](#שימוש-בסיסי)
- [API מלא](#api-מלא)
- [דוגמאות למבחן](#דוגמאות-למבחן)
- [פתרון בעיות](#פתרון-בעיות)

## 🎯 תכונות עיקריות

✅ **CRUD מלא** - יצירה, קריאה, עדכון, מחיקה  
✅ **חיפוש מתקדם** - פילטרים, מיון, עימוד  
✅ **פעולות חבצות** - עדכון/מחיקה של מספר רשומות  
✅ **ייצוא וייבוא** - JSON, CSV, Excel  
✅ **סטטיסטיקות** - ניתוח נתונים מפורט  
✅ **ניהול אינדקסים** - אופטימיזציה אוטומטית  
✅ **גיבוי ושחזור** - הגנה על הנתונים  
✅ **תמיכה בכל מבנה נתונים** - גנרי לחלוטין  

## ⚡ התקנה מהירה

### 1. דרישות מערכת
```bash
# MongoDB (יש להתקין נפרד)
# Python 3.8+
```

### 2. התקנת החבילות
```bash
pip install -r requirements.txt
```

### 3. הגדרות סביבה (אופציונלי)
```bash
export MONGO_HOST=localhost
export MONGO_PORT=27017
export MONGO_DB_NAME=test_db
export MONGO_COLLECTION_NAME=items
export LOG_LEVEL=INFO
```

## 🚀 הפעלת המערכת

### הפעלה פשוטה
```bash
python main.py --reload
```

### הפעלה מתקדמת
```bash
python main.py --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### הפעלה עם uvicorn
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 גישה למערכת

- **תיעוד API:** http://localhost:8000/docs
- **בדיקת בריאות:** http://localhost:8000/health
- **מדריך מהיר:** http://localhost:8000/quick-start

## 💡 שימוש בסיסי

### 1. בדיקת תקינות המערכת
```bash
curl http://localhost:8000/health
```

### 2. יצירת רשומה חדשה
```bash
curl -X POST "http://localhost:8000/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "name": "פריט ראשון",
      "category": "בדיקה",
      "price": 100,
      "active": true
    }
  }'
```

### 3. קבלת רשומה
```bash
curl "http://localhost:8000/api/v1/items/{item_id}"
```

### 4. חיפוש מתקדם
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "פריט",
    "page": 1,
    "limit": 10,
    "include_count": true
  }'
```

## 📚 API מלא

### פעולות CRUD בסיסיות

| שיטה | נתיב | תיאור |
|-------|------|-------|
| POST | `/api/v1/items` | יצירת פריט חדש |
| GET | `/api/v1/items/{id}` | קבלת פריט לפי ID |
| PUT | `/api/v1/items/{id}` | עדכון פריט |
| DELETE | `/api/v1/items/{id}` | מחיקת פריט |
| GET | `/api/v1/items` | קבלת כל הפריטים |

### חיפוש מתקדם

| שיטה | נתיב | תיאור |
|-------|------|-------|
| POST | `/api/v1/search` | חיפוש מתקדם עם פילטרים |
| GET | `/api/v1/search/quick` | חיפוש מהיר |
| GET | `/api/v1/search/field/{field}/{value}` | חיפוש לפי שדה |
| GET | `/api/v1/search/date-range` | חיפוש לפי טווח תאריכים |

### פעולות חבצות

| שיטה | נתיב | תיאור |
|-------|------|-------|
| POST | `/api/v1/bulk/create` | יצירה חבצית |
| POST | `/api/v1/bulk/update` | עדכון חבצי |
| POST | `/api/v1/bulk/delete` | מחיקה חבצית |

### ניתוח וסטטיסטיקות

| שיטה | נתיב | תיאור |
|-------|------|-------|
| GET | `/api/v1/statistics` | סטטיסטיקות קולקשן |
| GET | `/api/v1/schema` | מידע על מבנה הנתונים |
| POST | `/api/v1/aggregate` | Aggregation מותאם אישית |
| GET | `/api/v1/distinct/{field}` | ערכים ייחודיים |

### ייצוא וייבוא

| שיטה | נתיב | תיאור |
|-------|------|-------|
| POST | `/api/v1/export` | ייצוא נתונים |
| POST | `/api/v1/import` | ייבוא נתונים |

### ניהול קולקשנים

| שיטה | נתיב | תיאור |
|-------|------|-------|
| GET | `/api/v1/collections` | רשימת קולקשנים |
| POST | `/api/v1/collections/{name}` | יצירת קולקשן |
| DELETE | `/api/v1/collections/{name}` | מחיקת קולקשן |
| PUT | `/api/v1/collections/switch/{name}` | החלפת קולקשן פעיל |

## 🎓 דוגמאות למבחן

### תרחיש 1: ניהול סטודנטים

```bash
# החלפה לקולקשן סטודנטים
curl -X PUT "http://localhost:8000/api/v1/collections/switch/students"

# יצירת סטודנט
curl -X POST "http://localhost:8000/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "first_name": "יוסי",
      "last_name": "כהן",
      "student_id": "123456789",
      "email": "yossi@example.com",
      "grade": 85,
      "course": "מדעי המחשב",
      "year": 2024
    }
  }'

# חיפוש סטודנטים לפי ציון
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [
      {
        "field": "data.grade",
        "operator": "gte",
        "value": 80
      }
    ],
    "sort": [
      {
        "field": "data.grade",
        "order": "desc"
      }
    ],
    "limit": 50
  }'
```

### תרחיש 2: ניהול מוצרים

```bash
# החלפה לקולקשן מוצרים
curl -X PUT "http://localhost:8000/api/v1/collections/switch/products"

# יצירה חבצית של מוצרים
curl -X POST "http://localhost:8000/api/v1/bulk/create" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "מחשב נייד",
      "category": "אלקטרוניקה", 
      "price": 3000,
      "stock": 10,
      "supplier": "טכנולוגיה בע\"מ"
    },
    {
      "name": "עכבר",
      "category": "אלקטרוניקה",
      "price": 50,
      "stock": 100,
      "supplier": "אביזרים בע\"מ"
    }
  ]'

# חיפוש מוצרים בקטגוריה
curl -X GET "http://localhost:8000/api/v1/search/field/data.category/אלקטרוניקה?limit=20"

# סטטיסטיקות על המוצרים
curl "http://localhost:8000/api/v1/statistics"
```

### תרחיש 3: ניתוח נתונים מתקדם

```bash
# aggregation לחישוב ממוצע מחירים לפי קטגוריה
curl -X POST "http://localhost:8000/api/v1/aggregate" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "$group": {
        "_id": "$data.category",
        "average_price": {"$avg": "$data.price"},
        "total_items": {"$sum": 1},
        "max_price": {"$max": "$data.price"},
        "min_price": {"$min": "$data.price"}
      }
    },
    {
      "$sort": {"average_price": -1}
    }
  ]'

# ייצוא לקובץ CSV
curl -X POST "http://localhost:8000/api/v1/export?format=csv" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [
      {
        "field": "data.price",
        "operator": "gte", 
        "value": 100
      }
    ]
  }' \
  --output products_export.csv
```

## 🔧 תצורה מתקדמת

### משתני סביבה

```bash
# חיבור MongoDB
export MONGO_HOST=localhost
export MONGO_PORT=27017
export MONGO_USER=username          # אופציונלי
export MONGO_PASSWORD=password      # אופציונלי
export MONGO_DB_NAME=my_database

# הגדרות מערכת
export LOG_LEVEL=DEBUG              # DEBUG, INFO, WARNING, ERROR
export MAX_ITEMS_PER_REQUEST=1000   # הגבלת פריטים בבקשה
export DEFAULT_PAGE_SIZE=50         # גודל עמוד ברירת מחדל

# אבטחה (אופציונלי)
export ENABLE_AUTH=true
export API_KEY=your-secret-key
export CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### הפעלה עם Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# בניה והרצה
docker build -t generic-crud .
docker run -p 8000:8000 -e MONGO_HOST=host.docker.internal generic-crud
```

## 🔍 חיפוש ופילטרים מתקדמים

### אופרטורי חיפוש

| אופרטור | תיאור | דוגמה |
|----------|--------|-------|
| `eq` | שווה ל | `{"field": "data.name", "operator": "eq", "value": "יוסי"}` |
| `ne` | לא שווה ל | `{"field": "data.active", "operator": "ne", "value": false}` |
| `gt` | גדול מ | `{"field": "data.price", "operator": "gt", "value": 100}` |
| `gte` | גדול או שווה | `{"field": "data.grade", "operator": "gte", "value": 80}` |
| `lt` | קטן מ | `{"field": "data.age", "operator": "lt", "value": 30}` |
| `lte` | קטן או שווה | `{"field": "data.stock", "operator": "lte", "value": 10}` |
| `contains` | מכיל טקסט | `{"field": "data.description", "operator": "contains", "value": "מחשב"}` |
| `starts` | מתחיל ב | `{"field": "data.name", "operator": "starts", "value": "דר"}` |
| `ends` | מסתיים ב | `{"field": "data.email", "operator": "ends", "value": "@gmail.com"}` |
| `in` | קיים ברשימה | `{"field": "data.category", "operator": "in", "value": ["אלקטרוניקה", "ספרים"]}` |
| `nin` | לא קיים ברשימה | `{"field": "data.status", "operator": "nin", "value": ["מבוטל", "מחוק"]}` |
| `regex` | ביטוי רגולרי | `{"field": "data.phone", "operator": "regex", "value": "^05[0-9]"}` |
| `exists` | השדה קיים | `{"field": "data.optional_field", "operator": "exists", "value": true}` |
| `size` | גודל מערך | `{"field": "data.tags", "operator": "size", "value": 3}` |

### דוגמאות חיפוש מתקדמות

#### חיפוש רב-תנאי
```json
{
  "filters": [
    {
      "field": "data.category",
      "operator": "eq",
      "value": "אלקטרוניקה"
    },
    {
      "field": "data.price",
      "operator": "gte",
      "value": 500
    },
    {
      "field": "data.stock",
      "operator": "gt",
      "value": 0
    }
  ],
  "sort": [
    {
      "field": "data.price",
      "order": "asc"
    }
  ],
  "page": 1,
  "limit": 20
}
```

#### חיפוש עם טקסט חופשי ופילטרים
```json
{
  "text": "מחשב נייד",
  "fields": ["data.name", "data.description"],
  "filters": [
    {
      "field": "data.price",
      "operator": "lte",
      "value": 5000
    }
  ],
  "sort": [
    {
      "field": "data.price",
      "order": "desc"
    }
  ]
}
```

#### חיפוש לפי תאריכים
```json
{
  "filters": [
    {
      "field": "created_at",
      "operator": "gte",
      "value": "2024-01-01T00:00:00"
    },
    {
      "field": "created_at",
      "operator": "lte", 
      "value": "2024-12-31T23:59:59"
    }
  ],
  "sort": [
    {
      "field": "created_at",
      "order": "desc"
    }
  ]
}
```

## 📊 פעולות מתקדמות

### Aggregation למבחנים

#### חישוב ממוצעים לפי קבוצה
```json
[
  {
    "$match": {
      "data.category": "אלקטרוניקה"
    }
  },
  {
    "$group": {
      "_id": "$data.supplier",
      "average_price": {"$avg": "$data.price"},
      "total_products": {"$sum": 1},
      "max_price": {"$max": "$data.price"},
      "min_price": {"$min": "$data.price"}
    }
  },
  {
    "$sort": {"average_price": -1}
  }
]
```

#### ספירת פריטים לפי תאריכים
```json
[
  {
    "$group": {
      "_id": {
        "year": {"$year": "$created_at"},
        "month": {"$month": "$created_at"}
      },
      "count": {"$sum": 1}
    }
  },
  {
    "$sort": {"_id.year": 1, "_id.month": 1}
  }
]
```

#### מציאת TOP 10
```json
[
  {
    "$match": {
      "data.active": true
    }
  },
  {
    "$sort": {"data.sales": -1}
  },
  {
    "$limit": 10
  },
  {
    "$project": {
      "name": "$data.name",
      "sales": "$data.sales",
      "rank": {"$literal": null}
    }
  }
]
```

## 🛠️ פתרון בעיות נפוצות

### בעיית חיבור למונגו
```bash
# בדיקת חיבור
curl http://localhost:8000/test/connectivity

# בדיקת מצב המסד
curl http://localhost:8000/health
```

**פתרונות:**
1. ודא שMongoDB פועל: `sudo systemctl status mongod`
2. בדוק הגדרות חיבור: `echo $MONGO_HOST`
3. נסה חיבור ידני: `mongo --host localhost --port 27017`

### שגיאות אימות נתונים
```json
{
  "error": true,
  "status_code": 422,
  "message": "שגיאת אימות נתונים"
}
```

**פתרון:** וודא שהנתונים בפורמט הנכון:
```json
{
  "data": {
    "field1": "value1",
    "field2": 123
  }
}
```

### ביצועים איטיים
1. **יצירת אינדקסים:**
```bash
curl -X POST "http://localhost:8000/api/v1/indexes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "category_index",
    "fields": {"data.category": 1},
    "background": true
  }'
```

2. **אופטימיזציה:**
```bash
curl -X POST "http://localhost:8000/api/v1/maintenance/optimize"
```

### ניקוי נתונים
```bash
# ניקוי רשומות ישנות (30+ ימים)
curl -X POST "http://localhost:8000/api/v1/maintenance/cleanup?days_old=30"

# ניקוי נתוני דמו
curl -X DELETE "http://localhost:8000/api/v1/demo/cleanup"
```

## 🎯 טיפים למבחן

### 1. הכנה מהירה
```bash
# הפעלת שרת
python main.py --reload

# מילוי נתוני דמו
curl -X POST "http://localhost:8000/api/v1/demo/populate"

# בדיקת תקינות
curl "http://localhost:8000/health"
```

### 2. מעבר בין נושאים
```bash
# עבור לקולקשן סטודנטים
curl -X PUT "http://localhost:8000/api/v1/collections/switch/students"

# עבור לקולקשן מוצרים  
curl -X PUT "http://localhost:8000/api/v1/collections/switch/products"

# רשימת כל הקולקשנים
curl "http://localhost:8000/api/v1/collections"
```

### 3. שמירת נתונים
```bash
# גיבוי לפני התחלת מבחן
curl -X POST "http://localhost:8000/api/v1/backup"

# ייצוא נתונים ל-JSON
curl -X POST "http://localhost:8000/api/v1/export?format=json" > backup.json
```

### 4. תבניות נפוצות למבחן

#### תבנית סטודנט
```json
{
  "data": {
    "student_id": "123456789",
    "first_name": "שם פרטי",
    "last_name": "שם משפחה",
    "email": "student@example.com",
    "phone": "0501234567",
    "course": "מדעי המחשב",
    "year": 2024,
    "grade": 85,
    "active": true
  }
}
```

#### תבנית מוצר
```json
{
  "data": {
    "name": "שם המוצר",
    "category": "קטגוריה",
    "price": 299.99,
    "stock": 50,
    "supplier": "שם הספק",
    "description": "תיאור המוצר",
    "tags": ["תג1", "תג2"],
    "active": true
  }
}
```

#### תבנית עובד
```json
{
  "data": {
    "employee_id": "EMP001",
    "first_name": "שם פרטי",
    "last_name": "שם משפחה",
    "department": "מחלקה",
    "position": "תפקיד",
    "salary": 15000,
    "hire_date": "2024-01-15",
    "email": "employee@company.com",
    "active": true
  }
}
```

## 📈 ניטור וביצועים

### מדדי ביצועים
```bash
# מידע על המערכת
curl "http://localhost:8000/system/metrics"

# סטטיסטיקות מסד נתונים
curl "http://localhost:8000/api/v1/statistics"

# מידע מפורט על הקולקשן
curl "http://localhost:8000/api/v1/info"
```

### בדיקת איכות נתונים
```bash
# אימות תקינות נתונים
curl -X POST "http://localhost:8000/api/v1/maintenance/validate"

# מציאת כפולות
curl -X POST "http://localhost:8000/api/v1/duplicates" \
  -H "Content-Type: application/json" \
  -d '["data.email", "data.phone"]'
```

## 🔐 אבטחה

### הפעלת אימות
```bash
export ENABLE_AUTH=true
export API_KEY=your-secret-key-here
```

### שימוש עם API Key
```bash
curl -H "X-API-Key: your-secret-key-here" \
  "http://localhost:8000/api/v1/items"
```

## 🚀 פריסה לייצור

### עם Gunicorn
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### עם Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGO_HOST=mongo
      - MONGO_DB_NAME=production_db
    depends_on:
      - mongo

  mongo:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

## 📞 תמיכה

לשאלות ובעיות:
1. בדוק את הלוגים: `tail -f app.log`
2. גש לתיעוד: http://localhost:8000/docs
3. בדוק בריאות המערכת: http://localhost:8000/health

## 📄 רישיון

MIT License - ניתן לשימוש חופשי במבחנים ופרויקטים.

---

**🎓 בהצלחה במבחן! המערכת מכילה כל מה שצריך לכל תרחיש אפשרי.**