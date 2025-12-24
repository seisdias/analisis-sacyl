// web/assets/chart_api.js

import { apiGet } from "./api.js";
import { state } from "./state.js";

let timelineCache = null; // { config, treatments, hospital_stays } | null

// -----------------------------
// API
// -----------------------------
export async function fetchSeries(param) {
  const qs = new URLSearchParams({
    param,
    limit: "10000",
  });

  if (state.sessionId) {
    qs.set("session_id", state.sessionId);
  }

  const data = await apiGet(
    state.base,
    `/series?${qs.toString()}`
  );

  return (data.points || []).map((p) => [p.date, p.value]);
}

export async function fetchParamLimits(baseUrl, paramKey){
  const sid = state.sessionId || null;
  const url = new URL(`${baseUrl}/param_limits`, window.location.origin);
  url.searchParams.set("param_key", paramKey);
  if (sid) url.searchParams.set("session_id", sid);

  const r = await fetch(url.toString());
  if(!r.ok) throw new Error(`limits http ${r.status}`);
  const j = await r.json();
  return j.limits || [];
}

export async function fetchTimeline() {
  // Reutilizamos apiGet (ya mete session_id automáticamente si state.sessionId existe)
  const data = await apiGet(state.base, "/timeline");
  timelineCache = data || null;
  return timelineCache;
}

export function getTimelineCache() {
  return timelineCache;
}