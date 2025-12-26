// web/assets/kpis/treatment_kpis.js

import { toISODate } from "../charts/utils/date.js"

export function renderTreatmentKpis(treatmentIntervals, crossingsByParam, limitByParam, labelOfFn = null) {
  const host = document.getElementById("kpis");
  if (!host) return;

  // Limpia previos
  host.querySelectorAll(".kpi.kpi-treatment").forEach(n => n.remove());

  if (!Array.isArray(treatmentIntervals) || treatmentIntervals.length === 0) return;

  const DAY = 24 * 60 * 60 * 1000;
  const fmtParam = (k) => (typeof labelOfFn === "function" ? labelOfFn(k) : k);

  // Tarjetas pequeñas, mismo formato que KPIs normales
  const html = treatmentIntervals
    .slice()
    .sort((a, b) => a.start - b.start)
    .map(tx => {
      const startISO = toISODate(tx.start);
      const endISO = toISODate(tx.end);
      const endDay = Math.floor((tx.end - tx.start) / DAY) + 1;

      const rows = [];
      for (const [paramKey, limitVal] of (limitByParam || new Map()).entries()) {
        const list = (crossingsByParam && crossingsByParam.get(paramKey)) ? crossingsByParam.get(paramKey) : [];
        const hits = list.filter(c =>
          Array.isArray(c.treatments) && c.treatments.some(t => t.name === tx.name)
        );

        if (!hits.length) continue;

        // Primer cruce dentro del tratamiento (por fecha)
        hits.sort((a, b) => (a.ts ?? 0) - (b.ts ?? 0));
        const c = hits[0];
        const tinfo = c.treatments.find(t => t.name === tx.name);
        const day = tinfo?.day;

        rows.push(`• ${fmtParam(paramKey)} (${limitVal}): ${c.direction === "up" ? "↑" : "↓"} ${c.dateISO}${day ? ` (D+${day})` : ""}`);
      }

      const tipHtml = rows.length ? rows.join("<br>") : "Sin cruces clínicos para límites configurados.";

      return buildKpiCardHtml({
        title: "Tratamiento",
        value: tx.name,
        status: "good",
        subtitle: `Inicio D+1: ${startISO} · Fin: ${endISO} (D+${endDay})`,
        tipHtml
      }).replace('class="kpi ', 'class="kpi kpi-treatment '); // marca para limpieza
    })
    .join("");

  // IMPORTANTE: se inserta después de renderKpis() (ver chart.js)
  host.insertAdjacentHTML("afterbegin", html);
}

function buildKpiCardHtml({ title, value, status = "ok", subtitle = "", tipHtml = "" }) {
  // status: ok | warn | bad  (usa los mismos nombres que ya uses en tus KPIs normales)
  const tipBlock = tipHtml ? `<div class="tip">${tipHtml}</div>` : "";
  return `
    <div class="kpi ${status}">
      <div class="t">${title}</div>
      <div class="v">${value}</div>
      ${subtitle ? `<div class="s">${subtitle}</div>` : `<div class="s"></div>`}
      ${tipBlock}
    </div>
  `;
}