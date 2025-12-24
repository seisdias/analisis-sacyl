// web/assets/chart_utils.js

// -----------------------------
// Helpers
// -----------------------------

const DAY = 24 * 60 * 60 * 1000;

export function outOfRangeFlag(value, low, high) {
  if (low != null && value < low) return "below";
  if (high != null && value > high) return "above";
  return null;
}

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

export function extentTs(flat) {
  if (!flat || flat.length === 0) return { minTs: null, maxTs: null };
  const minTs = new Date(flat[0][0]).getTime();
  const maxTs = new Date(flat[flat.length - 1][0]).getTime();
  if (Number.isNaN(minTs) || Number.isNaN(maxTs)) return { minTs: null, maxTs: null };
  return { minTs, maxTs };
}

export function pctToTs(pct, minTs, maxTs) {
  if (minTs == null || maxTs == null) return null;
  return minTs + (maxTs - minTs) * (pct / 100);
}

export function tsToPct(ts, minTs, maxTs) {
  if (ts == null || minTs == null || maxTs == null) return 0;
  if (maxTs === minTs) return 0;
  const p = ((ts - minTs) / (maxTs - minTs)) * 100;
  return Math.max(0, Math.min(100, p));
}

export function percentToDate(flat, pct) {
  if (!flat || flat.length === 0) return null;
  const first = new Date(flat[0][0]).getTime();
  const last = new Date(flat[flat.length - 1][0]).getTime();
  if (Number.isNaN(first) || Number.isNaN(last)) return null;
  return first + (last - first) * (pct / 100);
}

export function buildTreatmentIntervals(timeline) {
  const out = [];
  if (!timeline) return out;

  const defaultDays = timeline.config?.treatment_default_days ?? null;

  for (const t of (timeline.treatments || [])) {
    const start = safeParseTs(t.start_date);
    if (start == null) continue;

    let end = safeParseTs(t.end_date);
    if (end == null) {
      const days = (t.standard_days ?? defaultDays);
      if (days != null) end = start + days * DAY;
    }
    if (end != null && end >= start) {
      out.push({ name: t.name || "Tratamiento", start, end });
    }
  }
  return out;
}

export function staggerMarkLineLabels(data, stepPx = 26) {
  let k = 0;
  return (data || []).map((item) => {
    const sign = (k % 2 === 0) ? -1 : +1;
    const level = Math.floor(k / 2) + 1;
    const dx = sign * level * stepPx;
    k += 1;

    return {
      ...item,
      label: {
        ...(item.label || {}),
        show: true,
        rotate: 90,
        position: "end",
        offset: [dx, 0],
      },
    };
  });
}

export function treatmentsAt(ts, intervals) {
  const res = [];
  for (const iv of intervals) {
    if (ts >= iv.start && ts <= iv.end) {
      const day = Math.floor((ts - iv.start) / DAY) + 1;
      res.push({ name: iv.name, day });
    }
  }
  return res;
}

export function computeExtentWithHorizon(flats, padDays = 7, horizonDays = 60) {
  const ts = [];
  for (const flat of (flats || [])) {
    for (const [d] of (flat || [])) {
      const t = new Date(d).getTime();
      if (!Number.isNaN(t)) ts.push(t);
    }
  }
  if (!ts.length) return { minTs: null, maxTs: null };
  const minTs = Math.min(...ts) - padDays * DAY;
  const maxTs = Math.max(...ts) + horizonDays * DAY;
  return { minTs, maxTs };
}

export function buildLimitsMarkLine(limits){
  if(!limits || !limits.length) return null;

  const data = limits
    .filter(l => l && l.value != null)
    .map(l => ({
      name: l.label || "Límite",
      yAxis: Number(l.value),
      lineStyle: { color: "#111827" },
    }));

  return {
    silent: true,
    symbol: ["none", "none"],
    lineStyle: { width: 2, type: "solid", opacity: 0.9 },
    label: {
      show: true,
      position: "end",
      formatter: (p) => p?.name ?? "",
    },
    /*data: staggerMarkLineLabels(data),*/
    data: data,
  };
}

export function mergeMarkLines(a, b) {
  if (!a && !b) return undefined;
  const base = a || b;

  const dataA = (a && a.data) ? a.data : [];
  const dataB = (b && b.data) ? b.data : [];

  const merged = [...dataA, ...dataB];

  // Orden estable para que el escalonado sea determinista
  const rank = (it) => {
    const n = String(it?.name || "");
    const low = n.toLowerCase();
    if (low.includes("límite")) return 10;
    if (n === "Max") return 20;
    if (n === "Min") return 30;
    return 99;
  };
  merged.sort((x, y) => rank(x) - rank(y));

  // Escalonamos UNA sola vez, después de mezclar
  const mergedStaggered = staggerMarkLineLabels(merged, 26);

  return {
    ...base,
    data: mergedStaggered,
  };
}

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

