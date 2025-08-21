import os
from .dal.data_access_layer import AnalyticsDAL

# 1. קריאת משתני סביבה במקום אחד מרכזי
# אם המשתנה לא קיים (למשל, בפיתוח מקומי), ניתן ערך ברירת מחדל מ-MongoDB Atlas
# החלף את הערך ב-Connection String שלך לפיתוח מקומי אם תרצה
MONGO_CONNECTION_STRING = os.getenv(
    "MONGO_CONNECTION_STRING",
    "mongodb+srv://<username>:<password>@<cluster-url>/...retryWrites=true&w=majority"
)

# 2. יצירת מופע יחיד (Singleton) של שכבת ה-DAL
# כל שאר חלקי האפליקציה ייבאו את המשתנה 'dal' הזה כדי לדבר עם מסד הנתונים
dal = AnalyticsDAL(connection_string=MONGO_CONNECTION_STRING)