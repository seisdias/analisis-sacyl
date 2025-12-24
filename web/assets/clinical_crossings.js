// web/assets/clinical_crossings.js

const DAY = 24 * 60 * 60 * 1000;

function toTs(dateISO) {
  if (!dateISO) return null;
  const t = new Date(dateISO + "T00:00:00").getTime();
  return Number.isNaN(t) ? null : t;
}

function dirLabel(a, b, limit) {
  // devuelve "down" si cruza hacia abajo (pasa de >= a <),
  // "up" si cruza hacia arriba (pasa de <= a >)
  if (a >= limit && b < limit) return "down";
  if (a <= limit && b > limit) return "up";
  return null;
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

/**
 * Detecta cruces de una serie con un único límite.
 * @param {Array<[string, number]>} flat - [[YYYY-MM-DD, value], ...] ordenado
 * @param {number} limitValue
 * @returns {Array<{direction:"down"|"up", ts:number, dateISO:string, i0:number, i1:number, v0:number, v1:number}>}
 */
export function detectCrossingsFlat(flat, limitValue) {
  const out = [];
  if (!flat || flat.length < 2) return out;
  if (limitValue == null || !Number.isFinite(limitValue)) return out;

  for (let i = 1; i < flat.length; i++) {
    const [d0, v0raw] = flat[i - 1];
    const [d1, v1raw] = flat[i];

    const v0 = Number(v0raw);
    const v1 = Number(v1raw);
    if (!Number.isFinite(v0) || !Number.isFinite(v1)) continue;

    const t0 = toTs(d0);
    const t1 = toTs(d1);
    if (t0 == null || t1 == null || t1 <= t0) continue;

    const direction = dirLabel(v0, v1, limitValue);
    if (!direction) continue;

    // Interpolación lineal en el segmento (tiempo) para encontrar cuándo v(t)=limit
    const denom = (v1 - v0);
    if (denom === 0) continue;

    const alpha = (limitValue - v0) / denom; // 0..1 idealmente
    if (!(alpha >= 0 && alpha <= 1)) continue;

    const ts = Math.round(lerp(t0, t1, alpha));
    const dateISO = new Date(ts).toISOString().slice(0, 10);

    out.push({ direction, ts, dateISO, i0: i - 1, i1: i, v0, v1 });
  }

  return out;
}

/**
 * Asocia cruces a tratamientos (día +X) usando intervals del chart_utils.buildTreatmentIntervals().
 * intervals: [{name,start,end}]
 */
export function attachTreatmentDay(crossings, treatmentIntervals) {
  const out = [];
  for (const c of crossings || []) {
    const hits = [];
    for (const iv of (treatmentIntervals || [])) {
      if (c.ts >= iv.start && c.ts <= iv.end) {
        const day = Math.floor((c.ts - iv.start) / DAY) + 1;
        hits.push({ name: iv.name, day, start: iv.start, end: iv.end });
      }
    }
    out.push({ ...c, treatments: hits });
  }
  return out;
}
