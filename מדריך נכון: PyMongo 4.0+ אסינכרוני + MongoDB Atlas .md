# מדריך נכון: PyMongo 4.0+ אסינכרוני + MongoDB Atlas

## הערה חשובה!
**PyMongo 4.0+** כולל תמיכה אסינכרונית מובנית! 
**Motor יצא משימוש** - אל תשתמש בו!

---

## התקנה נכונה

```bash
# התקנה עם תמיכה ב-Atlas
pip install pymongo[srv] pandas asyncio

# אל תתקין motor!
```

---

## חיבור אסינכרוני נכון ל-MongoDB Atlas

### 1. חיבור אסינכרוני בסיסי

```python
import asyncio
import pandas as pd
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from typing import List, Dict, Any, Optional

class AsyncAtlasDAL:
    """DAL אסינכרוני ל-MongoDB Atlas עם PyMongo 4.0+"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[AsyncMongoClient] = None
        self.db = None
        self.connected = False
    
    async def connect(self) -> bool:
        """התחברות אסינכרונית ל-Atlas"""
        try:
            # PyMongo 4.0+ עם תמיכה אסינכרונית מובנית
            self.client = AsyncMongoClient(
                self.connection_string,
                server_api=ServerApi('1'),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50,
                retryWrites=True
            )
            
            # בדיקת חיבור אסינכרונית
            await self.client.admin.command('ping')
            print("✅ חיבור אסינכרוני ל-Atlas הצליח!")
            
            self.db = self.client[self.database_name]
            self.connected = True
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בחיבור אסינכרוני: {e}")
            return False
    
    async def disconnect(self):
        """ניתוק אסינכרוני"""
        if self.client:
            self.client.close()
            self.connected = False
            print("🔌 ניתוק אסינכרוני הושלם")
    
    def _ensure_connected(self):
        """בדיקה שיש חיבור"""
        if not self.connected:
            raise RuntimeError("DAL לא מחובר למסד נתונים")
    
    async def find_documents(self, collection_name: str,
                           query: Dict[str, Any] = None,
                           projection: Dict[str, int] = None,
                           sort: List[tuple] = None,
                           limit: int = None,
                           skip: int = 0) -> List[Dict[str, Any]]:
        """מציאת מסמכים אסינכרונית"""
        
        self._ensure_connected()
        collection = self.db[collection_name]
        
        # בניית cursor
        cursor = collection.find(query or {}, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        # איטרציה אסינכרונית על הcursor
        documents = []
        async for doc in cursor:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            documents.append(doc)
        
        return documents
    
    async def find_one_document(self, collection_name: str,
                              query: Dict[str, Any],
                              projection: Dict[str, int] = None) -> Optional[Dict[str, Any]]:
        """מציאת מסמך אחד אסינכרונית"""
        
        self._ensure_connected()
        collection = self.db[collection_name]
        
        doc = await collection.find_one(query, projection)
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        return doc
    
    async def count_documents(self, collection_name: str,
                            query: Dict[str, Any] = None) -> int:
        """ספירת מסמכים אסינכרונית"""
        
        self._ensure_connected()
        collection = self.db[collection_name]
        
        return await collection.count_documents(query or {})
    
    async def aggregate_data(self, collection_name: str,
                           pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """אגרגציה אסינכרונית"""
        
        self._ensure_connected()
        collection = self.db[collection_name]
        
        # cursor אגרגציה
        cursor = collection.aggregate(pipeline)
        
        # איטרציה אסינכרונית
        results = []
        async for doc in cursor:
            if '_id' in doc and doc['_id'] is not None:
                doc['_id'] = str(doc['_id'])
            results.append(doc)
        
        return results
    
    async def get_distinct_values(self, collection_name: str,
                                field: str,
                                query: Dict[str, Any] = None) -> List[Any]:
        """ערכים ייחודיים אסינכרוני"""
        
        self._ensure_connected()
        collection = self.db[collection_name]
        
        return await collection.distinct(field, query or {})

# דוגמה לשימוש:
async def main():
    dal = AsyncAtlasDAL(
        "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority",
        "school_db"
    )
    
    if await dal.connect():
        # עבודה עם הנתונים...
        students = await dal.find_documents("students", {"active": True})
        print(f"נמצאו {len(students)} סטודנטים פעילים")
        
        await dal.disconnect()

# הרצה
asyncio.run(main())
```

