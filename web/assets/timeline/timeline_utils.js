// web/assets/timeline/timeline_utils.js

export function safeParseTs(dateStr) {
  // Esperamos "YYYY-MM-DD" desde backend
  if (!dateStr) return null;
  const t = new Date(dateStr + "T00:00:00").getTime();
  return Number.isNaN(t) ? null : t;
}

export function uniqByKey(items, keyFn) {
  const seen = new Set();
  const out = [];
  for (const it of items) {
    const k = keyFn(it);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(it);
  }
  return out;
}