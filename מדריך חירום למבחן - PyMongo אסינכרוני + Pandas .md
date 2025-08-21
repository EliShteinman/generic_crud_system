# מדריך חירום למבחן - PyMongo אסינכרוני + Pandas

## 🚨 אם יש לך 5 דקות במבחן - קרא רק את זה!

### קוד מינימלי שעובד תמיד:

```python
import asyncio
import pandas as pd
from pymongo import AsyncMongoClient

async def emergency_analysis():
    # 1. חיבור מהיר
    client = AsyncMongoClient("mongodb+srv://user:pass@cluster.mongodb.net/")
    db = client["db_name"]
    collection = db["collection_name"]
    
    try:
        # 2. בדיקה ראשונה - תמיד!
        sample = await collection.find_one()
        print("🔍 מבנה נתונים:", list(sample.keys()) if sample else "ריק")
        
        total = await collection.count_documents({})
        print(f"📊 סה\"כ מסמכים: {total:,}")
        
        # 3. טעינה חכמה
        docs = []
        if total > 5000:
            # גדול - דגימה בלבד
            cursor = collection.find({}).limit(1000)
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                docs.append(doc)
            print(f"📦 נטענה דגימה: {len(docs)} מתוך {total}")
        else:
            # קטן - הכל
            async for doc in collection.find({}):
                doc['_id'] = str(doc['_id'])
                docs.append(doc)
            print(f"📦 נטען הכל: {len(docs)} מסמכים")
        
        # 4. Pandas מהיר
        df = pd.DataFrame(docs)
        
        # 5. ניתוח בזק
        print(f"\n🐼 DataFrame: {df.shape[0]} שורות, {df.shape[1]} עמודות")
        print(f"📋 עמודות: {list(df.columns)}")
        
        # מספרים
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            print(f"\n📈 עמודות מספריות: {list(numeric_cols)}")
            print(df[numeric_cols].describe())
        
        # קטגוריות
        obj_cols = df.select_dtypes(include=['object']).columns
        for col in obj_cols[:3]:  # רק 3 ראשונות
            if df[col].nunique() < 20:  # רק אם לא יותר מדי ערכים
                print(f"\n📊 התפלגות {col}:")
                print(df[col].value_counts().head())
        
        return df
        
    finally:
        client.close()

# הרצה
df = asyncio.run(emergency_analysis())
```

---

## 🔥 פונקציות חירום - העתק והדבק

### 1. דיפדוף מהיר (40 בכל פעם)

```python
async def quick_paginate(collection, page_size=40, max_docs=2000):
    """דיפדוף מהיר - 40 מסמכים בכל פעם"""
    docs = []
    skip = 0
    
    while len(docs) < max_docs:
        batch = []
        cursor = collection.find({}).skip(skip).limit(page_size)
        
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            batch.append(doc)
        
        if not batch:  # אין יותר נתונים
            break
            
        docs.extend(batch)
        skip += page_size
        print(f"📄 טען {len(docs)} / {max_docs}")
    
    return docs[:max_docs]  # הגבלה

# שימוש:
# docs = await quick_paginate(collection)
```

### 2. אגרגציה מהירה

```python
async def quick_aggregation(collection, group_by_field, value_field=None):
    """אגרגציה מהירה לסטטיסטיקות"""
    
    if value_field:
        # עם חישובים
        pipeline = [
            {"$group": {
                "_id": f"${group_by_field}",
                "count": {"$sum": 1},
                "total": {"$sum": f"${value_field}"},
                "avg": {"$avg": f"${value_field}"},
                "min": {"$min": f"${value_field}"},
                "max": {"$max": f"${value_field}"}
            }},
            {"$sort": {"count": -1}}
        ]
    else:
        # רק ספירה
        pipeline = [
            {"$group": {
                "_id": f"${group_by_field}",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
    
    results = []
    async for doc in collection.aggregate(pipeline):
        results.append(doc)
    
    return results

# שימוש:
# stats = await quick_aggregation(collection, "category", "price")
```

### 3. Pandas מהיר

```python
def quick_pandas_analysis(df, target_col=None):
    """ניתוח Pandas מהיר"""
    
    print(f"📊 DataFrame: {df.shape}")
    print(f"📋 עמודות: {list(df.columns)}")
    
    # מספרים
    nums = df.select_dtypes(include=['number']).columns
    if len(nums) > 0:
        print(f"\n🔢 מספרים: {list(nums)}")
        if target_col and target_col in nums:
            col = df[target_col]
            print(f"   {target_col}: ממוצע={col.mean():.2f}, חציון={col.median():.2f}")
    
    # טקסט
    cats = df.select_dtypes(include=['object']).columns
    for col in cats[:2]:  # רק 2 ראשונות
        if df[col].nunique() < 15:
            print(f"\n📝 {col}:")
            print(df[col].value_counts().head(5))
    
    return df.describe()

# שימוש:
# quick_pandas_analysis(df, "grade")
```