### 2. דיפדוף אסינכרוני נכון (40 מסמכים בכל פעם)

```python
async def paginate_async(dal: AsyncAtlasDAL, collection_name: str,
                        query: Dict = None, page_size: int = 40,
                        max_pages: int = None) -> List[Dict[str, Any]]:
    """דיפדוף אסינכרוני על מסמכים"""
    
    # ספירה כוללת
    total_docs = await dal.count_documents(collection_name, query)
    total_pages = (total_docs + page_size - 1) // page_size
    
    if max_pages:
        total_pages = min(total_pages, max_pages)
    
    print(f"📊 סה\"כ {total_docs} מסמכים, {total_pages} עמודים של {page_size}")
    
    all_data = []
    
    for page in range(total_pages):
        skip = page * page_size
        
        print(f"📄 טוען עמוד {page + 1}/{total_pages}...")
        
        # טעינה אסינכרונית של העמוד
        page_data = await dal.find_documents(
            collection_name,
            query=query,
            skip=skip,
            limit=page_size
        )
        
        all_data.extend(page_data)
        print(f"   ✅ נטענו {len(page_data)} מסמכים (סה\"כ: {len(all_data)})")
        
        # הפסקה קטנה (אופציונלי)
        await asyncio.sleep(0.1)
    
    return all_data

# שימוש:
async def load_all_students():
    dal = AsyncAtlasDAL("connection_string", "school_db")
    
    if await dal.connect():
        # טעינה של כל הסטודנטים, 40 בכל פעם
        all_students = await paginate_async(
            dal, 
            "students",
            query={"active": True},
            page_size=40,
            max_pages=10  # מקסימום 10 עמודים = 400 סטודנטים
        )
        
        print(f"🎓 נטענו סה\"כ {len(all_students)} סטודנטים")
        await dal.disconnect()
        
        return all_students

# הרצה
students = asyncio.run(load_all_students())
```

### 3. עיבוד אסינכרוני עם Pandas

```python
async def async_mongo_to_pandas(dal: AsyncAtlasDAL, 
                               collection_name: str,
                               query: Dict = None,
                               max_documents: int = 10000) -> pd.DataFrame:
    """המרה אסינכרונית של MongoDB ל-Pandas"""
    
    print("🔍 בודק גודל מערך הנתונים...")
    total_count = await dal.count_documents(collection_name, query)
    
    if total_count > max_documents:
        print(f"⚠️ מערך נתונים גדול ({total_count:,} מסמכים)")
        print(f"   טוען רק {max_documents:,} ראשונים...")
        
        documents = await dal.find_documents(
            collection_name,
            query=query,
            limit=max_documents
        )
    else:
        print(f"📦 טוען כל {total_count:,} המסמכים...")
        
        if total_count > 1000:
            # טעינה בדיפדוף
            documents = await paginate_async(dal, collection_name, query, page_size=50)
        else:
            # טעינה ישירה
            documents = await dal.find_documents(collection_name, query)
    
    if not documents:
        print("⚠️ לא נמצאו נתונים")
        return pd.DataFrame()
    
    # המרה ל-DataFrame
    df = pd.DataFrame(documents)
    
    # ניקוי בסיסי
    df = df.dropna(how='all')
    
    # זיהוי אוטומטי של עמודות תאריך
    date_columns = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                date_columns.append(col)
            except:
                pass
    
    if date_columns:
        print(f"📅 זוהו עמודות תאריך: {date_columns}")
    
    print(f"🐼 DataFrame מוכן: {len(df):,} שורות, {len(df.columns)} עמודות")
    print(f"📋 עמודות: {list(df.columns)}")
    
    return df

# שימוש:
async def analyze_students():
    dal = AsyncAtlasDAL("connection_string", "school_db")
    
    if await dal.connect():
        # המרה ל-DataFrame
        df = await async_mongo_to_pandas(
            dal, 
            "students",
            query={"active": True},
            max_documents=5000
        )
        
        await dal.disconnect()
        
        # עכשיו ניתוח ב-Pandas
        if not df.empty:
            print("\n📊 ניתוח בסיסי:")
            print(f"   ממוצע GPA: {df['gpa'].mean():.2f}")
            print(f"   התפלגות לפי קורס:")
            print(df['course'].value_counts())
        
        return df

# הרצה
df = asyncio.run(analyze_students())
```

