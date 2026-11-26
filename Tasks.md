# Tasks: Event Registration Website

อ้างอิงการตัดสินใจจาก [CONTEXT.md](./CONTEXT.md) และศัพท์จาก [GLOSSARY.md](./GLOSSARY.md)

สถานะ: `[x]` เสร็จแล้ว, `[ ]` ยังไม่ทำ

**ตรวจสอบล่าสุด (2026-11-25):** ยังไม่เริ่มกระบวนการ Dev โปรเจกต์มีเฉพาะเอกสาร (`GLOSSARY.md`, `CONTEXT.md`, `Tasks.md`) และโฟลเดอร์ config ของ Claude (`.claude/`, `.agents/`) ไม่มี `backend/`, `frontend/`, `docker-compose.yml`, `.env`, `.gitignore` หรือ `README.md` (ที่เคยสร้าง `backend/` ไว้ในเซสชันก่อนหน้าไม่อยู่บนดิสก์แล้ว จึงต้องเริ่มสร้างใหม่)

**ลำดับที่แนะนำ:** 0 (infra) → 1.1–1.4 (Backend) → 3.1 + 1.5 (tests) → 2 (Frontend) → 3.2–3.4 (QA) ถ้ามี git เพื่อป้องกันงานหายอีก ควร commit เป็นระยะ

**หมายเหตุ:** ใช้ Python ตาม `.agents/AGENTS.md` และ repo นี้ยังไม่มี `.gitignore` ของตัวเอง (git root อยู่ที่ระดับบน `~/Desktop`) ควรสร้างก่อนเริ่มเขียนโค้ด

## 0. Shared / Infrastructure

- [x] สร้าง `GLOSSARY.md` และ `CONTEXT.md`
- [x] สร้าง `docker-compose.yml` รัน PostgreSQL (volume, port 5432)
- [x] สร้าง `.env.example` (`POSTGRES_*`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `CORS_ALLOWED_ORIGINS`, `REGISTRATION_RATE_LIMIT`) และ copy เป็น `.env`
- [x] สร้าง `.gitignore` (`.env`, `backend/.venv`, `__pycache__`, `*.pyc`)
- [x] เขียน `README.md` วิธีรันในเครื่อง (compose up, migrate, createsuperuser, runserver, static server)

## 1. Backend (Django + Django Ninja)

### 1.1 โครงสร้างและ config
- [x] สร้าง `backend/` และ venv (`backend/.venv`)
- [x] ติดตั้งแพ็กเกจและบันทึก `requirements.txt`: `django`, `django-ninja`, `django-cors-headers`, `psycopg[binary]`, `pytest`, `pytest-django`, `python-dotenv`
- [x] สร้างโปรเจกต์ `config` และแอป `registration`
- [x] เขียน `settings.py` (PostgreSQL, CORS, อ่านค่าจาก `.env`, `TIME_ZONE`, `REGISTRATION_RATE_LIMIT`)

### 1.2 Models
- [x] `Event`: `name`, `starts_at`, `location`, `capacity`
- [x] `Registration`: `event` (FK), `name`, `email`, `phone`, `consent_at`, `status` (`confirmed`/`cancelled`), `created_at`
- [x] Unique constraint: 1 อีเมลต่อ Event เฉพาะ Registration ที่ `confirmed`
- [x] Property คำนวณ Seat คงเหลือ (นับเฉพาะ `confirmed`)
- [x] สร้างและรัน migrations

### 1.3 Django Admin
- [x] ลงทะเบียน `Event` (สร้าง/แก้ไข)
- [x] ลงทะเบียน `Registration` พร้อม filter ตาม Event/สถานะ และ action "Cancel selected registrations"

### 1.4 API (Django Ninja + Pydantic)
- [x] `GET /api/events` คืนรายการ Event พร้อม Seat คงเหลือ
- [x] `GET /api/events/{id}` คืนรายละเอียด Event (404 ถ้าไม่พบ)
- [x] `POST /api/events/{id}/registrations` รับ `name`, `email`, `phone`, `consent` แล้วคืน 201
  - [x] Pydantic schema ตรวจรูปแบบอีเมลและความยาวฟิลด์ (422)
  - [x] ปฏิเสธถ้า `consent` ไม่เป็น true (422)
  - [x] ปฏิเสธ Event ที่ผ่านวันจัดไปแล้ว (409)
  - [x] ปฏิเสธเมื่อที่นั่งเต็ม (409) โดยล็อกแถวด้วย `select_for_update` ใน transaction เพื่อกัน race condition
  - [x] ปฏิเสธอีเมลซ้ำใน Event เดียวกัน (409) และรองรับกรณีชนที่ constraint ของฐานข้อมูล
  - [x] บันทึก `consent_at` เป็นเวลาปัจจุบัน (ไม่เก็บ IP)
- [x] Rate limit ต่อ IP ที่ endpoint สมัคร (ค่าจาก `REGISTRATION_RATE_LIMIT`)
- [x] Honeypot field: ถ้ามีค่าให้ปฏิเสธโดยไม่บอกเหตุผลละเอียด
- [x] ผูก API เข้า `config/urls.py` พร้อม `/admin/`

### 1.5 Backend tests (`pytest` + `pytest-django`)
- [x] ตั้งค่า `pytest.ini` / `conftest.py`
- [ ] ดูหัวข้อ 3 (QA) สำหรับรายการเคสทดสอบ

