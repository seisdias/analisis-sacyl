function fmt(n){
  if(n == null) return "—";
  const v = Number(n);
  if(Number.isNaN(v)) return "—";
  if(Math.abs(v) >= 100) return v.toFixed(0);
  if(Math.abs(v) >= 10) return v.toFixed(1);
  return v.toFixed(2);
}

export function renderKpis(items){
  const el = document.getElementById("kpis");
  if(!el) return;

  if(!items || items.length === 0){
    el.innerHTML = "";
    return;
  }

  el.innerHTML = items.map(it => {
    const deltaTxt = (it.delta == null) ? "Δ —" : `Δ ${fmt(it.delta)}`;
    const unitTxt = it.unit ? ` ${it.unit}` : "";
    const alertsTxt = it.alerts ? ` • Alertas: ${it.alerts}` : "";
    const cls = it.statusKind === "good" ? "kpi good" : (it.statusKind === "bad" ? "kpi bad" : "kpi");

    return `
      <div class="${cls}">
        <div class="t">${it.name}</div>
        <div class="v">${fmt(it.lastValue)}${unitTxt}</div>
        <div class="s">${deltaTxt} • Estado: ${it.status}${alertsTxt}</div>
      </div>
    `;
  }).join("");
}
