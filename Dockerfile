# استخدم صورة بايثون الرسمية كقاعدة
FROM python:3.9-slim

# غيّر مجلد العمل داخل الحاوية إلى /app
WORKDIR /app

# --- إضافة جديدة: ثبت أدوات الشبكات (بما في ذلك ping) ---
RUN apt-get update && apt-get install -y iputils-ping nmap

# انسخ ملف المتطلبات إلى الحاوية
COPY requirements.txt .

# ثبت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# انسخ كل ملفات المشروع إلى الحاوية
COPY . .

# الأمر الذي سيتم تشغيله عند بدء الحاوية
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