## 2. Frontend (HTML/CSS/JS ล้วน)

- [x] สร้างโครง `frontend/` (`index.html`, `register.html`, `css/style.css`, `js/`)
- [x] `js/config.js`: ค่า API base URL (เช่น `http://localhost:8000/api`)
- [x] `js/api.js`: ฟังก์ชัน `fetch` เรียก 3 endpoint และจัดการรหัสข้อผิดพลาด
- [ ] หน้า 1 `index.html`: แสดงรายการ Event (ชื่อ, วันเวลา, สถานที่, Seat คงเหลือ) พร้อมลิงก์ไปสมัคร
  - [ ] สถานะกำลังโหลด, ข้อผิดพลาดเมื่อเรียก API ไม่ได้, กรณีไม่มี Event
  - [ ] Event ที่เต็มหรือผ่านไปแล้วปิดปุ่มสมัคร
- [ ] หน้า 2 `register.html?event=<id>`: ฟอร์ม `name`, `email`, `phone`, checkbox consent, honeypot field ที่ซ่อนด้วย CSS
  - [ ] ตรวจฟอร์มฝั่ง client ก่อนส่ง (ช่องว่าง, รูปแบบอีเมล, ต้องติ๊ก consent)
  - [ ] แสดงข้อความสำเร็จเมื่อได้ 201
  - [ ] แสดงข้อความตามรหัส 409 (เต็ม/สมัครซ้ำ/Event ผ่านไปแล้ว), 422, 404 และ 429 (ส่งถี่เกินไป)
  - [ ] ปิดปุ่มส่งระหว่างรอผลเพื่อกันกดซ้ำ
  - [ ] ใส่ข้อความ consent ที่ให้ฝ่ายกฎหมายหรือ DPO ตรวจก่อนใช้งานจริง
- [ ] CSS responsive พื้นฐาน (มือถือและเดสก์ท็อป) และ accessibility เบื้องต้น (label, focus, contrast)
- [x] ป้องกัน XSS: แสดงข้อมูลจาก API ด้วย `textContent` ไม่ใช้ `innerHTML`
- [x] เสิร์ฟด้วย static server (เช่น `python -m http.server 5500`) ให้ตรงกับ CORS origin

## 3. QA

### 3.1 Backend automated tests (`pytest`)
- [ ] สมัครสำเร็จ: ได้ 201, สร้าง Registration `confirmed`, Seat คงเหลือลดลง 1, มี `consent_at`
- [ ] ที่นั่งเต็ม: ได้ 409 และไม่สร้าง Registration
- [ ] ที่นั่งสุดท้ายถูกแย่งพร้อมกัน: สำเร็จเพียงรายการเดียว (ทดสอบ concurrency ด้วย transaction/thread)
- [ ] อีเมลซ้ำใน Event เดียวกัน: ได้ 409
- [ ] อีเมลเดียวกันสมัครคนละ Event: สำเร็จ
- [ ] Registration ที่ `cancelled` ไม่นับเป็น Seat และอีเมลเดิมสมัครใหม่ได้
- [ ] Event ที่ผ่านวันจัดไปแล้ว: ได้ 409
- [ ] ไม่ติ๊ก consent: ได้ 422
- [ ] ข้อมูลไม่ผ่านการตรวจ (อีเมลผิดรูปแบบ, ฟิลด์ว่าง, ฟิลด์ยาวเกิน): ได้ 422
- [ ] Event ไม่มีอยู่: ได้ 404 ทั้ง GET รายละเอียดและ POST
- [ ] Honeypot มีค่า: ปฏิเสธ
- [ ] Rate limit: ส่งเกินจำนวนที่กำหนดแล้วได้ 429
- [ ] `GET /api/events` แสดง Seat คงเหลือถูกต้อง

### 3.2 Frontend manual test
- [ ] รายการ Event แสดงถูกต้อง รวมถึงกรณีโหลด/ว่าง/Backend ล่ม
- [ ] สมัครสำเร็จตั้งแต่ต้นจนจบ แล้วตรวจข้อมูลใน Django Admin
- [ ] ทดสอบข้อความผิดพลาดทุกกรณี (409 เต็ม, 409 ซ้ำ, 409 ผ่านไปแล้ว, 422, 429)
- [ ] ตรวจ validation ฝั่ง client (consent ไม่ติ๊ก, อีเมลผิด)
- [ ] ทดสอบบน Chrome, Safari และหน้าจอมือถือ
- [ ] ตรวจ CORS: เรียกจาก origin ที่อนุญาตได้ และ origin อื่นถูกปฏิเสธ
- [ ] ตรวจว่ากดส่งซ้ำไม่สร้าง Registration ซ้ำ

### 3.3 Admin และข้อมูล
- [ ] Admin สร้าง Event และยกเลิก Registration ได้ และ Seat คืนกลับหลังยกเลิก
- [ ] ตรวจว่ามีเฉพาะฟิลด์ที่ตกลงกันเก็บในฐานข้อมูล (ไม่มี IP)
- [ ] ตรวจว่า `.env` ไม่ถูก commit และไม่มี secret ในโค้ด

### 3.4 เกณฑ์เสร็จ (Definition of Done)
- [ ] `pytest` ผ่านทั้งหมด
- [ ] ผ่าน manual test ใน 3.2 และ 3.3
- [ ] ทำตาม `README.md` แล้วรันได้ครบบนเครื่องใหม่
