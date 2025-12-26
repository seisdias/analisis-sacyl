// web/assets/charts/utils/treatments.js

import { safeParseTs } from "../../timeline/timeline_utils.js"
import { DAY } from "./date.js"

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