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

let lastZoomStart = 0;
let lastZoomEnd = 100;

let zoomStart = 0;
let zoomEnd = 100;



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

  chart.on("dataZoom", () => {
    const opt = chart.getOption();
    const dz = (opt.dataZoom || []).find((z) => z.type === "slider");
    if (!dz) return;
    zoomStart = dz.start ?? zoomStart;
    zoomEnd = dz.end ?? zoomEnd;
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

function percentToDate(flat, pct){
  if(!flat || flat.length === 0) return null;
  const first = new Date(flat[0][0]).getTime();
  const last = new Date(flat[flat.length - 1][0]).getTime();
  const t = first + (last - first) * (pct / 100);
  return t;
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

    // Guardamos una versión "plana" para minimap y KPIs
    // (la usaremos también como base para el tooltip/valores)
    const baseFlat = pts;

    // Convertimos puntos fuera de rango en objetos con estilo
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
      };
    });

    // ---------- KPI ----------
    const flat = baseFlat; // [date, value]
    const last = flat.length ? flat[flat.length - 1] : null;
    const prev = flat.length > 1 ? flat[flat.length - 2] : null;

    const lastValue = last ? last[1] : null;
    const prevValue = prev ? prev[1] : null;
    const delta =
      lastValue != null && prevValue != null ? lastValue - prevValue : null;

    const alerts = flat.reduce((acc, x) => {
      const v = x[1];
      return outOfRangeFlag(v, low, high) ? acc + 1 : acc;
    }, 0);

    let status = "sin datos";
    let statusKind = "neutral";

    const lastDate = last ? last[0] : null;
    const rangeText = (low != null || high != null)
      ? `${low != null ? low : "—"} – ${high != null ? high : "—"}`
      : "—";

    // últimas 5 alertas (fecha/valor/tipo)
    const lastAlerts = flat
      .map(([d, v]) => {
        const f = outOfRangeFlag(v, low, high);
        return f ? { date: d, value: v, flag: f } : null;
      })
      .filter(Boolean)
      .slice(-5)
      .reverse();



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

    kpiData.push({
      name: labelOf(p),
      unit: rr ? rr.unit || "" : "",
      lastValue,
      delta,
      status,
      statusKind,
      alerts,
      lastDate,
      rangeText,
      lastAlerts,
    });

    // ---------- Serie principal ----------
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
      data: pts,

      // min/max (más sutil)
      markLine:
        low != null || high != null
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

      // banda rango normal
      markArea:
        low != null && high != null
          ? {
              silent: true,
              itemStyle: { opacity: 0.3 },
              data: [[{ yAxis: low }, { yAxis: high }]],
            }
          : undefined,
    });

    // ---------- Serie minimap ----------
    // Usamos baseFlat (sin objetos rojos) para que sea ligera y coherente.
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

      // Ventana seleccionada (se pinta encima del minimap)
      markArea: {
        silent: true,
        itemStyle: { opacity: 0.10 },
        data: [[
          { xAxis: percentToDate(baseFlat, lastZoomStart) },
          { xAxis: percentToDate(baseFlat, lastZoomEnd) }
        ]]
      }

    });
  }

  // Filtra legend.selected para que no incluya series que ya no existen (y que no meta minis)
  let legendSelected = lastMultiLegendSelected;
  if (legendSelected) {
    const names = new Set(series.map((s) => s.name).filter((n) => !n.endsWith("__mini")));
    legendSelected = Object.fromEntries(
      Object.entries(legendSelected).filter(([k]) => names.has(k))
    );
  }

  // Leyenda: solo series "reales"
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

        // Quitamos minis del tooltip
        const mainParams = params.filter(
          (it) => !String(it.seriesName || "").endsWith("__mini")
        );
        if (mainParams.length === 0) return "";

        const date =
          mainParams[0].axisValueLabel || mainParams[0].axisValue || "";

        const rows = mainParams.map((it) => {
          const c = it.color || "#999";
          const marker = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${c};margin-right:8px;"></span>`;

          // Valor: puede ser [date,value] o {value:[date,value]}
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
      { top: 60, left: 60, right: 20, bottom: 120 }, // principal
      { left: 60, right: 20, height: 60, bottom: 40 }, // mini
    ],

    xAxis: [
      { type: "time", gridIndex: 0 },
      { type: "time", gridIndex: 1, min: "dataMin", max: "dataMax" }
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

  renderKpis(kpiData);
  chart.setOption(option, { notMerge: false, lazyUpdate: true });

  chart.off("dataZoom");
  chart.on("dataZoom", () => {
    const opt = chart.getOption();
    const dz = (opt.dataZoom || []).find(z => z.type === "slider" || z.type === "inside");
    if(!dz) return;
    lastZoomStart = dz.start ?? lastZoomStart;
    lastZoomEnd = dz.end ?? lastZoomEnd;

    // vuelve a pintar para actualizar la ventana en minimap
    refreshChart();
  });


  chart.off("dataZoom"); // evita duplicados si refrescas
  chart.on("dataZoom", () => {
    const opt = chart.getOption();
    const dz = opt.dataZoom || [];
    const slider = dz.find(z => z.type === "slider");
    if(!slider) return;

    suppressLegendHandler = true;
    chart.setOption({
      dataZoom: [
        { type: "inside", xAxisIndex: 0, start: slider.start, end: slider.end }
      ]
    }, false);
    suppressLegendHandler = false;
  });

}
