import { API_BASE_URL } from "./config.js";

export class ApiError extends Error {
  constructor(kind, message, status = null, fieldErrors = {}) {
    super(message);
    this.kind = kind; // "network" | "server" | "http"
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

const FALLBACK_MESSAGES = {
  404: "ไม่พบ Event ที่ต้องการ",
  409: "ไม่สามารถสมัครได้ในขณะนี้",
  422: "ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง",
  429: "ส่งคำขอถี่เกินไป กรุณารอสักครู่แล้วลองใหม่",
};

const FIELD_LABELS = { name: "ชื่อ", email: "อีเมล", phone: "เบอร์โทรศัพท์", consent: "ความยินยอม" };
const LIMIT_TEXT = { name: "100 ตัวอักษร", email: "254 ตัวอักษร", phone: "20 ตัวอักษร" };

// Translate Pydantic error (English msg) into Thai text per field.
function translateValidationItem(field, item) {
  const type = String(item.type || "");
  const label = FIELD_LABELS[field] || "ข้อมูล";
  if (type === "missing") return `กรุณากรอก${label}`;
  if (type === "string_too_short") {
    return field === "phone" ? "เบอร์โทรศัพท์สั้นเกินไป (อย่างน้อย 6 ตัวอักษร)" : `กรุณากรอก${label}`;
  }
  if (type === "string_too_long") return `${label}ยาวเกินกำหนด (ไม่เกิน ${LIMIT_TEXT[field] || "ที่กำหนด"})`;
  if (type === "string_pattern_mismatch") {
    return field === "phone" ? "เบอร์โทรศัพท์ใช้ได้เฉพาะตัวเลข + - ( ) และช่องว่าง" : `รูปแบบ${label}ไม่ถูกต้อง`;
  }
  if (field === "email") return "อีเมลไม่ถูกต้อง หรือโดเมนอีเมลไม่รองรับ";
  if (field === "consent") return "กรุณาให้ความยินยอมก่อนสมัคร";
  return `${label}ไม่ถูกต้อง`;
}

// Django Ninja 422: {"detail": [{"loc": ["body","payload","email"], "msg": "..."}]}
function parseValidationDetail(detail) {
  const fieldErrors = {};
  const general = [];
  if (!Array.isArray(detail)) return { fieldErrors, general };
  for (const item of detail) {
    if (!item || typeof item !== "object") continue;
    const loc = Array.isArray(item.loc) ? item.loc : [];
    const field = String(loc[loc.length - 1] ?? "");
    if (["name", "email", "phone", "consent"].includes(field)) {
      fieldErrors[field] = fieldErrors[field] || translateValidationItem(field, item);
    } else {
      general.push(FALLBACK_MESSAGES[422]);
    }
  }
  return { fieldErrors, general };
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
  } catch {
    throw new ApiError("network", "เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาตรวจสอบอินเทอร์เน็ตแล้วลองใหม่");
  }

  const body = await readJson(response);

  if (response.ok) {
    if (response.status === 204) return null;
    if (body === null) {
      throw new ApiError("server", "เซิร์ฟเวอร์ตอบกลับผิดปกติ", response.status);
    }
    return body;
  }

  if (response.status === 422) {
    const { fieldErrors, general } = parseValidationDetail(body && body.detail);
    const message = general[0] || FALLBACK_MESSAGES[422];
    throw new ApiError("http", message, 422, fieldErrors);
  }

  if ([404, 409, 429].includes(response.status)) {
    const detail = body && typeof body.detail === "string" ? body.detail : null;
    throw new ApiError("http", detail || FALLBACK_MESSAGES[response.status], response.status);
  }

  throw new ApiError("server", "เซิร์ฟเวอร์ขัดข้อง กรุณาลองใหม่ภายหลัง", response.status);
}

export function listEvents() {
  return request("/events");
}

export function getEvent(id) {
  return request(`/events/${encodeURIComponent(id)}`);
}

export function createRegistration(eventId, payload) {
  return request(`/events/${encodeURIComponent(eventId)}/registrations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
