# Event Registration Website

เว็บไซต์ลงทะเบียนเข้าร่วม Event แยก Frontend (HTML/CSS/JS ล้วน) กับ Backend (Django + Django Ninja + PostgreSQL)
ดูการตัดสินใจใน [CONTEXT.md](./CONTEXT.md), ศัพท์ใน [GLOSSARY.md](./GLOSSARY.md), งานใน [Tasks.md](./Tasks.md)

## ข้อกำหนดเบื้องต้น
- Python 3.12+ และ Docker (Docker Desktop ต้องเปิดอยู่)

## วิธีรันในเครื่อง

```bash
# 1) ตั้งค่า environment (แก้ค่า password / secret ใน .env ก่อนใช้งาน ห้าม commit .env)
cp .env.example .env

# 2) เริ่มฐานข้อมูล PostgreSQL
docker compose up -d

# 3) ติดตั้ง Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4) สร้างตาราง และบัญชี Admin
python manage.py migrate
python manage.py createsuperuser

# 5) รัน Backend ที่ http://localhost:8000
python manage.py runserver
```

เปิดอีก terminal เพื่อเสิร์ฟ Frontend แบบ static (origin ต้องตรงกับ `CORS_ALLOWED_ORIGINS`):

```bash
cd frontend
python3 -m http.server 5500
```

- Frontend: http://localhost:5500
- Django Admin (สร้าง Event, ยกเลิก Registration): http://localhost:8000/admin/
- API docs: http://localhost:8000/api/docs

## ทดสอบ

```bash
cd backend
pytest
```

Test ต้องใช้ PostgreSQL ที่รันอยู่ (มี concurrency test ที่ใช้ row lock)

## หมายเหตุ
- ถ้า port 5432 ถูกใช้อยู่ ให้ตั้ง `POSTGRES_PORT` ใน `.env` เป็นพอร์ตอื่น (เช่น 5433)
- `COMPOSE_PROJECT_NAME` ใน `.env` กำหนดชื่อ project/volume ของ docker compose
- `REGISTRATION_RATE_LIMIT` รูปแบบ `<จำนวน>/<s|m|h>` (ต่อ IP, เก็บใน cache ของ process ใช้สำหรับรันในเครื่อง)
- ข้อความ consent ควรให้ฝ่ายกฎหมายหรือ DPO ตรวจก่อนใช้งานจริง
