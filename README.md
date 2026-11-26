# Event Registration Website

เว็บไซต์ลงทะเบียนเข้าร่วม Event แยก Frontend (HTML/CSS/JS ล้วน) กับ Backend (Django + Django Ninja + PostgreSQL)
ดูการตัดสินใจใน [CONTEXT.md](./CONTEXT.md), ศัพท์ใน [GLOSSARY.md](./GLOSSARY.md), งานใน [Tasks.md](./Tasks.md)

## เริ่มเร็ว (Docker คำสั่งเดียว)

ต้องมี Docker (Docker Desktop ต้องเปิดอยู่) ไม่ต้องมี `.env` ไม่ต้องติดตั้ง Python

```bash
docker compose up -d --build
```

รอประมาณ 30 วินาที (สร้าง image, migrate, สร้างบัญชี Admin และ Event ตัวอย่างให้อัตโนมัติ) แล้วเปิด

- เว็บสมัคร: http://localhost:5500
- Django Admin: http://localhost:8000/admin/
- API docs: http://localhost:8000/api/docs

**บัญชี Admin สำหรับ dev:** username `admin` / password `admin12345`
ค่านี้เป็นค่าเริ่มต้นสำหรับเครื่อง dev เท่านั้น **ห้ามใช้จริง** ถ้าจะเปลี่ยน ให้ตั้ง `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD` ใน `.env` ก่อนรันครั้งแรก
(บัญชีถูกสร้างเมื่อยังไม่มี username นั้นเท่านั้น การเปลี่ยนค่าทีหลังไม่แก้รหัสผ่านของบัญชีเดิม)

Event ตัวอย่าง 4 รายการ (รวม 1 รายการที่นั่งเหลือ 3) ถูกสร้างจาก `seed_demo_events` ซึ่งทำซ้ำได้ ไม่สร้างซ้ำ ถ้าไม่ต้องการ ตั้ง `SEED_DEMO_DATA=false`

```bash
docker compose logs -f backend      # ดู log (หรือ frontend / db)
docker compose ps                   # ดูสถานะ
docker compose stop                 # หยุด (ข้อมูลยังอยู่)
docker compose down                 # ลบ container (ข้อมูลใน volume ยังอยู่)
docker compose down -v              # ลบ container และ volume = ข้อมูลฐานข้อมูลหายทั้งหมด
```

เปลี่ยนพอร์ตผ่าน environment หรือ `.env` (ค่าเริ่มต้น `POSTGRES_PORT=5432`, `BACKEND_PORT=8000`, `FRONTEND_PORT=5500`):

```bash
BACKEND_PORT=8601 FRONTEND_PORT=5602 docker compose up -d --build
```

`CORS_ALLOWED_ORIGINS` และ `API_BASE_URL` ของ frontend ปรับตามพอร์ตให้อัตโนมัติ ไม่ต้องแก้โค้ด (ถ้าตั้ง `CORS_ALLOWED_ORIGINS` ใน `.env` เอง ต้องให้ตรงกับ `FRONTEND_PORT`) PostgreSQL เปิดพอร์ตที่ `127.0.0.1` เท่านั้น

หมายเหตุ Docker
- Backend รันด้วย gunicorn **1 worker + หลาย thread** เพราะ rate limit เก็บใน memory ของ process ถ้าเพิ่ม worker ตัวนับจะแยกกันและ limit หลวมลง
- ตั้ง `POSTGRES_PASSWORD` **ก่อน** รันครั้งแรก เพราะ volume จำรหัสผ่านแรกไว้
- แก้โค้ด backend/frontend แล้วต้อง `docker compose up -d --build` ใหม่

## ข้อกำหนดเบื้องต้น
- Python 3.12+ และ Docker (Docker Desktop ต้องเปิดอยู่)

## รันแบบพัฒนาในเครื่อง (venv)

วิธีนี้รันเฉพาะ DB ใน Docker (`docker compose up -d db`) ส่วน backend/frontend รันเอง
ถ้าชนกับ stack ด้านบน ให้ `docker compose down` ก่อน หรือเปลี่ยนพอร์ต

```bash
# 1) ตั้งค่า environment (แก้ POSTGRES_PASSWORD และ DJANGO_SECRET_KEY ใน .env ก่อนใช้งาน ห้าม commit .env)
cp .env.example .env

# 2) เริ่มฐานข้อมูล PostgreSQL
docker compose up -d db

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

## สร้าง Event แรกและลองสมัคร

แบบ venv ฐานข้อมูลใหม่ยังไม่มี Event หน้าเว็บจะว่างจนกว่าจะสร้าง (หรือรัน `python manage.py seed_demo_events`)

1. เปิด http://localhost:8000/admin/ แล้ว login ด้วยบัญชีที่สร้างจาก `createsuperuser`
2. เพิ่ม **Event** (ชื่อ, วันเวลาจัดในอนาคต, สถานที่, จำนวนที่นั่ง)
3. เปิด http://localhost:5500 แล้วกดสมัคร หรือทดสอบด้วย curl:

```bash
curl http://localhost:8000/api/events

curl -X POST http://localhost:8000/api/events/1/registrations \
  -H "Content-Type: application/json" \
  -d '{"name":"สมชาย ใจดี","email":"somchai@example.com","phone":"0812345678","consent":true,"website":""}'
```

ถ้าสมัครสำเร็จได้ `201` ส่งอีเมลเดิมซ้ำได้ `409` ถ้าไม่ติ๊ก consent หรือข้อมูลไม่ผ่านการตรวจได้ `422`

## ทดสอบ

```bash
cd backend
pytest
```

Test ต้องใช้ PostgreSQL ที่รันอยู่ (มี concurrency test ที่ใช้ row lock)

## หมายเหตุ
- ตั้ง `POSTGRES_PASSWORD` ใน `.env` **ก่อน** รัน `docker compose up` ครั้งแรก เพราะ volume จะจำรหัสผ่านแรกไว้ ถ้าแก้ภายหลังจะ login ฐานข้อมูลไม่ได้ (ต้องลบ volume ซึ่งลบข้อมูลทั้งหมด)
- ถ้า port 5432 ถูกใช้อยู่ ให้ตั้ง `POSTGRES_PORT` ใน `.env` เป็นพอร์ตอื่น (เช่น 5433)
- `COMPOSE_PROJECT_NAME` ใน `.env` กำหนดชื่อ project, volume และชื่อ container (`<ชื่อ>-db`) ถ้าจะรันอีกชุดในเครื่องเดียวกัน ให้ตั้งชื่อต่างกันและใช้พอร์ตต่างกัน
- ถ้ารันแบบ venv แล้วเปลี่ยนพอร์ต Backend จาก 8000 ต้องแก้ `API_BASE_URL` ใน `frontend/js/config.js` ให้ตรงด้วย (ใน Docker ไฟล์นี้ถูกสร้างใหม่จาก env ตอนสตาร์ต) และถ้าเปลี่ยนพอร์ต Frontend จาก 5500 ต้องแก้ `CORS_ALLOWED_ORIGINS` ใน `.env`
- `REGISTRATION_RATE_LIMIT` รูปแบบ `<จำนวน>/<s|m|h>` (ต่อ IP, เก็บใน cache ของ process ใช้สำหรับรันในเครื่อง)
- ข้อความ consent ควรให้ฝ่ายกฎหมายหรือ DPO ตรวจก่อนใช้งานจริง
