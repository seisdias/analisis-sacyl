// web/assets/charts/utils/date.js


export const DAY = 24 * 60 * 60 * 1000;

export function toISODate(ts) {
  const x = new Date(ts);
  if (Number.isNaN(x.getTime())) return "";
  const yyyy = x.getFullYear();
  const mm = String(x.getMonth() + 1).padStart(2, "0");
  const dd = String(x.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function parseISODate(s) {
  if (!s) return null;
  const t = new Date(s + "T00:00:00").getTime();
  return Number.isNaN(t) ? null : t;
}