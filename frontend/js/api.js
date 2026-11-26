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

// Django Ninja 422: {"detail": [{"loc": ["body","payload","email"], "msg": "..."}]}
function parseValidationDetail(detail) {
  const fieldErrors = {};
  const general = [];
  if (!Array.isArray(detail)) return { fieldErrors, general };
  for (const item of detail) {
    const msg = item && typeof item.msg === "string" ? item.msg : null;
    if (!msg) continue;
    const loc = Array.isArray(item.loc) ? item.loc : [];
    const field = String(loc[loc.length - 1] ?? "");
    if (["name", "email", "phone", "consent"].includes(field)) {
      fieldErrors[field] = fieldErrors[field] || msg;
    } else {
      general.push(msg);
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
    const message = general.join(" ") || FALLBACK_MESSAGES[422];
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
