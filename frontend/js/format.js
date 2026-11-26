export function formatDateTime(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("th-TH", { dateStyle: "long", timeStyle: "short" });
}

export function isPast(isoString) {
  const date = new Date(isoString);
  return !Number.isNaN(date.getTime()) && date.getTime() < Date.now();
}

// Returns null if the Event is open, otherwise a Thai reason.
export function closedReason(event) {
  if (isPast(event.starts_at)) return "Event ผ่านไปแล้ว";
  if (event.seats_remaining <= 0) return "ที่นั่งเต็ม";
  return null;
}
