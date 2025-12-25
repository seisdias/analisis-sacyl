// web/assets/charts/chart.js

import { state, labelOf } from "../state.js";
import { outOfRangeFlag, toISODate, parseISODate, extentTs, pctToTs, tsToPct, percentToDate, buildTreatmentIntervals,
 staggerMarkLineLabels, treatmentsAt, computeExtentWithHorizon, buildLimitsMarkLine, mergeMarkLines,
 renderTreatmentKpis } from "./chart_utils.js";
import { fetchSeries, fetchParamLimits, fetchTimeline, getTimelineCache } from "./chart_api.js";
import { timelineStyle, groupTimelineEventsByDay, buildTimelineEvents, buildTimelineMarkLineData,
  buildGlobalTimelineMarkLine, buildTimelineMarkAreas, buildTimelineMarkAreaOption } from "../timeline/timeline_builders.js";
import { detectCrossingsFlat, attachTreatmentDay } from "../clinical/clinical_crossings.js";
import { renderKpis } from "../kpis/kpis.js";


let chart = null;
let zoomStart = 0;
let zoomEnd = 100;
let globalExtent = { minTs: null, maxTs: null };
let lastMultiLegendSelected = null;
let suppressLegendHandler = false;

let zoomUi = null;

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

  const treatmentIntervals = buildTreatmentIntervals(timeline);
  const params = Array.from(state.enabledParams || []);
  const series = [];
  const kpiData = [];

  // Reset de extensión global (la fijamos con la primera serie con datos)
  globalExtent = { minTs: null, maxTs: null };

  const allFlats = [];
  const crossingsByParam = new Map();
  const limitByParam = new Map();



  for (const p of params) {
    const baseFlat = await fetchSeries(p);
    allFlats.push(baseFlat);
    let crossingsForParam = [];
    let limitValueForParam = null;

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

      // --- Cruces clínicos (FASE 4.3.1): SOLO cálculo (sin pintar aún)
      const firstLimit = (limits || []).find(l => l && l.value != null);
      if (firstLimit) {
        limitValueForParam = Number(firstLimit.value);
        const crossings = detectCrossingsFlat(baseFlat, limitValueForParam);
        crossingsForParam = attachTreatmentDay(crossings, treatmentIntervals);

        if (crossingsForParam.length) {
          console.log("[crossings]", p, firstLimit.label || "Límite", limitValueForParam, crossingsForParam);
        }

      }

      limitsMarkLine = buildLimitsMarkLine(limits);
    }catch(e){
      console.warn("No se pudieron cargar límites para", p, e);
      limitsMarkLine = null;
    }

    crossingsByParam.set(p, crossingsForParam || []);
    if (limitValueForParam != null) {
      limitByParam.set(p, limitValueForParam);
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
      markArea:
        (low != null && high != null)
          ? {
              silent: true,
              itemStyle: { opacity: 0.3 },
              data: [[{ yAxis: low }, { yAxis: high }]],
            }
          : undefined,
    });

    // --- Serie de cruces (puntos ficticios)
    if (crossingsForParam.length && limitValueForParam != null) {
      const crossingPoints = crossingsForParam.map(c => ([
        c.dateISO,
        limitValueForParam,
        {
          kind: "crossing",
          paramKey: p,
          direction: c.direction,   // "up" | "down"
          limitValue: limitValueForParam,
          treatments: c.treatments || [],
        }
      ]));

      series.push({
        name: `${labelOf(p)} — cruce`,
        type: "scatter",
        xAxisIndex: 0,
        yAxisIndex: 0,
        symbolSize: 10,
        data: crossingPoints,
        z: 10,
        tooltip: { show: true },
        // Para que no moleste en la leyenda:
        legendHoverLink: false,
        // Si no quieres que aparezca en la leyenda, lo hacemos luego con legend.selected
      });
    }


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

        // --- Caso especial: punto ficticio de cruce (scatter)
        let crossingHtml = "";
        const crossing = params.find((it) => {
          const v = it && it.value;
          return Array.isArray(v) && v.length >= 3 && v[2] && v[2].kind === "crossing";
        });

        if (crossing) {
          const v = crossing.value; // [dateISO, limitValue, meta]
          const dateISO = v[0];
          const limitVal = v[1];
          const meta = v[2];

          const dirTxt = meta.direction === "up" ? "↑ Cruce al alza" : "↓ Cruce a la baja";

          // Si hay tratamientos, muestra el primero (o todos)
          let txHtml = "";
          const txs = Array.isArray(meta.treatments) ? meta.treatments : [];
          if (txs.length) {
            txHtml = `
              <div style="margin-top:6px;opacity:.9">
                <hr style="margin:6px 0; opacity:.25"/>
                ${txs.map(it => `💊 ${it.name}`).join("<br/>")}
              </div>
            `;
          }

          crossingHtml =  `
            <div style="font-weight:700;margin-bottom:6px;">${dateISO}</div>
            <div><b>${labelOf(meta.paramKey)}</b></div>
            <div style="margin-top:4px;">${dirTxt} @ <b>${limitVal}</b></div>
            ${txHtml}
          `;
        }


        const mainParams = params.filter((it) => {
          const n = String(it.seriesName || "");
          if (n.endsWith("__mini")) return false;
          // excluir scatter de cruces del bloque "normal"
          if (n.includes("— cruce")) return false;
          return true;
        });
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
          ${crossingHtml}
        `
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
  // KPIs de tratamiento (se añaden DESPUÉS, porque renderKpis hace innerHTML y borraría lo previo)
  renderTreatmentKpis(treatmentIntervals, crossingsByParam, limitByParam, labelOf);


  // Pintado robusto: reset total
  chart.clear();
  chart.setOption(option, { notMerge: true, lazyUpdate: false });

  // Reaplicar zoom (por si ECharts reajusta internamente al cambiar series)
  chart.dispatchAction({ type: "dataZoom", start: zoomStart, end: zoomEnd });

  // Sincroniza inputs con el estado actual
  syncZoomInputsFromState();
}