### 4. אגרגציה אסינכרונית מתקדמת

```python
async def advanced_aggregation_async(dal: AsyncAtlasDAL, 
                                   collection_name: str,
                                   analysis_type: str = "summary") -> pd.DataFrame:
    """אגרגציה מתקדמת אסינכרונית"""
    
    if analysis_type == "grade_analysis":
        pipeline = [
            # סינון
            {"$match": {"active": True, "gpa": {"$exists": True}}},
            
            # קיבוץ לפי קורס
            {"$group": {
                "_id": "$course",
                "student_count": {"$sum": 1},
                "avg_gpa": {"$avg": "$gpa"},
                "min_gpa": {"$min": "$gpa"},
                "max_gpa": {"$max": "$gpa"},
                "gpa_std": {"$stdDevPop": "$gpa"},
                "students": {"$push": {
                    "name": "$name",
                    "gpa": "$gpa",
                    "year": "$year"
                }}
            }},
            
            # הוספת חישובים
            {"$addFields": {
                "gpa_range": {"$subtract": ["$max_gpa", "$min_gpa"]},
                "performance_category": {
                    "$switch": {
                        "branches": [
                            {"case": {"$gte": ["$avg_gpa", 3.5]}, "then": "מצוין"},
                            {"case": {"$gte": ["$avg_gpa", 3.0]}, "then": "טוב"},
                            {"case": {"$gte": ["$avg_gpa", 2.5]}, "then": "בינוני"}
                        ],
                        "default": "נמוך"
                    }
                }
            }},
            
            # מיון
            {"$sort": {"avg_gpa": -1}}
        ]
        
        print("🔄 מבצע אגרגציה אסינכרונית...")
        results = await dal.aggregate_data(collection_name, pipeline)
        
        # עיבוד התוצאות
        summary_data = []
        detailed_data = []
        
        for result in results:
            # נתוני סיכום
            summary_data.append({
                'course': result['_id'],
                'student_count': result['student_count'],
                'avg_gpa': round(result['avg_gpa'], 2),
                'min_gpa': result['min_gpa'],
                'max_gpa': result['max_gpa'],
                'gpa_std': round(result.get('gpa_std', 0), 2),
                'gpa_range': round(result['gpa_range'], 2),
                'performance_category': result['performance_category']
            })
            
            # נתונים מפורטים
            for student in result.get('students', []):
                detailed_data.append({
                    'course': result['_id'],
                    'name': student['name'],
                    'gpa': student['gpa'],
                    'year': student.get('year', 'N/A'),
                    'course_avg': result['avg_gpa']
                })
        
        summary_df = pd.DataFrame(summary_data)
        detailed_df = pd.DataFrame(detailed_data)
        
        if not summary_df.empty:
            print("\n📊 תוצאות אגרגציה:")
            print("=" * 50)
            
            for _, course in summary_df.iterrows():
                print(f"📚 {course['course']}:")
                print(f"   סטודנטים: {course['student_count']}")
                print(f"   ממוצע GPA: {course['avg_gpa']}")
                print(f"   טווח: {course['min_gpa']} - {course['max_gpa']}")
                print(f"   קטגוריה: {course['performance_category']}")
                print()
        
        return summary_df, detailed_df
    
    elif analysis_type == "time_series":
        # דוגמה לניתוח זמני
        pipeline = [
            {"$match": {"enrollment_date": {"$exists": True}}},
            
            {"$addFields": {
                "enrollment_month": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": {"$dateFromString": {"dateString": "$enrollment_date"}}
                    }
                }
            }},
            
            {"$group": {
                "_id": "$enrollment_month",
                "new_students": {"$sum": 1},
                "avg_gpa": {"$avg": "$gpa"}
            }},
            
            {"$sort": {"_id": 1}}
        ]
        
        results = await dal.aggregate_data(collection_name, pipeline)
        df = pd.DataFrame(results)
        
        if not df.empty:
            df['month'] = pd.to_datetime(df['_id'])
            df = df.drop('_id', axis=1).set_index('month')
            
            # חישוב מגמות
            df['enrollment_trend'] = df['new_students'].pct_change()
            df['enrollment_ma3'] = df['new_students'].rolling(window=3).mean()
            
            print("📈 ניתוח זמני - רישום סטודנטים:")
            print(f"   ממוצע רישומים חודשיים: {df['new_students'].mean():.1f}")
            print(f"   חודש שיא: {df['new_students'].idxmax().strftime('%Y-%m')} ({df['new_students'].max()} סטודנטים)")
            print(f"   מגמת צמיחה ממוצעת: {df['enrollment_trend'].mean()*100:.1f}%")
        
        return df

# שימוש:
async def full_analysis():
    dal = AsyncAtlasDAL("connection_string", "school_db")
    
    if await dal.connect():
        # ניתוח ציונים
        summary_df, detailed_df = await advanced_aggregation_async(
            dal, "students", "grade_analysis"
        )
        
        # ניתוח זמני
        time_df = await advanced_aggregation_async(
            dal, "students", "time_series"
        )
        
        await dal.disconnect()
        
        return summary_df, detailed_df, time_df

# הרצה
summary, detailed, time_series = asyncio.run(full_analysis())
```

