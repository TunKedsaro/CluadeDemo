import { getEvent, createRegistration } from "./api.js";
import { formatDateTime, closedReason } from "./format.js";

const FIELDS = ["name", "email", "phone"];
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const eventInfoEl = document.getElementById("event-info");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const formEl = document.getElementById("register-form");
const submitEl = document.getElementById("submit-button");
const params = new URLSearchParams(window.location.search);
const eventId = params.get("event");

function showResult(text, isError) {
  resultEl.textContent = text;
  resultEl.hidden = text === "";
  resultEl.classList.toggle("message--error", isError);
  resultEl.classList.toggle("message--success", !isError);
}

function setFieldError(field, message) {
  const errorEl = document.getElementById(`${field}-error`);
  const input = document.getElementById(field);
  errorEl.textContent = message;
  if (message) input.setAttribute("aria-invalid", "true");
  else input.removeAttribute("aria-invalid");
}

function clearErrors() {
  [...FIELDS, "consent"].forEach((field) => setFieldError(field, ""));
  showResult("", false);
}

function validate(values) {
  const errors = {};
  if (!values.name) errors.name = "กรุณากรอกชื่อ";
  if (!values.email) errors.email = "กรุณากรอกอีเมล";
  else if (!EMAIL_PATTERN.test(values.email)) errors.email = "รูปแบบอีเมลไม่ถูกต้อง";
  if (!values.phone) errors.phone = "กรุณากรอกเบอร์โทรศัพท์";
  if (!values.consent) errors.consent = "กรุณาให้ความยินยอมก่อนสมัคร";
  return errors;
}

function applyFieldErrors(errors) {
  Object.entries(errors).forEach(([field, message]) => setFieldError(field, message));
  const firstInvalid = formEl.querySelector("[aria-invalid='true']");
  if (firstInvalid) firstInvalid.focus();
}

function renderEvent(event) {
  const lines = [
    ["วันเวลา", formatDateTime(event.starts_at)],
    ["สถานที่", event.location],
    ["Seat คงเหลือ", `${event.seats_remaining} / ${event.capacity}`],
  ];
  const title = document.createElement("h2");
  title.textContent = event.name;
  const rows = lines.map(([label, value]) => {
    const p = document.createElement("p");
    p.className = "event-card__row";
    const strong = document.createElement("strong");
    strong.textContent = `${label}: `;
    p.append(strong, document.createTextNode(value));
    return p;
  });
  eventInfoEl.replaceChildren(title, ...rows);
  eventInfoEl.hidden = false;
}

function showFatal(text) {
  statusEl.textContent = text;
  statusEl.hidden = false;
  statusEl.classList.add("message--error");
  formEl.hidden = true;
}

function readValues() {
  return {
    name: formEl.elements.name.value.trim(),
    email: formEl.elements.email.value.trim(),
    phone: formEl.elements.phone.value.trim(),
    consent: formEl.elements.consent.checked,
    website: formEl.elements.website.value,
  };
}

function handleSubmitError(error) {
  if (error.status === 422) {
    applyFieldErrors(error.fieldErrors);
    if (Object.keys(error.fieldErrors).length === 0) showResult(error.message, true);
    else showResult("ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบช่องที่มีเครื่องหมายแจ้งเตือน", true);
    return;
  }
  if (error.status === 404) {
    showFatal("ไม่พบ Event ที่ต้องการ");
    return;
  }
  showResult(error.message || "เกิดข้อผิดพลาด กรุณาลองใหม่", true);
}

async function onSubmit(submitEvent) {
  submitEvent.preventDefault();
  if (submitEl.disabled) return;
  clearErrors();

  const values = readValues();
  const errors = validate(values);
  if (Object.keys(errors).length > 0) {
    applyFieldErrors(errors);
    return;
  }

  submitEl.disabled = true;
  submitEl.textContent = "กำลังส่ง...";
  formEl.setAttribute("aria-busy", "true");
  try {
    await createRegistration(eventId, values);
    formEl.reset();
    formEl.hidden = true;
    showResult("สมัครสำเร็จแล้ว ขอบคุณที่ลงทะเบียนเข้าร่วม Event", false);
  } catch (error) {
    handleSubmitError(error);
    submitEl.disabled = false;
  } finally {
    submitEl.textContent = "ส่งใบสมัคร";
    formEl.removeAttribute("aria-busy");
  }
}

async function init() {
  if (!eventId || !/^\d+$/.test(eventId)) {
    showFatal("ไม่พบ Event ที่ต้องการ (ลิงก์ไม่ถูกต้อง)");
    return;
  }
  statusEl.textContent = "กำลังโหลดข้อมูล Event...";
  statusEl.hidden = false;
  try {
    const event = await getEvent(eventId);
    renderEvent(event);
    statusEl.hidden = true;
    const reason = closedReason(event);
    if (reason) {
      showFatal(`ไม่สามารถสมัครได้: ${reason}`);
      return;
    }
    formEl.hidden = false;
    formEl.addEventListener("submit", onSubmit);
  } catch (error) {
    const message = error && error.status === 404 ? "ไม่พบ Event ที่ต้องการ" : (error && error.kind ? error.message : "เซิร์ฟเวอร์ตอบกลับผิดปกติ");
    showFatal(message);
  }
}

init();
