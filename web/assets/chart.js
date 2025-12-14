import { apiGet } from "./api.js";
import { state, labelOf } from "./state.js";

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
    tooltip: { trigger: "axis" },
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

  chart.setOption(option, true);
}