---

## זרימת עבודה מלאה למבחן

```python
class ExamWorkflow:
    """זרימת עבודה מלאה למבחן עם PyMongo אסינכרוני"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.dal = AsyncAtlasDAL(connection_string, database_name)
    
    async def start_exam_analysis(self, collection_name: str) -> pd.DataFrame:
        """תהליך מלא לניתוח במבחן"""
        
        print("🚀 מתחיל ניתוח למבחן...")
        
        # שלב 1: חיבור
        if not await self.dal.connect():
            print("❌ נכשל בחיבור!")
            return pd.DataFrame()
        
        try:
            # שלב 2: בדיקה ראשונית
            print("\n🔍 בדיקה ראשונית:")
            sample = await self.dal.find_one_document(collection_name, {})
            if sample:
                print(f"   מבנה מסמך: {list(sample.keys())}")
                
            total_docs = await self.dal.count_documents(collection_name)
            print(f"   סה\"כ מסמכים: {total_docs:,}")
            
            # שלב 3: החלטה על אסטרטגיה
            if total_docs > 10000:
                print(f"\n📊 מערך נתונים גדול - משתמש באגרגציה")
                df = await self._large_dataset_strategy(collection_name)
            else:
                print(f"\n📦 מערך נתונים קטן - טוען הכל")
                df = await self._small_dataset_strategy(collection_name)
            
            # שלב 4: ניתוח מהיר
            if not df.empty:
                print(f"\n📋 ניתוח מהיר:")
                self._quick_analysis(df)
            
            return df
            
        finally:
            await self.dal.disconnect()
    
    async def _small_dataset_strategy(self, collection_name: str) -> pd.DataFrame:
        """אסטרטגיה למערך נתונים קטן"""
        
        documents = await self.dal.find_documents(collection_name)
        df = pd.DataFrame(documents)
        
        print(f"✅ נטען DataFrame עם {len(df)} שורות")
        return df
    
    async def _large_dataset_strategy(self, collection_name: str) -> pd.DataFrame:
        """אסטרטגיה למערך נתונים גדול"""
        
        # תחילה - סיכום עם אגרגציה
        pipeline = [
            {"$sample": {"size": 5000}},  # דגימה אקראית
            {"$project": {"_id": 0}}      # בלי ID
        ]
        
        sample_data = await self.dal.aggregate_data(collection_name, pipeline)
        df = pd.DataFrame(sample_data)
        
        print(f"✅ נטענה דגימה של {len(df)} שורות")
        return df
    
    def _quick_analysis(self, df: pd.DataFrame):
        """ניתוח מהיר של DataFrame"""
        
        print(f"   גודל: {df.shape[0]:,} שורות, {df.shape[1]} עמודות")
        
        # זיהוי עמודות מספריות
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            print(f"   עמודות מספריות: {numeric_cols}")
            for col in numeric_cols[:2]:  # רק 2 הראשונות
                mean_val = df[col].mean()
                print(f"      {col}: ממוצע = {mean_val:.2f}")
        
        # זיהוי עמודות טקסט
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        if text_cols:
            print(f"   עמודות טקסט: {text_cols}")
            for col in text_cols[:2]:  # רק 2 הראשונות
                unique_count = df[col].nunique()
                print(f"      {col}: {unique_count} ערכים ייחודיים")

# שימוש במבחן:
async def exam_analysis():
    workflow = ExamWorkflow(
        "mongodb+srv://username:password@cluster.mongodb.net/",
        "exam_database"
    )
    
    df = await workflow.start_exam_analysis("exam_collection")
    
    # המשך עם ניתוח ב-Pandas...
    if not df.empty:
        print("\n🐼 ניתוח Pandas:")
        print(df.describe())
        
        # דוגמה לקיבוץ
        if 'category' in df.columns:
            print(f"\nהתפלגות לפי קטגוריה:")
            print(df['category'].value_counts())
    
    return df

# הרצה
df = asyncio.run(exam_analysis())
```

