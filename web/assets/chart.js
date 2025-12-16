import { apiGet } from "./api.js";
import { state, labelOf } from "./state.js";
import { renderKpis } from "./kpis.js";


function outOfRangeFlag(value, low, high) {
  if (low != null && value < low) return "below";
  if (high != null && value > high) return "above";
  return null;
}

let chart = null;

let lastMultiLegendSelected = null;
let suppressLegendHandler = false;

export function initChart(dom) {
  chart = echarts.init(dom);

  chart.on("legendselectchanged", (e) => {
    if (suppressLegendHandler) return;

    const selectedMap = e.selected || {};
    const selectedNames = Object.keys(selectedMap).filter((k) => selectedMap[k]);
    const multiCount = selectedNames.length;

    // Si el usuario tiene varias activas, guardamos ese estado como “vista completa”
    if (multiCount >= 2) {
      lastMultiLegendSelected = { ...selectedMap };
      return;
    }

    // Si se queda a 0 (por click en la única activa), restauramos el estado multi anterior
    if (multiCount === 0 && lastMultiLegendSelected) {
      suppressLegendHandler = true;
      chart.setOption({ legend: { selected: lastMultiLegendSelected } }, false);
      suppressLegendHandler = false;
    }
  });

  window.addEventListener("resize", () => chart && chart.resize());
}

async function fetchSeries(param) {
  const data = await apiGet(
    state.base,
    `/series?param=${encodeURIComponent(param)}&limit=10000`
  );
  return data.points.map((p) => [p.date, p.value]);
}

export async function refreshChart() {
  const params = Array.from(state.enabledParams);
  const series = [];
  const kpiData = [];


  for (const p of params) {
    let pts = await fetchSeries(p);

    const rr = state.ranges && state.ranges[p] ? state.ranges[p] : null;
    const low = rr ? rr.min : null;
    const high = rr ? rr.max : null;

    pts = pts.map(([date, value]) => {
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
        tooltip: {
          extraCssText: "max-width: 320px",
          formatter: () => {
            const lowTxt = low != null ? low : "—";
            const highTxt = high != null ? high : "—";
            const why =
              flag === "below" ? "por debajo del mínimo" : "por encima del máximo";
            return `
              <div style="font-weight:600;margin-bottom:4px;">${labelOf(p)}</div>
              <div>Fecha: ${date}</div>
              <div>Valor: <b>${value}</b> (${why})</div>
              <div>Rango: ${lowTxt} – ${highTxt}</div>
            `;
          },
        },
      };
    });

    // Extraer puntos a formato uniforme: [date, value]
const flat = pts.map(x => Array.isArray(x) ? x : x.value);

// KPI: último y anterior
const last = flat.length ? flat[flat.length - 1] : null;
const prev = flat.length > 1 ? flat[flat.length - 2] : null;

const lastValue = last ? last[1] : null;
const prevValue = prev ? prev[1] : null;
const delta = (lastValue != null && prevValue != null) ? (lastValue - prevValue) : null;

// Alertas: nº de puntos fuera de rango
const alerts = flat.reduce((acc, x) => {
  const v = x[1];
  return outOfRangeFlag(v, low, high) ? acc + 1 : acc;
}, 0);

// Estado del último valor
let status = "sin datos";
let statusKind = "neutral";
if(lastValue != null){
  const flag = outOfRangeFlag(lastValue, low, high);
  if(!flag){ status = "en rango"; statusKind = "good"; }
  else if(flag === "below"){ status = "bajo"; statusKind = "bad"; }
  else { status = "alto"; statusKind = "bad"; }
}

kpiData.push({
  name: labelOf(p),
  unit: rr ? (rr.unit || "") : "",
  lastValue,
  delta,
  status,
  statusKind,
  alerts,
});


    series.push({
      name: labelOf(p),
      type: "line",
      smooth: true,
      showSymbol: true,
      symbolSize: 6,
      lineStyle: { width: 3 },
      //areaStyle: { opacity: 0.06 },
      emphasis: { focus: "series" },
      data: pts,

      markLine:
        low != null || high != null
          ? {
              silent: true,
              symbol: ["none", "none"],
              lineStyle: { type: "dashed" , opacity: 0.6 },
              data: [
                ...(low != null ? [{ yAxis: low, name: "Min" }] : []),
                ...(high != null ? [{ yAxis: high, name: "Max" }] : []),
              ],
            }
          : undefined,

      markArea:
        low != null && high != null
          ? {
              silent: true,
              itemStyle: { opacity: 0.08 },
              data: [[{ yAxis: low }, { yAxis: high }]],
            }
          : undefined,
    });
  }

  // Filtra legend.selected para que no incluya series que ya no existen
  let legendSelected = lastMultiLegendSelected;
  if (legendSelected) {
    const names = new Set(series.map((s) => s.name));
    legendSelected = Object.fromEntries(
      Object.entries(legendSelected).filter(([k]) => names.has(k))
    );
  }

  const option = {
  animation: true,
  tooltip: {
    trigger: "axis",
    confine: true,
    appendToBody: true,
    formatter: (params) => {
      if (!params || params.length === 0) return "";

      const date =
        params[0].axisValueLabel ||
        params[0].axisValue ||
        "";

      const rows = params.map((it) => {
        // Color REAL de la serie (no el del punto out-of-range)
        const c = it.color || "#999";
        const marker = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${c};margin-right:8px;"></span>`;

        // Valor: puede venir como [date, value] o como {value:[date,value]}
        let v = it.value;
        if (Array.isArray(it.data)) v = it.data[1];
        else if (it.data && it.data.value && Array.isArray(it.data.value)) v = it.data.value[1];

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
    selected: legendSelected || undefined,
  },
  grid: { top: 60, left: 60, right: 20, bottom: 60 },
  xAxis: { type: "time" },
  yAxis: { type: "value", scale: true },
  dataZoom: [
    { type: "inside", xAxisIndex: 0 },
    { type: "slider", xAxisIndex: 0 },
  ],
  series,
};

  renderKpis(kpiData);
  chart.setOption(option, true);
}
