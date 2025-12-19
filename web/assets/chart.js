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

// -----------------------------
// Render (main)
// -----------------------------
export async function refreshChart() {
  if (!chart) return;

  const params = Array.from(state.enabledParams || []);
  const series = [];
  const kpiData = [];

  // Reset de extensión global (la fijamos con la primera serie con datos)
  globalExtent = { minTs: null, maxTs: null };

  for (const p of params) {
    const baseFlat = await fetchSeries(p);

    // Si aún no tenemos extents globales, usamos la primera serie con datos
    if (globalExtent.minTs == null && baseFlat && baseFlat.length) {
      globalExtent = extentTs(baseFlat);
    }

    const rr = state.ranges && state.ranges[p] ? state.ranges[p] : null;
    const low = rr ? rr.min : null;
    const high = rr ? rr.max : null;

    // Serie principal con out-of-range estilado
    const ptsStyled = baseFlat.map(([date, value]) => {
      const flag = outOfRangeFlag(value, low, high);
      if (!flag) return [date, value];

      return {
        value: [date, value],
        symbolSize: 10,
        itemStyle: {
          color: "#ef4444",
          borderColor: "#ffffff",
          borderWidth: 2,
        },
      };
    });

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
      markLine:
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
          : undefined,
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

        const date =
          mainParams[0].axisValueLabel || mainParams[0].axisValue || "";

        const rows = mainParams.map((it) => {
          const c = it.color || "#999";
          const marker = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${c};margin-right:8px;"></span>`;

          let v = it.value;
          if (Array.isArray(it.data)) v = it.data[1];
          else if (it.data && it.data.value && Array.isArray(it.data.value))
            v = it.data.value[1];

          return `<div>${marker}${it.seriesName}: <b>${v ?? "—"}</b></div>`;
        });

        return `
          <div style="font-weight:700;margin-bottom:6px;">${date}</div>
          ${rows.join("")}
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
      { type: "time", gridIndex: 0 },
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
