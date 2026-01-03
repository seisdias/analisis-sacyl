// web/assets/ui/modals/histograms/renderers.js

function buildXYData(res) {
  const x = res.x || [];
  const y = res.y || [];
  const data = [];
  for (let i = 0; i < Math.min(x.length, y.length); i++) data.push([x[i], y[i]]);
  return data;
}

function buildMarkers(res) {
  const markLines = [];
  if (res.markers && typeof res.markers === "object") {
    for (const [k, v] of Object.entries(res.markers)) {
      if (v == null || Number.isNaN(Number(v))) continue;
      markLines.push({
        xAxis: Number(v),
        name: k,
        label: { formatter: k },
      });
    }
  }
  return markLines;
}

function buildBands(res) {
  const markAreas = [];
  if (Array.isArray(res.bands)) {
    for (const b of res.bands) {
      if (!b) continue;
      const from = Number(b.from);
      const to = Number(b.to);
      if (Number.isFinite(from) && Number.isFinite(to)) {
        markAreas.push([{ xAxis: from, name: b.label || "" }, { xAxis: to }]);
      }
    }
  }
  return markAreas;
}

export function renderXYCurve(chart, res) {
  const labelX = res.labels && res.labels.x ? res.labels.x : "X";
  const labelY = res.labels && res.labels.y ? res.labels.y : "Y";

  const data = buildXYData(res);
  const markLines = buildMarkers(res);
  const markAreas = buildBands(res);

  chart.setOption(
    {
      title: { text: `${(res.title || "Histograma")} · ${res.date || ""}`.trim(), left: "center", top: 6 },
      grid: { left: 60, right: 18, top: 52, bottom: 46 },
      tooltip: {
        trigger: "axis",
        confine: true,
        axisPointer: { type: "cross" },
        formatter: (params) => {
          const p = params && params[0];
          if (!p || !p.value) return "";
          const x = p.value[0];
          const y = p.value[1];
          return `X: <b>${x}</b><br/>Y: <b>${y}</b>`;
        },
      },
      xAxis: { type: "value", name: labelX, nameLocation: "middle", nameGap: 28 },
      yAxis: { type: "value", name: labelY, nameLocation: "middle", nameGap: 40 },
      series: [
        {
          name: "Actual",
          type: "line",
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 3 },
          areaStyle: { opacity: 0.1 },
          data,
          markLine: markLines.length ? { data: markLines } : undefined,
          markArea: markAreas.length ? { data: markAreas } : undefined,
        },
      ],
    },
    { notMerge: true }
  );
}

/**
 * Compare overlay (Hoy vs Ayer) para RBC/PLT.
 * - Mantiene markers/bands SOLO del "today" para evitar ruido.
 * - Serie prev en gris translúcido.
 */
export function renderXYCurveCompare(chart, todayRes, prevRes) {
  const labelX = todayRes.labels && todayRes.labels.x ? todayRes.labels.x : "X";
  const labelY = todayRes.labels && todayRes.labels.y ? todayRes.labels.y : "Y";

  const todayData = buildXYData(todayRes);
  const prevData = buildXYData(prevRes);

  const markLines = buildMarkers(todayRes);
  const markAreas = buildBands(todayRes);

  chart.setOption(
    {
      title: {
        text: `${(todayRes.title || "Histograma")} · ${todayRes.date || ""} vs ${prevRes.date || ""}`.trim(),
        left: "center",
        top: 6,
      },
      grid: { left: 60, right: 18, top: 52, bottom: 46 },
      tooltip: {
        trigger: "axis",
        confine: true,
        axisPointer: { type: "cross" },
        formatter: (params) => {
          // params puede traer 1 o 2 series
          const lines = [];
          let xVal = null;

          for (const p of params || []) {
            if (!p || !p.value) continue;
            const x = p.value[0];
            const y = p.value[1];
            if (xVal == null) xVal = x;
            lines.push(`${p.seriesName}: <b>${y}</b>`);
          }

          const head = xVal == null ? "" : `X: <b>${xVal}</b>`;
          return [head, ...lines].filter(Boolean).join("<br/>");
        },
      },
      xAxis: { type: "value", name: labelX, nameLocation: "middle", nameGap: 28 },
      yAxis: { type: "value", name: labelY, nameLocation: "middle", nameGap: 40 },
      series: [
        {
          name: "Ayer",
          type: "line",
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2, opacity: 0.55, color: "#9aa0a6" },
          areaStyle: { opacity: 0.03, color: "#9aa0a6" },
          data: prevData,
          z: 1,
        },
        {
          name: "Hoy",
          type: "line",
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 3 },
          areaStyle: { opacity: 0.1 },
          data: todayData,
          markLine: markLines.length ? { data: markLines } : undefined,
          markArea: markAreas.length ? { data: markAreas } : undefined,
          z: 2,
        },
      ],
    },
    { notMerge: true }
  );
}

export function renderWbcBars(chart, res) {
  const cats = res.categories || [];
  const pct = res.pct || [];
  const abs = res.abs || [];

  chart.setOption(
    {
      title: { text: `WBC diferencial · ${res.date || ""}`.trim(), left: "center", top: 6 },
      grid: { left: 60, right: 18, top: 52, bottom: 46 },
      tooltip: {
        trigger: "axis",
        confine: true,
        axisPointer: { type: "shadow" },
        formatter: (params) => {
          const p = params && params[0];
          if (!p) return "";
          const idx = p.dataIndex;
          const a = abs[idx];
          const aTxt = a == null ? "" : `<br/>Abs: <b>${a}</b>`;
          return `${cats[idx]}<br/>%: <b>${(pct[idx] ?? 0).toFixed(1)}</b>${aTxt}`;
        },
      },
      xAxis: { type: "category", data: cats },
      yAxis: { type: "value", name: "Porcentaje (%)", nameLocation: "middle", nameGap: 40, max: 100 },
      series: [{ type: "bar", data: pct }],
    },
    { notMerge: true }
  );
}
