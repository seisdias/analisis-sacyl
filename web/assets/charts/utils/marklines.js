// web/assets/charts/utils/marklines.js

export function staggerMarkLineLabels(data, stepPx = 26) {
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

export function buildLimitsMarkLine(limits){
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

export function mergeMarkLines(a, b) {
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