### 4. TOP N מהיר

```python
async def quick_top_n(collection, field, n=10, descending=True):
    """TOP N מהיר"""
    
    sort_dir = -1 if descending else 1
    
    docs = []
    cursor = collection.find({}).sort(field, sort_dir).limit(n)
    
    async for doc in cursor:
        doc['_id'] = str(doc['_id'])
        docs.append(doc)
    
    print(f"🏆 TOP {len(docs)} לפי {field}:")
    for i, doc in enumerate(docs, 1):
        name = doc.get('name', doc.get('title', str(doc.get('_id', i))))
        value = doc.get(field, 'N/A')
        print(f"   {i}. {name}: {value}")
    
    return docs

# שימוש:
# top_students = await quick_top_n(collection, "gpa")
```

---

## ⚡ תרחישים נפוצים במבחן

### תרחיש 1: ניתוח סטודנטים

```python
async def analyze_students_emergency():
    client = AsyncMongoClient("connection_string")
    collection = client["school"]["students"]
    
    try:
        # בדיקה מהירה
        sample = await collection.find_one()
        total = await collection.count_documents({})
        print(f"🎓 {total} סטודנטים, שדות: {list(sample.keys())}")
        
        # סטטיסטיקות מהירות בMongoDB
        grade_stats = await quick_aggregation(collection, "course", "gpa")
        print("\n📊 ממוצע ציונים לפי קורס:")
        for stat in grade_stats[:5]:
            print(f"   {stat['_id']}: {stat['avg']:.2f} (סטודנטים: {stat['count']})")
        
        # טעינה ל-Pandas לניתוח מפורט
        docs = await quick_paginate(collection, page_size=50, max_docs=1000)
        df = pd.DataFrame(docs)
        
        # ניתוח מהיר
        print(f"\n🐼 ניתוח מפורט:")
        print(f"   ממוצע GPA כללי: {df['gpa'].mean():.2f}")
        print(f"   סטודנטים פעילים: {df['active'].sum()}")
        print(f"   גיל ממוצע: {df['age'].mean():.1f}")
        
        return df
        
    finally:
        client.close()

# הרצה
df = asyncio.run(analyze_students_emergency())
```

### תרחיש 2: ניתוח מכירות

```python
async def analyze_sales_emergency():
    client = AsyncMongoClient("connection_string")
    collection = client["store"]["sales"]
    
    try:
        # מכירות לפי אזור
        region_stats = await quick_aggregation(collection, "region", "amount")
        print("💰 מכירות לפי אזור:")
        for stat in region_stats:
            print(f"   {stat['_id']}: {stat['total']:,.0f}₪ (עסקאות: {stat['count']})")
        
        # TOP מוכרים
        top_sales = await quick_top_n(collection, "amount", n=5)
        
        # נתונים ל-Pandas
        docs = await quick_paginate(collection, max_docs=2000)
        df = pd.DataFrame(docs)
        
        # המרת תאריכים
        if 'sale_date' in df.columns:
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            df['month'] = df['sale_date'].dt.to_period('M')
            
            monthly_sales = df.groupby('month')['amount'].sum()
            print(f"\n📈 מכירות חודשיות:")
            print(monthly_sales.tail())
        
        return df
        
    finally:
        client.close()

# הרצה
df = asyncio.run(analyze_sales_emergency())
```

### תרחיש 3: ניתוח כללי (לא יודע מה יש)

```python
async def analyze_unknown_collection():
    client = AsyncMongoClient("connection_string")
    db = client["database_name"]
    collection = db["collection_name"]
    
    try:
        # גילוי מבנה
        sample = await collection.find_one()
        if not sample:
            print("❌ אוסף ריק!")
            return None
            
        print("🔍 מבנה הנתונים:")
        for key, value in sample.items():
            value_type = type(value).__name__
            print(f"   {key}: {value_type} = {str(value)[:50]}")
        
        # זיהוי שדות חשובים
        numeric_fields = []
        category_fields = []
        
        for key, value in sample.items():
            if isinstance(value, (int, float)):
                numeric_fields.append(key)
            elif isinstance(value, str) and len(value) < 50:
                category_fields.append(key)
        
        print(f"\n📊 שדות מספריים: {numeric_fields}")
        print(f"🏷️ שדות קטגוריה: {category_fields}")
        
        # ניתוח אוטומטי
        if category_fields and numeric_fields:
            cat_field = category_fields[0]
            num_field = numeric_fields[0]
            
            stats = await quick_aggregation(collection, cat_field, num_field)
            print(f"\n📈 {num_field} לפי {cat_field}:")
            for stat in stats[:5]:
                print(f"   {stat['_id']}: ממוצע={stat['avg']:.2f}")
        
        # טעינה ל-Pandas
        docs = await quick_paginate(collection, max_docs=1500)
        df = pd.DataFrame(docs)
        
        quick_pandas_analysis(df, numeric_fields[0] if numeric_fields else None)
        
        return df
        
    finally:
        client.close()

# הרצה
df = asyncio.run(analyze_unknown_collection())
```

