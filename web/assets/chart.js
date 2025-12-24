// web/assets/chart.js
import { apiGet } from "./api.js";
import { state, labelOf } from "./state.js";
import { renderKpis } from "./kpis.js";

// -----------------------------
// Helpers
// -----------------------------
function outOfRangeFlag(value, low, high) {
  if (low != null && value < low) return "below";
  if (high != null && value > high) return "above";
  return null;
}

function toISODate(ts) {
  const x = new Date(ts);
  if (Number.isNaN(x.getTime())) return "";
  const yyyy = x.getFullYear();
  const mm = String(x.getMonth() + 1).padStart(2, "0");
  const dd = String(x.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function parseISODate(s) {
  if (!s) return null;
  const t = new Date(s + "T00:00:00").getTime();
  return Number.isNaN(t) ? null : t;
}

function extentTs(flat) {
  if (!flat || flat.length === 0) return { minTs: null, maxTs: null };
  const minTs = new Date(flat[0][0]).getTime();
  const maxTs = new Date(flat[flat.length - 1][0]).getTime();
  if (Number.isNaN(minTs) || Number.isNaN(maxTs)) return { minTs: null, maxTs: null };
  return { minTs, maxTs };
}

function pctToTs(pct, minTs, maxTs) {
  if (minTs == null || maxTs == null) return null;
  return minTs + (maxTs - minTs) * (pct / 100);
}

function tsToPct(ts, minTs, maxTs) {
  if (ts == null || minTs == null || maxTs == null) return 0;
  if (maxTs === minTs) return 0;
  const p = ((ts - minTs) / (maxTs - minTs)) * 100;
  return Math.max(0, Math.min(100, p));
}

function percentToDate(flat, pct) {
  if (!flat || flat.length === 0) return null;
  const first = new Date(flat[0][0]).getTime();
  const last = new Date(flat[flat.length - 1][0]).getTime();
  if (Number.isNaN(first) || Number.isNaN(last)) return null;
  return first + (last - first) * (pct / 100);
}

function buildTreatmentIntervals(timeline) {
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

function treatmentsAt(ts, intervals) {
  const res = [];
  for (const iv of intervals) {
    if (ts >= iv.start && ts <= iv.end) {
      const day = Math.floor((ts - iv.start) / DAY) + 1;
      res.push({ name: iv.name, day });
    }
  }
  return res;
}

const DAY = 24 * 60 * 60 * 1000;

function computeExtentWithHorizon(flats, padDays = 7, horizonDays = 60) {
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

async function fetchParamLimits(baseUrl, paramKey){
  const sid = state.sessionId || null;
  const url = new URL(`${baseUrl}/param_limits`, window.location.origin);
  url.searchParams.set("param_key", paramKey);
  if (sid) url.searchParams.set("session_id", sid);

  const r = await fetch(url.toString());
  if(!r.ok) throw new Error(`limits http ${r.status}`);
  const j = await r.json();
  return j.limits || [];
}

function buildLimitsMarkLine(limits){
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


function mergeMarkLines(a, b) {
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


function staggerMarkLineLabels(data, stepPx = 26) {
  // Con rotate:90, el solape se evita escalonando en X (dx)
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







// -----------------------------
// Module state
// -----------------------------
let chart = null;

// Zoom actual (en % de dataZoom)
let zoomStart = 0;
let zoomEnd = 100;

// Extensión global (timestamps) para convertir fechas <-> %
let globalExtent = { minTs: null, maxTs: null };

// Legend multi-selection guardada
let lastMultiLegendSelected = null;
let suppressLegendHandler = false;

// UI zoom refs (se enlazan si existen)
let zoomUi = null;

// -----------------------------
// API
// -----------------------------
async function fetchSeries(param) {
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

// -----------------------------
// Timeline (ingresos + tratamientos)
// -----------------------------
let timelineCache = null; // { config, treatments, hospital_stays } | null

async function fetchTimeline() {
  // Reutilizamos apiGet (ya mete session_id automáticamente si state.sessionId existe)
  const data = await apiGet(state.base, "/timeline");
  timelineCache = data || null;
  return timelineCache;
}

function safeParseTs(dateStr) {
  // Esperamos "YYYY-MM-DD" desde backend
  if (!dateStr) return null;
  const t = new Date(dateStr + "T00:00:00").getTime();
  return Number.isNaN(t) ? null : t;
}

function uniqByKey(items, keyFn) {
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

function buildTimelineEvents(timeline, defaultTreatmentDays) {
  const events = [];
  if (!timeline) return events;

  const stays = timeline.hospital_stays || [];
  for (const s of stays) {
    const a = safeParseTs(s.admission_date);
    const d = safeParseTs(s.discharge_date);

    if (a != null) {
      events.push({
        x: a,
        kind: "hospital_admission",
        label: "Ingreso",
        detail: s.notes || "",
      });
    }
    if (d != null) {
      events.push({
        x: d,
        kind: "hospital_discharge",
        label: "Alta",
        detail: s.notes || "",
      });
    }
  }

  const treatments = timeline.treatments || [];
  for (const t of treatments) {
    const start = safeParseTs(t.start_date);
    const end = safeParseTs(t.end_date);

    if (start != null) {
      events.push({
        x: start,
        kind: "treatment_start",
        label: `Inicio tto${t.name ? `: ${t.name}` : ""}`,
        detail: t.notes || "",
      });
    }

    // Si no hay end_date, NO pintamos fin aún (lo haremos más adelante con fin teórico)
    if (end != null) {
      events.push({
        x: end,
        kind: "treatment_end",
        label: `Fin tto${t.name ? `: ${t.name}` : ""}`,
        detail: t.notes || "",
      });
    }
  }

  // Orden + dedupe por kind+ts+label (evita duplicados si backend repite)
  const ordered = events
    .filter((e) => e.x != null)
    .sort((a, b) => a.x - b.x);

  return uniqByKey(ordered, (e) => `${e.kind}|${e.x}|${e.label}`);
}

function buildTimelineMarkLineData(events) {
  if (!events || events.length === 0) return [];

  return events.map((e) => ({
    name: e.label,
    xAxis: e.x,                 // <-- ahora string "YYYY-MM-DD"
    lineStyle: timelineStyle(e.kind),
  }));
}


// -----------------------------
// Init
// -----------------------------
export function initChart(dom) {
  chart = echarts.init(dom);

  // Leyenda: proteger multi-selección
  chart.on("legendselectchanged", (e) => {
    if (suppressLegendHandler) return;

    const selectedMap = e.selected || {};
    const selectedNames = Object.keys(selectedMap).filter((k) => selectedMap[k]);
    const multiCount = selectedNames.length;

    if (multiCount >= 2) {
      lastMultiLegendSelected = { ...selectedMap };
      return;
    }

    // Si el usuario desactiva la única activa y se queda a 0, restauramos vista multi anterior
    if (multiCount === 0 && lastMultiLegendSelected) {
      suppressLegendHandler = true;
      chart.setOption({ legend: { selected: lastMultiLegendSelected } }, false);
      suppressLegendHandler = false;
    }
  });

  // Un ÚNICO handler dataZoom: actualiza zoomStart/zoomEnd y sincroniza inputs si existen
  chart.on("dataZoom", () => {
    const opt = chart.getOption();
    const dz = opt.dataZoom || [];
    const slider = dz.find((z) => z.type === "slider") || dz.find((z) => z.type === "inside");
    if (!slider) return;

    zoomStart = slider.start ?? zoomStart;
    zoomEnd = slider.end ?? zoomEnd;

    // Sync UI (si está cableado)
    if (zoomUi) {
      queueMicrotask(() => syncZoomInputsFromState());
    }
  });

  window.addEventListener("resize", () => chart && chart.resize());

  // Cablear UI zoom (si existe en el DOM)
  wireZoomUI();
}

// -----------------------------
// Zoom UI
// -----------------------------
function wireZoomUI() {
  const fromEl = document.getElementById("zoomFrom");
  const toEl = document.getElementById("zoomTo");
  const applyEl = document.getElementById("zoomApply");
  const resetEl = document.getElementById("zoomReset");
  const hintEl = document.getElementById("zoomHint");

  if (!fromEl || !toEl || !applyEl || !resetEl) {
    zoomUi = null;
    return;
  }

  zoomUi = { fromEl, toEl, applyEl, resetEl, hintEl };

  applyEl.addEventListener("click", () => {
    const { minTs, maxTs } = globalExtent;
    if (minTs == null || maxTs == null) return;

    const a = parseISODate(fromEl.value);
    const b = parseISODate(toEl.value);
    if (a == null || b == null) return;

    const lo = Math.min(a, b);
    const hi = Math.max(a, b);

    zoomStart = tsToPct(lo, minTs, maxTs);
    zoomEnd = tsToPct(hi, minTs, maxTs);

    // ECharts: aplicar zoom
    chart.dispatchAction({ type: "dataZoom", start: zoomStart, end: zoomEnd });
    syncZoomInputsFromState();
  });

  resetEl.addEventListener("click", () => {
    zoomStart = 0;
    zoomEnd = 100;
    chart.dispatchAction({ type: "dataZoom", start: zoomStart, end: zoomEnd });
    syncZoomInputsFromState();
  });

  // Primer sync (cuando refreshChart calcule globalExtent y pinte)
  setTimeout(syncZoomInputsFromState, 250);
}

function syncZoomInputsFromState() {
  if (!zoomUi) return;
  const { minTs, maxTs } = globalExtent;
  if (minTs == null || maxTs == null) return;

  const a = pctToTs(zoomStart, minTs, maxTs);
  const b = pctToTs(zoomEnd, minTs, maxTs);
  if (a == null || b == null) return;

  zoomUi.fromEl.value = toISODate(a);
  zoomUi.toEl.value = toISODate(b);

  if (zoomUi.hintEl) {
    zoomUi.hintEl.textContent =
      `Mostrando: ${toISODate(a)} → ${toISODate(b)} (zoom ${zoomStart.toFixed(1)}%–${zoomEnd.toFixed(1)}%)`;
  }
}

function timelineStyle(kind) {
  // No especifico colores globales (para no “imponer” estilo), pero sí diferenciamos patrón y grosor.
  // Si luego quieres colores específicos, lo ajustamos en 2 minutos.
  if (kind === "hospital_admission") return { type: "solid", width: 2, opacity: 0.85 };
  if (kind === "hospital_discharge") return { type: "dashed", width: 2, opacity: 0.85 };
  if (kind === "treatment_start") return { type: "solid", width: 1, opacity: 0.70 };
  if (kind === "treatment_end") return { type: "dashed", width: 1, opacity: 0.70 };
  return { type: "dotted", width: 1, opacity: 0.6 };
}

function buildGlobalTimelineMarkLine(events, globalExtent) {
  if (!events || events.length === 0) return null;

  const { minTs, maxTs } = globalExtent || {};
  // Si tenemos extent, filtramos eventos fuera del rango para no “ensuciar” el zoom
  const filtered = (minTs != null && maxTs != null)
    ? events.filter((e) => e.x >= minTs && e.x <= maxTs)
    : events;

  if (filtered.length === 0) return null;

  // ECharts markLine requiere data: [{ xAxis: <value>, name: <...>, lineStyle: {...} }, ...]
  const data = filtered.map((e) => ({
    name: e.label,
    xAxis: e.x,               // xAxis time → timestamp OK
    lineStyle: timelineStyle(e.kind),
    // Tooltip: usamos un formatter general, pero dejamos info en el nombre.
  }));

  return {
    silent: true,
    symbol: ["none", "none"],
    // label se verá arriba; si molesta lo quitamos
    label: {
      show: true,
      formatter: (p) => p.name || "",
      rotate: 90,
      position: "insideEndTop",
    },
    data,
  };
}

function groupTimelineEventsByDay(events) {
  const map = new Map(); // x -> { x, labels: [], kinds: Set }
  for (const e of events) {
    const key = e.x; // "YYYY-MM-DD"
    if (!map.has(key)) map.set(key, { x: key, items: [] });
    map.get(key).items.push(e);
  }

  const grouped = [];
  for (const [x, g] of map.entries()) {
    // Orden interno estable: ingresos antes que tratamientos (ajústalo si quieres)
    const order = (k) => {
      if (k === "hospital_admission") return 10;
      if (k === "hospital_discharge") return 20;
      if (k === "treatment_start") return 30;
      if (k === "treatment_end") return 40;
      return 99;
    };

    g.items.sort((a, b) => order(a.kind) - order(b.kind));

    const label = g.items.map(it => it.label).join(" · ");
    // Elegimos el “kind principal” para el estilo de la línea (prioridad configurable)
    const kind = g.items[0]?.kind || "other";

    grouped.push({
      x,
      kind,
      label,
      count: g.items.length,
      items: g.items,
    });
  }

  grouped.sort((a, b) => String(a.x).localeCompare(String(b.x)));
  return grouped;
}

// -----------------------------
// Timeline MarkArea (intervalos)
// -----------------------------
function buildTimelineMarkAreas(timeline) {
  if (!timeline) return [];

  const areas = [];

  const stays = timeline.hospital_stays || [];
  for (const s of stays) {
    const a = safeParseTs(s.admission_date);
    const d = safeParseTs(s.discharge_date);
    if (a != null && d != null && d >= a) {
      areas.push({
        kind: "hospital",
        from: a,
        to: d,
        label: "Ingreso hospitalario",
      });
    }
  }

  const defaultDays =
    timeline.config?.treatment_default_days != null
      ? timeline.config.treatment_default_days
      : null;

  const treatments = timeline.treatments || [];
  for (const t of treatments) {
    const start = safeParseTs(t.start_date);
    if (start == null) continue;

    let end = safeParseTs(t.end_date);
    if (end == null) {
      const days =
        t.standard_days != null
          ? t.standard_days
          : defaultDays;
      if (days != null) {
        end = start + days * 24 * 60 * 60 * 1000;
      }
    }

    if (end != null && end >= start) {
      areas.push({
        kind: "treatment",
        from: start,
        to: end,
        label: t.name ? `Tratamiento: ${t.name}` : "Tratamiento",
      });
    }
  }

  return areas;
}

function buildTimelineMarkAreaOption(areas) {
  if (!areas || areas.length === 0) return null;

  const hospitalColor = "rgba(59,130,246,0.10)";   // azul/gris
  const treatmentColor = "rgba(16,185,129,0.12)"; // verde

  return {
    silent: true,
    data: areas.map((a) => ([
      {
        xAxis: a.from,
        itemStyle: {
          color: a.kind === "hospital" ? hospitalColor : treatmentColor,
        },
        label: {
          show: false,
        },
      },
      {
        xAxis: a.to,
      },
    ])),
  };
}

// -----------------------------
// Render (main)
// -----------------------------
export async function refreshChart() {
  if (!chart) return;

    // 1) Cargar timeline (no bloquea si falla; no queremos romper gráficas)
  let timeline = null;
  try {
    timeline = await fetchTimeline();
  } catch (e) {
    console.warn("No se pudo cargar timeline:", e);
    timeline = null;
  }


  const params = Array.from(state.enabledParams || []);
  const series = [];
  const kpiData = [];

  // Reset de extensión global (la fijamos con la primera serie con datos)
  globalExtent = { minTs: null, maxTs: null };

  const allFlats = [];

  for (const p of params) {
    const baseFlat = await fetchSeries(p);
    allFlats.push(baseFlat);

    // Si aún no tenemos extents globales, usamos la primera serie con datos
    if (globalExtent.minTs == null && baseFlat && baseFlat.length) {
      globalExtent = extentTs(baseFlat);
    }

    const rr = state.ranges && state.ranges[p] ? state.ranges[p] : null;
    const low = rr ? rr.min : null;
    const high = rr ? rr.max : null;

    const ptsStyled = baseFlat;

    let limitsMarkLine = null;
    try{
      const limits = await fetchParamLimits(state.base, p);   // p = paramKey
      limitsMarkLine = buildLimitsMarkLine(limits);
    }catch(e){
      console.warn("No se pudieron cargar límites para", p, e);
      limitsMarkLine = null;
    }

    const rangesData = [
      ...(low != null ? [{ yAxis: low, name: "Min" }] : []),
      ...(high != null ? [{ yAxis: high, name: "Max" }] : []),
    ];

    const rangesMarkLine =
    (low != null || high != null)
      ? {
          silent: true,
          symbol: ["none", "none"],
          lineStyle: { type: "dashed", opacity: 0.6 },
          data: staggerMarkLineLabels(rangesData),

        }
      : undefined;

    // limitsMarkLine ya lo calculas arriba con fetchParamLimits + buildLimitsMarkLine(...)
    const combinedMarkLine = mergeMarkLines(rangesMarkLine, limitsMarkLine);



    // KPIs
    const last = baseFlat.length ? baseFlat[baseFlat.length - 1] : null;
    const prev = baseFlat.length > 1 ? baseFlat[baseFlat.length - 2] : null;

    const lastValue = last ? last[1] : null;
    const prevValue = prev ? prev[1] : null;
    const delta = (lastValue != null && prevValue != null) ? (lastValue - prevValue) : null;

    const alerts = baseFlat.reduce((acc, x) => {
      const v = x[1];
      return outOfRangeFlag(v, low, high) ? acc + 1 : acc;
    }, 0);

    let status = "sin datos";
    let statusKind = "neutral";

    if (lastValue != null) {
      const flag = outOfRangeFlag(lastValue, low, high);
      if (!flag) {
        status = "en rango";
        statusKind = "good";
      } else if (flag === "below") {
        status = "bajo";
        statusKind = "bad";
      } else {
        status = "alto";
        statusKind = "bad";
      }
    }

    const lastDate = last ? last[0] : null;
    const rangeText = (low != null || high != null)
      ? `${low != null ? low : "—"} – ${high != null ? high : "—"}`
      : "—";

    const lastAlerts = baseFlat
      .map(([d, v]) => {
        const f = outOfRangeFlag(v, low, high);
        return f ? { date: d, value: v, flag: f } : null;
      })
      .filter(Boolean)
      .slice(-5)
      .reverse();

    kpiData.push({
      name: labelOf(p),
      unit: rr ? (rr.unit || "") : "",
      lastValue,
      delta,
      status,
      statusKind,
      alerts,
      lastDate,
      rangeText,
      lastAlerts,
    });


    // Serie principal
    series.push({
      name: labelOf(p),
      type: "line",
      xAxisIndex: 0,
      yAxisIndex: 0,
      smooth: true,
      showSymbol: true,
      symbolSize: 6,
      lineStyle: { width: 3 },
      emphasis: { focus: "series" },
      data: ptsStyled,
      markLine : combinedMarkLine,
      /*markLine:
        (low != null || high != null)
          ? {
              silent: true,
              symbol: ["none", "none"],
              lineStyle: { type: "dashed", opacity: 0.6 },
              data: [
                ...(low != null ? [{ yAxis: low, name: "Min" }] : []),
                ...(high != null ? [{ yAxis: high, name: "Max" }] : []),
              ],
            }
          : undefined,*/
      markArea:
        (low != null && high != null)
          ? {
              silent: true,
              itemStyle: { opacity: 0.3 },
              data: [[{ yAxis: low }, { yAxis: high }]],
            }
          : undefined,
    });

    // Serie minimap (ligera, sin rojos)
    series.push({
      name: labelOf(p) + "__mini",
      type: "line",
      xAxisIndex: 1,
      yAxisIndex: 1,
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 1, opacity: 0.6 },
      data: baseFlat,
      tooltip: { show: false },
      emphasis: { disabled: true },
      markArea: {
        silent: true,
        itemStyle: { opacity: 0.10 },
        data: [[
          { xAxis: percentToDate(baseFlat, zoomStart) },
          { xAxis: percentToDate(baseFlat, zoomEnd) }
        ]]
      }
    });
  }

    // 2) Construir eventos timeline y markLine global
  const defaultDays = (timeline && timeline.config) ? timeline.config.treatment_default_days : null;
  const timelineEvents = buildTimelineEvents(timeline,defaultDays);
  const grouped = groupTimelineEventsByDay(timelineEvents);
  // 2.b) MarkArea de intervalos (ingresos + tratamientos)
  const timelineAreas = buildTimelineMarkAreas(timeline);
  const timelineMarkArea = buildTimelineMarkAreaOption(timelineAreas);
  const treatmentIntervals = buildTreatmentIntervals(timeline);
  globalExtent = computeExtentWithHorizon(allFlats, 7, 60);



  let flip = false;
  const timelineMarkData = grouped.map((g) => {
    flip = !flip;
    return {
      name: g.label,
      xAxis: g.x,
      lineStyle: timelineStyle(g.kind),
      label: {
        show: true,
        rotate: 90,
        position: flip ? "insideStartTop" : "insideEndTop",
      },
    };
  });




  const globalTimelineMarkLine = buildGlobalTimelineMarkLine(timelineEvents, globalExtent);


  // Legend selected: no incluir minis ni series desaparecidas
  let legendSelected = lastMultiLegendSelected;
  if (legendSelected) {
    const names = new Set(series.map((s) => s.name).filter((n) => !n.endsWith("__mini")));
    legendSelected = Object.fromEntries(
      Object.entries(legendSelected).filter(([k]) => names.has(k))
    );
  }

  // Leyenda: solo series reales
  const legendNames = series
    .map((s) => s.name)
    .filter((n) => !n.endsWith("__mini"));

  if (timelineMarkData.length) {
    series.push({
      name: "__timeline__",
      type: "line",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: [],                // no pinta línea como serie
      showSymbol: false,
      silent: true,
      lineStyle: { opacity: 0 },
      tooltip: { show: false },

      markLine: {
        silent: true,
        symbol: ["none", "none"],
        label: {
          show: true,
          formatter: (p) => p.name || "",
          rotate: 90,
          position: "insideEndTop",
        },
        data: timelineMarkData,
      },
      markArea: timelineMarkArea || undefined,
    });
  } else {
    console.warn("Timeline sin eventos para pintar.");
  }

  const option = {
    animation: true,

    tooltip: {
      trigger: "axis",
      confine: true,
      appendToBody: true,
      formatter: (params) => {
        if (!params || params.length === 0) return "";

        const mainParams = params.filter(
          (it) => !String(it.seriesName || "").endsWith("__mini")
        );
        if (mainParams.length === 0) return "";

        const axis = mainParams[0].axisValue;
        const ts = (axis != null) ? Number(axis) : null;
        const date = ts != null
          ? new Date(ts).toLocaleDateString("es-ES")
          : "";

        let extra = "";
        if (ts != null && Number.isFinite(ts)) {
          const inside = treatmentsAt(ts, treatmentIntervals);
          if (inside.length) {
            extra = `
              <div style="margin-top:6px;opacity:.9">
                <hr style="margin:6px 0; opacity:.25"/>
                ${inside.map(it => `💊 ${it.name}: día <b>+${it.day}</b>`).join("<br/>")}
              </div>
            `;
          }
        }

        const rows = mainParams.map((it) => {
          const c = it.color || "#999";
          const marker = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${c};margin-right:8px;"></span>`;

          let v = it.value;
          if (Array.isArray(it.data)) v = it.data[1];
          else if (it.data && it.data.value && Array.isArray(it.data.value)) v = it.data.value[1];

          return `<div>${marker}${it.seriesName}: <b>${v ?? "—"}</b></div>`;
        });
        return `
          <div style="font-weight:700;margin-bottom:6px;">${date}</div>
          ${rows.join("")}
          ${extra}
        `;
      },
    },

    legend: {
      top: 10,
      data: legendNames,
      selected: legendSelected || undefined,
    },

    grid: [
      { top: 60, left: 60, right: 20, bottom: 120 },
      { left: 60, right: 20, height: 60, bottom: 40 },
    ],

    xAxis: [
      {
        type: "time",
        gridIndex: 0,
        min: globalExtent.minTs ?? "dataMin",
        max: globalExtent.maxTs ?? "dataMax",
      },
      { type: "time", gridIndex: 1, min: "dataMin", max: "dataMax" },
    ],

    yAxis: [
      { type: "value", scale: true, gridIndex: 0 },
      {
        type: "value",
        scale: true,
        gridIndex: 1,
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ],

    dataZoom: [
      { type: "inside", xAxisIndex: 0, start: zoomStart, end: zoomEnd },
      { type: "slider", xAxisIndex: 0, bottom: 0, height: 28, start: zoomStart, end: zoomEnd },
    ],

    series,
    // MarkLine global (líneas verticales timeline)
    markLine: globalTimelineMarkLine || undefined,
  };

  // KPIs
  renderKpis(kpiData);

  // Pintado robusto: reset total
  chart.clear();
  chart.setOption(option, { notMerge: true, lazyUpdate: false });

  // Reaplicar zoom (por si ECharts reajusta internamente al cambiar series)
  chart.dispatchAction({ type: "dataZoom", start: zoomStart, end: zoomEnd });

  // Sincroniza inputs con el estado actual
  syncZoomInputsFromState();
}
