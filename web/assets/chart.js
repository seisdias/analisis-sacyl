import { apiGet } from "./api.js";
import { state, labelOf } from "./state.js";

let chart = null;

export function initChart(dom){
  chart = echarts.init(dom);
  window.addEventListener("resize", () => chart && chart.resize());
}

async function fetchSeries(param){
  const data = await apiGet(state.base, `/series?param=${encodeURIComponent(param)}&limit=10000`);
  return data.points.map(p => [p.date, p.value]);
}

export async function refreshChart(){
  const params = Array.from(state.enabledParams);
  const series = [];

  for(const p of params){
    const pts = await fetchSeries(p);
    const rr = (state.ranges && state.ranges[p]) ? state.ranges[p] : null;
    const low = rr ? rr.min : null;
    const high = rr ? rr.max : null;
    series.push({
      name: labelOf(p),
      type: "line",
      smooth: true,
      showSymbol: true,
      symbolSize: 6,
      data: pts,
      // ── líneas horizontales de mínimo y máximo ──
      markLine: (low != null || high != null) ? {
         silent: true,
         symbol: ["none", "none"],
         lineStyle: { type: "dashed" },
         data: [
           ...(low != null ? [{ yAxis: low, name: "Min" }] : []),
           ...(high != null ? [{ yAxis: high, name: "Max" }] : [])
         ]
      } : undefined,
      // ── banda sombreada del rango normal ──
      markArea: (low != null && high != null) ? {
         silent: true,
         itemStyle: { opacity: 0.12 },
         data: [[{ yAxis: low }, { yAxis: high }]]
      } : undefined,
    });
  }

  const option = {
    animation: true,
    tooltip: { trigger: "axis" },
    legend: { top: 10 },
    grid: { top: 60, left: 60, right: 20, bottom: 60 },
    xAxis: { type: "time" },
    yAxis: { type: "value", scale: true },
    dataZoom: [
      { type: "inside", xAxisIndex: 0 },
      { type: "slider", xAxisIndex: 0 }
    ],
    series
  };

  chart.setOption(option, true);
}