---

## סיכום - הקוד החשוב למבחן

### ✅ תבנית מינימלית למבחן:

```python
import asyncio
import pandas as pd
from pymongo import AsyncMongoClient

async def exam_quick_start():
    # חיבור
    client = AsyncMongoClient("mongodb+srv://...")
    db = client["database_name"]
    collection = db["collection_name"]
    
    # בדיקה ראשונית
    sample = await collection.find_one()
    print(f"מבנה: {list(sample.keys())}")
    
    total = await collection.count_documents({})
    print(f"סה\"כ: {total}")
    
    # טעינה (40 בכל פעם)
    if total > 1000:
        # דיפדוף
        all_docs = []
        for skip in range(0, min(total, 2000), 40):  # מקסימום 2000
            cursor = collection.find({}).skip(skip).limit(40)
            batch = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                batch.append(doc)
            all_docs.extend(batch)
            print(f"טען {len(all_docs)} מתוך {total}")
    else:
        # הכל
        all_docs = []
        async for doc in collection.find({}):
            doc['_id'] = str(doc['_id'])
            all_docs.append(doc)
    
    # Pandas
    df = pd.DataFrame(all_docs)
    print(f"DataFrame: {df.shape}")
    
    # ניתוק
    client.close()
    
    return df

# הרצה
df = asyncio.run(exam_quick_start())
```

**עכשיו זה נכון! PyMongo 4.0+ אסינכרוני בלבד, בלי Motor!** 🎯