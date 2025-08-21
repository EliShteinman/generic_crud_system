# Stage 1: Builder
FROM python:3.11-slim as builder

# הגדרת משתנים
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# התקנת תלויות מערכת
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# יצירת תיקיית עבודה
WORKDIR /app

# העתקת קובץ requirements
COPY requirements.txt .

# התקנת תלויות Python
RUN pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# הגדרת משתנים
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

# יצירת משתמש לא-root
RUN useradd -m -u 1001 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# העתקת תלויות מה-builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# הגדרת תיקיית עבודה
WORKDIR /app

# העתקת קוד האפליקציה
COPY --chown=appuser:appuser ./app ./app

# מעבר למשתמש לא-root
USER appuser

# חשיפת פורט
EXPOSE 8000

# פקודת הרצה
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]