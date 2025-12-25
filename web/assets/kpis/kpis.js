// web/assets/kpis/kpis.js

import { fmt } from "./../core/format.js"

export function renderKpis(items) {
  const el = document.getElementById("kpis");
  if (!el) return;

  if (!items || items.length === 0) {
    el.innerHTML = "";
    return;
  }

  el.innerHTML = items
    .map((it) => {
      const unitTxt = it.unit ? ` ${it.unit}` : "";
      const deltaTxt = it.delta == null ? "Δ —" : `Δ ${fmt(it.delta)}`;
      const cls =
        it.statusKind === "good"
          ? "kpi good"
          : it.statusKind === "bad"
          ? "kpi bad"
          : "kpi";

      const pillCls =
        it.statusKind === "good"
          ? "pill good"
          : it.statusKind === "bad"
          ? "pill bad"
          : "pill";

      const tipAlerts =
        it.lastAlerts && it.lastAlerts.length
          ? it.lastAlerts
              .map((a) => {
                const tag = a.flag === "below" ? "bajo" : "alto";
                return `
                  <div class="tip-row">
                    <span class="muted">${a.date}</span>
                    <span><b>${fmt(a.value)}</b> <span class="pill bad">${tag}</span></span>
                  </div>
                `;
              })
              .join("")
          : `<div class="muted">Sin alertas recientes.</div>`;

      return `
        <div class="${cls}">
          <div class="t">${it.name}</div>
          <div class="v">${fmt(it.lastValue)}${unitTxt}</div>
          <div class="s">${deltaTxt} • Estado: ${it.status}${
        it.alerts ? ` • Alertas: ${it.alerts}` : ""
      }</div>

          <div class="tip">
            <div class="h">${it.name}<span class="${pillCls}">${it.status}</span></div>

            <div class="tip-row"><span class="muted">Última fecha</span><span>${
              it.lastDate ?? "—"
            }</span></div>
            <div class="tip-row"><span class="muted">Rango normal</span><span>${
              it.rangeText ?? "—"
            }</span></div>
            <div class="tip-row"><span class="muted">Último valor</span><span><b>${fmt(
              it.lastValue
            )}</b>${unitTxt}</span></div>
            <div class="tip-row"><span class="muted">Delta</span><span>${deltaTxt}</span></div>

            <div class="alert">
              <div class="h" style="font-size:12px;">Alertas recientes</div>
              ${tipAlerts}
            </div>
          </div>
        </div>
      `;
    })
    .join("");
}
