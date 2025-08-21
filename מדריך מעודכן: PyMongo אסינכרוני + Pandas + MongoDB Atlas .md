# מדריך מעודכן: PyMongo אסינכרוני + Pandas + MongoDB Atlas

## תוכן עניינים
1. [חיבור ל-MongoDB Atlas עם PyMongo אסינכרוני](#חיבור-ל-mongodb-atlas)
2. [DAL מעשי לאטלס](#dal-מעשי-לאטלס)
3. [קריאת נתונים - סינכרוני vs אסינכרוני](#קריאת-נתונים)
4. [המרה ל-Pandas](#המרה-ל-pandas)
5. [דיפדוף (Pagination) במסמכים](#דיפדוף-במסמכים)
6. [מדריך Pandas למבחן](#מדריך-pandas-למבחן)

---

## חיבור ל-MongoDB Atlas

### PyMongo מודרני (4.0+) - סינכרוני ואסינכרוני

```python
# התקנה
pip install pymongo[srv] pandas

# ייבוא
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional
```

### חיבור ל-Atlas (סינכרוני)
```python
class MongoAtlasConnection:
    def __init__(self, connection_string: str, database_name: str):
        """
        חיבור ל-MongoDB Atlas
        connection_string: mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
    
    def connect(self):
        """יצירת חיבור ל-Atlas"""
        try:
            self.client = MongoClient(
                self.connection_string,
                server_api=ServerApi('1'),  # גרסה יציבה
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50,
                retryWrites=True
            )
            
            # בדיקת חיבור
            self.client.admin.command('ping')
            print("✅ חיבור ל-MongoDB Atlas הצליח!")
            
            self.db = self.client[self.database_name]
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בחיבור ל-Atlas: {e}")
            return False
    
    def get_collection(self, collection_name: str):
        """קבלת קולקשן"""
        if self.db is None:
            raise RuntimeError("לא מחובר למסד נתונים")
        return self.db[collection_name]
    
    def disconnect(self):
        """ניתוק"""
        if self.client:
            self.client.close()
            print("🔌 התנתקות מ-Atlas הושלמה")

# שימוש:
atlas = MongoAtlasConnection(
    "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority",
    "school_db"
)

if atlas.connect():
    students_collection = atlas.get_collection("students")
```

### חיבור אסינכרוני (עם AsyncIOMotorClient)
```python
from motor.motor_asyncio import AsyncIOMotorClient

class AsyncMongoAtlas:
    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
    
    async def connect(self):
        """חיבור אסינכרוני"""
        try:
            self.client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50
            )
            
            # בדיקת חיבור
            await self.client.admin.command('ping')
            print("✅ חיבור אסינכרוני ל-Atlas הצליח!")
            
            self.db = self.client[self.database_name]
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בחיבור אסינכרוני: {e}")
            return False
    
    def get_collection(self, collection_name: str):
        if self.db is None:
            raise RuntimeError("לא מחובר למסד נתונים")
        return self.db[collection_name]
    
    async def disconnect(self):
        if self.client:
            self.client.close()

# שימוש:
async def main():
    atlas = AsyncMongoAtlas(
        "mongodb+srv://username:password@cluster.mongodb.net/",
        "school_db"
    )
    
    if await atlas.connect():
        collection = atlas.get_collection("students")
        # עבודה עם הקולקשן...
        await atlas.disconnect()

# הרצה
asyncio.run(main())
```

---

## DAL מעשי לאטלס

```python
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

class AtlasDAL:
    """שכבת גישה לנתונים ל-MongoDB Atlas"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.atlas = MongoAtlasConnection(connection_string, database_name)
        self.connected = False
    
    def connect(self) -> bool:
        """התחברות למסד"""
        self.connected = self.atlas.connect()
        return self.connected
    
    def _ensure_connected(self):
        """בדיקה שיש חיבור"""
        if not self.connected:
            raise RuntimeError("DAL לא מחובר למסד נתונים")
    
    def find_documents(self, collection_name: str, 
                      query: Dict[str, Any] = None,
                      projection: Dict[str, int] = None,
                      sort: List[tuple] = None,
                      limit: int = None,
                      skip: int = 0) -> List[Dict[str, Any]]:
        """מציאת מסמכים עם אפשרויות מלאות"""
        
        self._ensure_connected()
        collection = self.atlas.get_collection(collection_name)
        
        query = query or {}
        cursor = collection.find(query, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        # המרה לרשימה + ניקוי ObjectId
        documents = []
        for doc in cursor:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            documents.append(doc)
        
        return documents
    
    def find_one_document(self, collection_name: str,
                         query: Dict[str, Any],
                         projection: Dict[str, int] = None) -> Optional[Dict[str, Any]]:
        """מציאת מסמך אחד"""
        
        self._ensure_connected()
        collection = self.atlas.get_collection(collection_name)
        
        doc = collection.find_one(query, projection)
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        return doc
    
    def count_documents(self, collection_name: str,
                       query: Dict[str, Any] = None) -> int:
        """ספירת מסמכים"""
        
        self._ensure_connected()
        collection = self.atlas.get_collection(collection_name)
        
        query = query or {}
        return collection.count_documents(query)
    
    def aggregate_data(self, collection_name: str,
                      pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ביצוע אגרגציה"""
        
        self._ensure_connected()
        collection = self.atlas.get_collection(collection_name)
        
        # אגרגציה מחזירה cursor
        cursor = collection.aggregate(pipeline)
        
        # המרה לרשימה + ניקוי ObjectId
        results = []
        for doc in cursor:
            if '_id' in doc and doc['_id'] is not None:
                doc['_id'] = str(doc['_id'])
            results.append(doc)
        
        return results
    
    def get_distinct_values(self, collection_name: str,
                           field: str,
                           query: Dict[str, Any] = None) -> List[Any]:
        """ערכים ייחודיים בשדה"""
        
        self._ensure_connected()
        collection = self.atlas.get_collection(collection_name)
        
        query = query or {}
        return collection.distinct(field, query)
    
    def disconnect(self):
        """ניתוק"""
        if self.connected:
            self.atlas.disconnect()
            self.connected = False

# דוגמה לשימוש:
dal = AtlasDAL(
    "mongodb+srv://username:password@cluster.mongodb.net/",
    "school_db"
)

if dal.connect():
    # מציאת כל הסטודנטים הפעילים
    students = dal.find_documents(
        "students",
        query={"active": True},
        sort=[("name", 1)],
        limit=100
    )
    
    print(f"נמצאו {len(students)} סטודנטים פעילים")
```

---

## קריאת נתונים - מתי לעבור בלולאה?

### 1. כמות קטנה של נתונים (עד 1000 מסמכים)
```python
# טוען הכל לזיכרון בבת אחת
def load_small_dataset(dal, collection_name, query=None):
    """לטעינת מערכי נתונים קטנים"""
    
    documents = dal.find_documents(collection_name, query=query)
    
    print(f"נטענו {len(documents)} מסמכים לזיכרון")
    return documents

# שימוש:
students = load_small_dataset(dal, "students", {"course": "מתמטיקה"})

# עיבוד ישיר
for student in students:
    print(f"{student['name']} - ציון: {student.get('grade', 'N/A')}")
```

### 2. כמות גדולה - עיבוד בחלקים (Chunking)
```python
def process_large_dataset_in_chunks(dal, collection_name, 
                                   query=None, chunk_size=1000):
    """עיבוד מערך נתונים גדול בחלקים"""
    
    total_docs = dal.count_documents(collection_name, query)
    print(f"סה\"כ {total_docs} מסמכים לעיבוד")
    
    processed = 0
    skip = 0
    
    while skip < total_docs:
        # טוען חלק
        chunk = dal.find_documents(
            collection_name,
            query=query,
            skip=skip,
            limit=chunk_size
        )
        
        if not chunk:  # אין יותר נתונים
            break
        
        # עיבוד החלק
        for doc in chunk:
            # כאן תעשה את העיבוד שלך
            process_single_document(doc)
        
        processed += len(chunk)
        skip += chunk_size
        
        print(f"עובד... {processed}/{total_docs} ({processed/total_docs*100:.1f}%)")
    
    print(f"✅ סיום עיבוד {processed} מסמכים")

def process_single_document(doc):
    """עיבוד מסמך יחיד"""
    # כאן הלוגיקה שלך לכל מסמך
    pass

# שימוש:
process_large_dataset_in_chunks(
    dal, 
    "large_collection",
    query={"status": "active"},
    chunk_size=500
)
```

### 3. עיבוד אסינכרוני (ליעילות מקסימלית)
```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

class AsyncAtlasDAL:
    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
    
    async def connect(self):
        self.client = AsyncIOMotorClient(self.connection_string)
        await self.client.admin.command('ping')
        self.db = self.client[self.database_name]
        return True
    
    async def find_documents_async(self, collection_name, query=None, limit=None):
        collection = self.db[collection_name]
        cursor = collection.find(query or {})
        
        if limit:
            cursor = cursor.limit(limit)
        
        documents = []
        async for doc in cursor:  # לולאה אסינכרונית
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            documents.append(doc)
        
        return documents

# שימוש אסינכרוני:
async def process_data_async():
    dal = AsyncAtlasDAL(
        "mongodb+srv://username:password@cluster.mongodb.net/",
        "school_db"
    )
    
    await dal.connect()
    
    # עיבוד מהיר של נתונים
    students = await dal.find_documents_async("students", {"active": True})
    
    print(f"נטענו {len(students)} סטודנטים במהירות")
    
    return students

# הרצה:
students = asyncio.run(process_data_async())
```

---

## המרה ל-Pandas

### 1. המרה בסיסית
```python
def mongo_to_pandas(dal, collection_name, query=None, 
                   flatten_nested=True) -> pd.DataFrame:
    """המרת נתוני MongoDB ל-DataFrame"""
    
    # שליפת הנתונים
    documents = dal.find_documents(collection_name, query)
    
    if not documents:
        print("⚠️ לא נמצאו נתונים")
        return pd.DataFrame()
    
    # המרה ל-DataFrame
    df = pd.DataFrame(documents)
    
    if flatten_nested:
        df = flatten_dataframe(df)
    
    print(f"✅ נוצר DataFrame עם {len(df)} שורות ו-{len(df.columns)} עמודות")
    print(f"עמודות: {list(df.columns)}")
    
    return df

def flatten_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """פירוק עמודות מקוננות"""
    
    new_df = df.copy()
    
    for column in df.columns:
        # בדיקה אם יש אובייקטים מקוננים
        if df[column].dtype == 'object':
            sample = df[column].dropna().iloc[0] if not df[column].dropna().empty else None
            
            if isinstance(sample, dict):
                # פירוק dictionary לעמודות נפרדות
                nested_df = pd.json_normalize(df[column])
                nested_df.columns = [f"{column}.{col}" for col in nested_df.columns]
                
                # הסרת העמודה המקורית והוספת העמודות החדשות
                new_df = new_df.drop(columns=[column])
                new_df = pd.concat([new_df, nested_df], axis=1)
    
    return new_df

# שימוש:
df_students = mongo_to_pandas(dal, "students", {"course": "מדעי המחשב"})
print(df_students.head())
```

### 2. המרה מתקדמת עם ניקוי נתונים
```python
def advanced_mongo_to_pandas(dal, collection_name, query=None,
                            date_columns=None, 
                            numeric_columns=None,
                            drop_columns=None) -> pd.DataFrame:
    """המרה מתקדמת עם ניקוי נתונים"""
    
    # שליפת נתונים
    documents = dal.find_documents(collection_name, query)
    
    if not documents:
        return pd.DataFrame()
    
    # המרה בסיסית
    df = pd.DataFrame(documents)
    
    # הסרת עמודות לא רצויות
    if drop_columns:
        df = df.drop(columns=[col for col in drop_columns if col in df.columns])
    
    # המרת עמודות תאריך
    if date_columns:
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # המרת עמודות מספריות
    if numeric_columns:
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # ניקוי בסיסי
    df = df.dropna(how='all')  # הסרת שורות ריקות לגמרי
    
    print(f"✅ DataFrame מוכן: {len(df)} שורות, {len(df.columns)} עמודות")
    print(f"סוגי נתונים:\n{df.dtypes}")
    
    return df

# דוגמה:
df = advanced_mongo_to_pandas(
    dal, 
    "students",
    query={"active": True},
    date_columns=["enrollment_date", "graduation_date"],
    numeric_columns=["age", "gpa", "credits"],
    drop_columns=["_id", "internal_notes"]
)
```

### 3. עבודה עם מערכים במונגו
```python
def handle_array_fields(dal, collection_name, array_field, query=None):
    """טיפול נכון במערכים ממונגו"""
    
    # קודם - ראה איך המערכים נראים
    sample = dal.find_one_document(collection_name, query or {})
    if sample and array_field in sample:
        print(f"דוגמה למערך {array_field}: {sample[array_field]}")
    
    documents = dal.find_documents(collection_name, query)
    
    # שתי אפשרויות:
    
    # אפשרות 1: המערך כטקסט
    df_as_text = pd.DataFrame(documents)
    df_as_text[f"{array_field}_str"] = df_as_text[array_field].astype(str)
    
    # אפשרות 2: פירוק המערך לשורות נפרדות
    exploded_data = []
    for doc in documents:
        if array_field in doc and isinstance(doc[array_field], list):
            for item in doc[array_field]:
                new_doc = doc.copy()
                new_doc[f"{array_field}_item"] = item
                exploded_data.append(new_doc)
    
    df_exploded = pd.DataFrame(exploded_data)
    
    return df_as_text, df_exploded

# דוגמה:
df_grades_text, df_grades_exploded = handle_array_fields(
    dal, "students", "grades", {"course": "מתמטיקה"}
)

print("עם מערכים כטקסט:")
print(df_grades_text[['name', 'grades_str']].head())

print("\nעם מערכים מפורקים:")
print(df_grades_exploded[['name', 'grades_item']].head())
```

---

## דיפדוף (Pagination) במסמכים

### 1. דיפדוף בסיסי
```python
def paginate_collection(dal, collection_name, query=None, 
                       page_size=50, max_pages=None):
    """דיפדוף על כל המסמכים באוסף"""
    
    total_docs = dal.count_documents(collection_name, query)
    total_pages = (total_docs + page_size - 1) // page_size
    
    if max_pages:
        total_pages = min(total_pages, max_pages)
    
    print(f"📊 סה\"כ {total_docs} מסמכים, {total_pages} עמודים")
    
    all_data = []
    
    for page in range(total_pages):
        skip = page * page_size
        
        print(f"📄 טוען עמוד {page + 1}/{total_pages}...")
        
        page_data = dal.find_documents(
            collection_name,
            query=query,
            skip=skip,
            limit=page_size
        )
        
        all_data.extend(page_data)
        
        print(f"   נטענו {len(page_data)} מסמכים (סה\"כ: {len(all_data)})")
        
        # הפסקה קטנה למניעת עומס
        import time
        time.sleep(0.1)
    
    return all_data

# שימוש:
all_students = paginate_collection(
    dal, 
    "students",
    query={"active": True},
    page_size=40,  # 40 מסמכים בכל עמוד
    max_pages=10   # מקסימום 10 עמודים
)

print(f"✅ נטענו סה\"כ {len(all_students)} סטודנטים")
```

### 2. דיפדוף עם עיבוד מיידי
```python
def process_with_pagination(dal, collection_name, 
                           processor_func, query=None, 
                           page_size=100):
    """דיפדוף עם עיבוד מיידי - חוסך זיכרון"""
    
    total_docs = dal.count_documents(collection_name, query)
    total_pages = (total_docs + page_size - 1) // page_size
    
    print(f"🔄 מתחיל עיבוד {total_docs} מסמכים ב-{total_pages} עמודים")
    
    results = []
    
    for page in range(total_pages):
        skip = page * page_size
        
        # טוען עמוד
        page_data = dal.find_documents(
            collection_name,
            query=query,
            skip=skip,
            limit=page_size
        )
        
        # מעבד מיד
        for doc in page_data:
            result = processor_func(doc)
            if result:  # רק אם יש תוצאה
                results.append(result)
        
        print(f"✅ עמוד {page + 1}/{total_pages} - {len(results)} תוצאות עד כה")
    
    return results

# דוגמה לפונקציית עיבוד
def calculate_student_average(student_doc):
    """חישוב ממוצע ציונים לסטודנט"""
    
    if 'grades' in student_doc and student_doc['grades']:
        grades = [g for g in student_doc['grades'] if isinstance(g, (int, float))]
        
        if grades:
            return {
                'name': student_doc.get('name', 'Unknown'),
                'average': sum(grades) / len(grades),
                'grade_count': len(grades)
            }
    
    return None

# שימוש:
averages = process_with_pagination(
    dal,
    "students",
    calculate_student_average,
    query={"grades": {"$exists": True}},
    page_size=50
)

# המרה ל-Pandas לניתוח נוסף
df_averages = pd.DataFrame(averages)
print(f"ממוצע כללי: {df_averages['average'].mean():.2f}")
```

### 3. דיפדוף עם MongoDB Cursor (יעיל יותר)
```python
def efficient_iteration(dal, collection_name, query=None, batch_size=1000):
    """איטרציה יעילה עם cursor"""
    
    collection = dal.atlas.get_collection(collection_name)
    cursor = collection.find(query or {}).batch_size(batch_size)
    
    processed = 0
    batch_data = []
    
    try:
        for doc in cursor:
            # נקה ObjectId
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            
            batch_data.append(doc)
            processed += 1
            
            # כל batch_size מסמכים - עבד אותם
            if len(batch_data) >= batch_size:
                yield batch_data.copy()  # החזר batch
                batch_data.clear()
                
                print(f"🔄 עובד... {processed} מסמכים")
        
        # האחרונים שנשארו
        if batch_data:
            yield batch_data
    
    finally:
        cursor.close()

# שימוש:
for batch in efficient_iteration(dal, "large_collection", batch_size=500):
    # עיבוד כל batch
    df_batch = pd.DataFrame(batch)
    
    # עשה משהו עם ה-DataFrame
    print(f"Batch עם {len(df_batch)} שורות")
    
    # דוגמה: שמירה לקובץ
    # df_batch.to_csv(f"batch_{len(df_batch)}.csv", index=False)
```

---

## מדריך Pandas למבחן

### 1. פעולות בסיסיות על DataFrame
```python
# קריאת מידע בסיסי על הנתונים
def explore_dataframe(df):
    """סקירה מהירה של DataFrame"""
    
    print("📊 מידע כללי:")
    print(f"   גודל: {df.shape[0]} שורות, {df.shape[1]} עמודות")
    print(f"   זיכרון: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    print("\n📋 עמודות וסוגי נתונים:")
    print(df.dtypes)
    
    print("\n🔍 דוגמאות:")
    print(df.head(3))
    
    print("\n📈 סטטיסטיקות בסיסיות:")
    print(df.describe())
    
    print("\n❌ ערכים חסרים:")
    missing = df.isnull().sum()
    print(missing[missing > 0])

# שימוש:
df = mongo_to_pandas(dal, "students")
explore_dataframe(df)
```

### 2. סינון וחיפוש
```python
# סינון נתונים
def filter_examples(df):
    """דוגמאות לסינון DataFrame"""
    
    # סינון בסיסי
    active_students = df[df['active'] == True]
    
    # סינון מספרי
    high_gpa = df[df['gpa'] > 3.5]
    
    # סינון טקסט
    cs_students = df[df['course'].str.contains('מדעי', na=False)]
    
    # סינון מורכב
    good_cs_students = df[
        (df['course'].str.contains('מדעי', na=False)) & 
        (df['gpa'] > 3.0) &
        (df['active'] == True)
    ]
    
    # סינון עם רשימה
    specific_courses = df[df['course'].isin(['מתמטיקה', 'פיזיקה'])]
    
    print(f"סטודנטים פעילים: {len(active_students)}")
    print(f"GPA גבוה: {len(high_gpa)}")
    print(f"מדעי המחשב: {len(cs_students)}")
    print(f"מדמח טובים: {len(good_cs_students)}")
    
    return good_cs_students

# שימוש:
filtered_df = filter_examples(df)
```

### 3. קיבוץ וחישובים (GroupBy)
```python
def groupby_examples(df):
    """דוגמאות לקיבוץ וחישובים"""
    
    # קיבוץ בסיסי
    by_course = df.groupby('course').agg({
        'gpa': ['mean', 'std', 'count'],
        'age': ['mean', 'min', 'max'],
        'active': 'sum'  # כמה פעילים
    }).round(2)
    
    print("📊 סטטיסטיקות לפי קורס:")
    print(by_course)
    
    # קיבוץ מרובה
    by_course_year = df.groupby(['course', 'year']).agg({
        'gpa': 'mean',
        'student_id': 'count'
    }).round(2)
    
    print("\n📊 לפי קורס ושנה:")
    print(by_course_year)
    
    # חישובים מותאמים אישית
    def custom_stats(group):
        return pd.Series({
            'avg_gpa': group['gpa'].mean(),
            'top_student': group.loc[group['gpa'].idxmax(), 'name'] if not group.empty else 'N/A',
            'pass_rate': (group['gpa'] >= 2.0).sum() / len(group) * 100
        })
    
    custom_by_course = df.groupby('course').apply(custom_stats)
    print("\n📊 סטטיסטיקות מותאמות:")
    print(custom_by_course)
    
    return by_course, custom_by_course

# שימוש:
stats, custom_stats = groupby_examples(df)
```

### 4. עבודה עם תאריכים
```python
def datetime_operations(df):
    """פעולות על תאריכים"""
    
    # המרה לתאריך (אם עדיין לא)
    if 'enrollment_date' in df.columns:
        df['enrollment_date'] = pd.to_datetime(df['enrollment_date'])
        
        # חילוץ מרכיבי תאריך
        df['enrollment_year'] = df['enrollment_date'].dt.year
        df['enrollment_month'] = df['enrollment_date'].dt.month
        df['enrollment_day_of_week'] = df['enrollment_date'].dt.day_name()
        
        # חישובי זמן
        df['days_since_enrollment'] = (pd.Timestamp.now() - df['enrollment_date']).dt.days
        df['years_since_enrollment'] = df['days_since_enrollment'] / 365.25
        
        # קיבוץ לפי תקופות
        enrollment_by_year = df.groupby('enrollment_year').size()
        enrollment_by_month = df.groupby(['enrollment_year', 'enrollment_month']).size()
        
        print("📅 רישום לפי שנים:")
        print(enrollment_by_year)
        
        return df
    else:
        print("⚠️ אין עמודת תאריך")
        return df

# שימוש:
df = datetime_operations(df)
```

### 5. עבודה עם מערכים מ-MongoDB
```python
def handle_mongodb_arrays(df):
    """טיפול במערכים שהגיעו מ-MongoDB"""
    
    if 'grades' in df.columns:
        # דרך 1: חישוב ממוצע למערך בכל שורה
        df['avg_grade'] = df['grades'].apply(
            lambda x: sum(x) / len(x) if isinstance(x, list) and x else None
        )
        
        # דרך 2: כמות הציונים
        df['grade_count'] = df['grades'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
        
        # דרך 3: הציון הגבוה ביותר
        df['max_grade'] = df['grades'].apply(
            lambda x: max(x) if isinstance(x, list) and x else None
        )
        
        # דרך 4: פירוק המערך לעמודות נפרדות (אם יש מספר קבוע)
        max_grades = df['grades'].apply(lambda x: len(x) if isinstance(x, list) else 0).max()
        if max_grades and max_grades <= 10:  # רק אם לא יותר מ-10 ציונים
            for i in range(max_grades):
                df[f'grade_{i+1}'] = df['grades'].apply(
                    lambda x: x[i] if isinstance(x, list) and len(x) > i else None
                )
        
        print("✅ עמודות חדשות נוצרו:")
        print(f"   avg_grade, grade_count, max_grade")
        if max_grades <= 10:
            print(f"   grade_1 עד grade_{max_grades}")
    
    return df

# שימוש:
df = handle_mongodb_arrays(df)
```

### 6. מיון ודירוג
```python
def sorting_and_ranking(df):
    """מיון ודירוג נתונים"""
    
    # מיון בסיסי
    top_students = df.nlargest(10, 'gpa')
    bottom_students = df.nsmallest(10, 'gpa')
    
    # מיון מורכב
    sorted_df = df.sort_values(['course', 'gpa'], ascending=[True, False])
    
    # דירוג
    df['gpa_rank'] = df['gpa'].rank(ascending=False, method='min')
    df['gpa_rank_by_course'] = df.groupby('course')['gpa'].rank(ascending=False, method='min')
    
    # אחוזונים
    df['gpa_percentile'] = df['gpa'].rank(pct=True) * 100
    
    # קטגוריות ביצועים
    df['performance_category'] = pd.cut(
        df['gpa'], 
        bins=[0, 2.0, 3.0, 3.5, 4.0], 
        labels=['נמוך', 'בינוני', 'טוב', 'מעולה']
    )
    
    print("🏆 10 הסטודנטים הטובים:")
    print(top_students[['name', 'course', 'gpa']].head())
    
    print(f"\n📊 התפלגות ביצועים:")
    print(df['performance_category'].value_counts())
    
    return df

# שימוש:
df = sorting_and_ranking(df)
```

### 7. יצירת דוחות מהירים
```python
def create_quick_reports(df):
    """יצירת דוחות מהירים למבחן"""
    
    print("=" * 60)
    print("📋 דוח מהיר - סטטיסטיקות סטודנטים")
    print("=" * 60)
    
    # 1. סיכום כללי
    print(f"\n📊 סיכום כללי:")
    print(f"   סה\"כ סטודנטים: {len(df):,}")
    print(f"   סטודנטים פעילים: {df['active'].sum():,}")
    print(f"   ממוצע GPA כללי: {df['gpa'].mean():.2f}")
    print(f"   גיל ממוצע: {df['age'].mean():.1f}")
    
    # 2. לפי קורסים
    print(f"\n📚 לפי קורסים:")
    course_stats = df.groupby('course').agg({
        'student_id': 'count',
        'gpa': 'mean',
        'active': 'sum'
    }).round(2)
    course_stats.columns = ['סטודנטים', 'ממוצע_GPA', 'פעילים']
    print(course_stats)
    
    # 3. התפלגות גילאים
    print(f"\n👥 התפלגות גילאים:")
    age_bins = pd.cut(df['age'], bins=[0, 20, 25, 30, 100], labels=['עד 20', '21-25', '26-30', '30+'])
    print(age_bins.value_counts())
    
    # 4. הישגים
    print(f"\n🎯 הישגים:")
    print(f"   GPA מעל 3.5: {(df['gpa'] > 3.5).sum()} סטודנטים")
    print(f"   GPA מתחת ל-2.0: {(df['gpa'] < 2.0).sum()} סטודנטים")
    
    # 5. סטודנטים מובילים
    print(f"\n🏆 5 הסטודנטים המובילים:")
    top_5 = df.nlargest(5, 'gpa')[['name', 'course', 'gpa']]
    for idx, row in top_5.iterrows():
        print(f"   {row['name']} ({row['course']}) - GPA: {row['gpa']}")
    
    print("=" * 60)

# שימוש:
create_quick_reports(df)
```

---

## טיפים למבחן

### 1. זרימת עבודה מומלצת
```python
def exam_workflow(connection_string, database_name, collection_name):
    """זרימת עבודה מלאה למבחן"""
    
    print("🚀 מתחיל זרימת עבודה למבחן...")
    
    # שלב 1: חיבור
    dal = AtlasDAL(connection_string, database_name)
    if not dal.connect():
        print("❌ חיבור נכשל!")
        return None
    
    # שלב 2: בדיקה ראשונית
    print("\n🔍 בדיקה ראשונית:")
    sample = dal.find_one_document(collection_name, {})
    if sample:
        print(f"   מבנה מסמך: {list(sample.keys())}")
        print(f"   דוגמה: {sample}")
    
    total_docs = dal.count_documents(collection_name)
    print(f"   סה\"כ מסמכים: {total_docs:,}")
    
    # שלב 3: טעינה חכמה
    if total_docs > 10000:
        print("\n📦 מערך נתונים גדול - טוען במנות...")
        all_data = paginate_collection(dal, collection_name, page_size=1000, max_pages=10)
    else:
        print("\n📦 טוען כל הנתונים...")
        all_data = dal.find_documents(collection_name)
    
    # שלב 4: המרה ל-Pandas
    print(f"\n🐼 יוצר DataFrame...")
    df = pd.DataFrame(all_data)
    
    # ניקוי אוטומטי
    df = df.dropna(how='all')  # הסרת שורות ריקות
    
    # זיהוי עמודות תאריך
    date_columns = []
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                date_columns.append(col)
            except:
                pass
    
    if date_columns:
        print(f"   זוהו עמודות תאריך: {date_columns}")
    
    # שלב 5: סקירה מהירה
    print(f"\n📊 DataFrame מוכן:")
    print(f"   גודל: {df.shape[0]:,} שורות, {df.shape[1]} עמודות")
    print(f"   עמודות: {list(df.columns)}")
    
    # ניתוק
    dal.disconnect()
    
    return df

# שימוש במבחן:
df = exam_workflow(
    "mongodb+srv://username:password@cluster.mongodb.net/",
    "exam_database",
    "exam_collection"
)

if df is not None:
    # המשך עם הניתוח...
    explore_dataframe(df)
    create_quick_reports(df)
```

### 2. פונקציות מהירות למבחן
```python
# מערך פונקציות מועילות למבחן
def quick_mongo_analysis(dal, collection_name):
    """ניתוח מהיר של קולקשן MongoDB"""
    
    # 1. מידע כללי
    total = dal.count_documents(collection_name)
    sample = dal.find_one_document(collection_name, {})
    
    print(f"📊 {collection_name}:")
    print(f"   מסמכים: {total:,}")
    print(f"   שדות: {list(sample.keys()) if sample else 'N/A'}")
    
    # 2. ערכים ייחודיים בשדות מפתח
    key_fields = ['status', 'type', 'category', 'active']
    for field in key_fields:
        if sample and field in sample:
            unique_vals = dal.get_distinct_values(collection_name, field)
            print(f"   {field}: {unique_vals}")
    
    return sample, total

def quick_pandas_summary(df, target_column=None):
    """סיכום מהיר של DataFrame"""
    
    print(f"📈 סיכום DataFrame:")
    print(f"   גודל: {df.shape}")
    print(f"   סוגי נתונים: {df.dtypes.value_counts().to_dict()}")
    
    if target_column and target_column in df.columns:
        print(f"\n🎯 ניתוח {target_column}:")
        if df[target_column].dtype in ['int64', 'float64']:
            print(f"   ממוצע: {df[target_column].mean():.2f}")
            print(f"   חציון: {df[target_column].median():.2f}")
            print(f"   טווח: {df[target_column].min():.2f} - {df[target_column].max():.2f}")
        else:
            print(f"   ערכים ייחודיים: {df[target_column].nunique()}")
            print(f"   השכיחים: {df[target_column].value_counts().head(3).to_dict()}")

# דוגמה למבחן:
sample, total = quick_mongo_analysis(dal, "students")
df = mongo_to_pandas(dal, "students")
quick_pandas_summary(df, "gpa")
```

### 3. תבניות שאילתות נפוצות למבחן
```python
# תבניות מוכנות לשאילתות נפוצות
COMMON_QUERIES = {
    "active_records": {"active": True},
    "recent_month": {"created_date": {"$gte": "2024-01-01"}},
    "high_value": {"amount": {"$gte": 1000}},
    "has_email": {"email": {"$exists": True}},
    "specific_categories": {"category": {"$in": ["A", "B", "C"]}},
    "text_search": {"name": {"$regex": "search_term", "$options": "i"}}
}

def run_common_query(dal, collection_name, query_name, **params):
    """הרצת שאילתה נפוצה עם פרמטרים"""
    
    query = COMMON_QUERIES.get(query_name, {}).copy()
    
    # התאמת פרמטרים
    for key, value in params.items():
        if key in query:
            query[key] = value
    
    results = dal.find_documents(collection_name, query)
    print(f"🔍 {query_name}: {len(results)} תוצאות")
    
    return results

# שימוש:
active_students = run_common_query(dal, "students", "active_records")
high_grades = run_common_query(dal, "students", "high_value", amount=85)  # מתאים ל-grade
```

---

## לסיכום - הרשימה החשובה למבחן

### ✅ סדר פעולות במבחן:
1. **חיבור ל-Atlas** → `AtlasDAL`
2. **בדיקה ראשונית** → `find_one_document()`
3. **טעינת נתונים** → `find_documents()` או `paginate_collection()`
4. **המרה ל-Pandas** → `pd.DataFrame()`
5. **ניתוח ועיבוד** → פעולות Pandas
6. **ניתוק** → `disconnect()`

### 🔧 פונקציות חובה לזכור:
```python
# MongoDB
dal.find_documents()          # טעינת מסמכים
dal.find_one_document()       # מסמך אחד
dal.count_documents()         # ספירה
dal.aggregate_data()          # אגרגציה

# Pandas
df.groupby().agg()           # קיבוץ וחישוב
df[df['column'] > value]     # סינון
df.sort_values()             # מיון
df.describe()                # סטטיסטיקות
```

### ⚠️ שגיאות להימנע מהן:
1. לא לבדוק את מבנה הנתונים קודם
2. לטעון יותר מדי נתונים בבת אחת
3. לשכוח לנקות ObjectId
4. לא לטפל בערכים חסרים
5. לשכוח ניתוק מהמסד

### 🚀 קוד מינימלי למבחן:
```python
# התחלה מהירה
dal = AtlasDAL("connection_string", "db_name")
dal.connect()

# בדיקה
sample = dal.find_one_document("collection", {})
print(sample)

# טעינה
data = dal.find_documents("collection", {"active": True})
df = pd.DataFrame(data)

# ניתוח בסיסי
print(df.describe())
print(df.groupby('category').size())

dal.disconnect()
```

עם המדריך הזה אתה מוכן לכל תרחיש במבחן! 🎯