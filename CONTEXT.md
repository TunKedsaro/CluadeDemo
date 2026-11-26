# CONTEXT: Event Registration Website

เอกสารนี้บันทึกผลการ grill session และการตัดสินใจทั้งหมด (ยืนยันโดยผู้ใช้แล้ว)
ศัพท์เฉพาะของโดเมนอยู่ใน [GLOSSARY.md](./GLOSSARY.md)

## เป้าหมาย

เว็บไซต์ลงทะเบียนเข้าร่วม Event โดยแยก Frontend และ Backend ออกจากกัน

## การตัดสินใจ

### โดเมน
- "Registration" = ลงทะเบียนเข้าร่วมอีเวนต์หรือคอร์ส ใช้คำเดียวว่า **Event**
- ผู้ใช้มี 2 กลุ่ม คือ **Attendee** (สมัคร) และ **Admin** (จัดการ)
- มีหลาย Event ได้ Attendee สมัครได้ทีละ Event
- 1 อีเมลสมัครได้ 1 ครั้งต่อ Event (สมัครคนละ Event ได้)
- สถานะ Registration มี `confirmed` (นับเป็น Seat) กับ `cancelled` (ไม่นับ)
- Attendee ยกเลิกเองไม่ได้ Admin ยกเลิกได้
- ที่นั่งเต็มให้ปฏิเสธ (409) ไม่มี waitlist และต้องกัน race condition ที่ที่นั่งสุดท้ายด้วยการล็อกแถวในฐานข้อมูล
- Event ที่ผ่านวันจัดไปแล้วปฏิเสธการสมัคร (409)

### ข้อมูลและ PDPA
- เก็บเฉพาะ `name`, `email`, `phone` และ `consent_at` (timestamp ไม่เก็บ IP)
- ปฏิเสธการสมัครถ้าไม่ติ๊ก consent
- ยังไม่ทำการยืนยันอีเมลและหน้านโยบายความเป็นส่วนตัวในเวอร์ชันแรก
- ข้อความ consent ควรให้ฝ่ายกฎหมายหรือ DPO ตรวจก่อนใช้งานจริง

### เทคโนโลยี
- Backend: Python, Django, **Django Ninja** (ใช้ Pydantic), `django-cors-headers`
- Frontend: HTML/CSS/JS ล้วน ไม่มี build tool เรียก API ด้วย `fetch`
- ฐานข้อมูล: PostgreSQL (รันด้วย Docker Compose ตอนพัฒนา)
- ทดสอบ: Backend ใช้ `pytest` (+ `pytest-django`) Frontend ทดสอบด้วยมือ
- Admin: ใช้ Django Admin ที่มีมากับ Django ไม่ทำหน้า Admin ใน Frontend

### โครงสร้าง (monorepo)
```
ClaudeDemo/
├── backend/            Django + Django Ninja
├── frontend/           HTML/CSS/JS
├── docker-compose.yml  PostgreSQL
├── .env                รหัสผ่าน (ไม่ commit)
├── GLOSSARY.md
└── CONTEXT.md
```

### API
| Method | Path | ผลลัพธ์ |
|---|---|---|
| GET | `/api/events` | รายการ Event พร้อม Seat คงเหลือ |
| GET | `/api/events/{id}` | รายละเอียด Event |
| POST | `/api/events/{id}/registrations` | รับ `name`, `email`, `phone`, `consent` แล้วคืน 201 |

รหัสข้อผิดพลาด
- 404: ไม่พบ Event
- 409: ที่นั่งเต็ม, อีเมลสมัครซ้ำใน Event เดียวกัน หรือ Event ผ่านไปแล้ว
- 422: ข้อมูลไม่ผ่านการตรวจ

### Frontend
- หน้า 1: รายการ Event พร้อม Seat คงเหลือ
- หน้า 2: ฟอร์มสมัครพร้อมช่อง consent แสดงผลสำเร็จหรือข้อผิดพลาด
- เสิร์ฟเป็น static แยกจาก Backend (เช่น `python -m http.server`)

### ความปลอดภัย
- rate limit ต่อ IP และ honeypot field ในฟอร์ม ยังไม่ใช้ CAPTCHA (เพิ่มภายหลังถ้าพบปัญหาจริง)
- CORS อนุญาตเฉพาะ origin ของ Frontend
- รหัสผ่านอยู่ใน `.env` ที่ไม่ commit

### ขอบเขตเวอร์ชันแรก
- รันในเครื่องเท่านั้นด้วย Docker Compose (PostgreSQL) และ `runserver`
- ยังไม่วางแผน deploy

## ADR
ยังไม่มี เพราะการตัดสินใจทั้งหมดไม่เข้าเกณฑ์ครบทั้งสามข้อ (ย้อนกลับยาก, น่าแปลกใจถ้าไม่มีบริบท, เป็น trade-off จริง)

## สถานะการลงมือ (ณ 2026-11-25)

ตรวจสอบแล้ว: ยังไม่เริ่ม Dev

เสร็จแล้ว
- `GLOSSARY.md`, `CONTEXT.md`, `Tasks.md`

ยังไม่ได้ทำ (ทุกอย่างในโค้ด)
- `backend/` ทั้งหมด (ที่เคยสร้างไว้ไม่อยู่บนดิสก์แล้ว ต้องสร้างใหม่)
- `frontend/`
- `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`

รายละเอียดงานอยู่ใน [Tasks.md](./Tasks.md)
