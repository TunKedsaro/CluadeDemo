import { listEvents } from "./api.js";
import { formatDateTime, closedReason } from "./format.js";

const listEl = document.getElementById("event-list");
const statusEl = document.getElementById("status");

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.hidden = text === "";
  statusEl.classList.toggle("message--error", isError);
}

function addRow(parent, label, value) {
  const row = document.createElement("p");
  row.className = "event-card__row";
  const strong = document.createElement("strong");
  strong.textContent = `${label}: `;
  row.append(strong, document.createTextNode(value));
  parent.append(row);
}

function buildCard(event) {
  const card = document.createElement("li");
  card.className = "card event-card";

  const title = document.createElement("h2");
  title.className = "event-card__title";
  title.textContent = event.name;
  card.append(title);

  addRow(card, "วันเวลา", formatDateTime(event.starts_at));
  addRow(card, "สถานที่", event.location);
  addRow(card, "Seat คงเหลือ", `${event.seats_remaining} / ${event.capacity}`);

  const reason = closedReason(event);
  if (reason) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "button";
    button.disabled = true;
    button.textContent = `สมัครไม่ได้ (${reason})`;
    card.append(button);
  } else {
    const link = document.createElement("a");
    link.className = "button button--primary";
    link.href = `register.html?event=${encodeURIComponent(event.id)}`;
    link.textContent = "สมัครเข้าร่วม";
    card.append(link);
  }
  return card;
}

async function init() {
  setStatus("กำลังโหลดรายการ Event...");
  listEl.setAttribute("aria-busy", "true");
  try {
    const events = await listEvents();
    if (!Array.isArray(events)) throw new Error("invalid");
    listEl.replaceChildren(...events.map(buildCard));
    setStatus(events.length === 0 ? "ยังไม่มี Event ในขณะนี้" : "");
  } catch (error) {
    const message = error && error.kind ? error.message : "เซิร์ฟเวอร์ตอบกลับผิดปกติ";
    setStatus(`โหลดรายการ Event ไม่สำเร็จ: ${message}`, true);
  } finally {
    listEl.removeAttribute("aria-busy");
  }
}

init();