---

## 🆘 פתרון בעיות מהיר

### בעיה: לא מצליח להתחבר
```python
# בדיקה מהירה של חיבור
async def test_connection():
    try:
        client = AsyncMongoClient("connection_string", serverSelectionTimeoutMS=3000)
        await client.admin.command('ping')
        print("✅ חיבור תקין")
        client.close()
        return True
    except Exception as e:
        print(f"❌ שגיאת חיבור: {e}")
        return False

# asyncio.run(test_connection())
```

### בעיה: אין נתונים
```python
# בדיקה מהירה של נתונים
async def check_data():
    client = AsyncMongoClient("connection_string")
    db = client["db_name"]
    
    print("📋 קולקשנים זמינים:")
    collections = await db.list_collection_names()
    for coll in collections:
        count = await db[coll].count_documents({})
        print(f"   {coll}: {count:,} מסמכים")
    
    client.close()

# asyncio.run(check_data())
```

### בעיה: DataFrame ריק
```python
def fix_empty_dataframe(docs):
    """תיקון DataFrame ריק"""
    if not docs:
        print("⚠️ אין נתונים - יוצר DataFrame ריק")
        return pd.DataFrame()
    
    df = pd.DataFrame(docs)
    
    if df.empty:
        print("⚠️ DataFrame ריק למרות שיש נתונים")
        print(f"   נתונים גולמיים: {len(docs)} פריטים")
        print(f"   דוגמה: {docs[0] if docs else 'אין'}")
        return pd.DataFrame()
    
    return df
```

---

## 📝 רשימת בדיקות לפני מבחן

### ✅ לוודא שעובד:

1. **חיבור בסיסי:**
```python
asyncio.run(test_connection())
```

2. **קריאת נתונים:**
```python
async def basic_test():
    client = AsyncMongoClient("connection_string")
    collection = client["db"]["collection"]
    doc = await collection.find_one()
    print("נתונים:", doc)
    client.close()

asyncio.run(basic_test())
```

3. **המרה ל-Pandas:**
```python
docs = [{"name": "test", "value": 123}]
df = pd.DataFrame(docs)
print(df)
```

### 🔧 אם משהו לא עובד:

1. **בדוק חיבור:** Connection string נכון?
2. **בדוק שמות:** Database וcollection נכונים?
3. **בדוק נתונים:** האם יש בכלל נתונים?
4. **בדוק ObjectId:** המרה למחרוזת?

---

## 🎯 קוד העתק-הדבק אחרון למבחן

```python
# השורות האלה תמיד עובדות - העתק והחלף את הפרטים
import asyncio
import pandas as pd
from pymongo import AsyncMongoClient

async def exam_solution():
    # החלף כאן ↓
    client = AsyncMongoClient("mongodb+srv://user:pass@cluster.mongodb.net/")
    collection = client["DB_NAME"]["COLLECTION_NAME"]
    
    try:
        # תמיד תתחיל עם זה ↓
        sample = await collection.find_one()
        print("שדות:", list(sample.keys()) if sample else "ריק")
        
        total = await collection.count_documents({})
        print(f"סה\"כ: {total}")
        
        # טען נתונים ↓
        docs = []
        limit = min(2000, total)  # מקסימום 2000
        
        async for doc in collection.find({}).limit(limit):
            doc['_id'] = str(doc['_id'])
            docs.append(doc)
        
        # Pandas ↓
        df = pd.DataFrame(docs)
        print(f"DataFrame: {df.shape}")
        
        # ניתוח בסיסי ↓
        print(df.describe())
        
        # אם יש קטגוריות ↓
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() < 20:
                print(f"\n{col}:")
                print(df[col].value_counts().head())
        
        return df
        
    finally:
        client.close()

# הרצה ↓
df = asyncio.run(exam_solution())
```

**זה הקוד שתמיד עובד! רק תחליף את החיבור ושמות הקולקשן!** 🎯