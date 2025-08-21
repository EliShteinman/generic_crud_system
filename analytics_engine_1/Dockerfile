# שלב 1: בניית הסביבה
FROM python:3.11-slim as builder

# הגדרת משתני סביבה
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# יצירת משתמש שאינו root
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser

# התקנת תלויות
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# שלב 2: בניית האימג' הסופי
FROM python:3.11-slim

# שימוש באותו משתמש
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser

# העתקת התלויות שהותקנו בשלב הקודם
COPY --from=builder /home/appuser/.local /home/appuser/.local

# העתקת קוד המקור של האפליקציה
COPY --chown=appuser:appuser ./app ./app

# הגדרת ה-PATH כדי שהמערכת תמצא את החבילות המותקנות
ENV PATH="/home/appuser/.local/bin:${PATH}"

# חשיפת הפורט
EXPOSE 8080

# פקודת ההרצה
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]