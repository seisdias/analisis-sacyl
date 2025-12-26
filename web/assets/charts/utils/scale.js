// web/assets/charts/utils/scale.js

import { DAY } from "./date.js"

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




