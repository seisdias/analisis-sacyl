// web/assets/timeline/timeline_builders.js

import { safeParseTs, uniqByKey } from "./timeline_utils.js";

export function timelineStyle(kind) {
  // No especifico colores globales (para no “imponer” estilo), pero sí diferenciamos patrón y grosor.
  if (kind === "hospital_admission") return { type: "solid", width: 2, opacity: 0.85 };
  if (kind === "hospital_discharge") return { type: "dashed", width: 2, opacity: 0.85 };
  if (kind === "treatment_start") return { type: "solid", width: 1, opacity: 0.70 };
  if (kind === "treatment_end") return { type: "dashed", width: 1, opacity: 0.70 };
  return { type: "dotted", width: 1, opacity: 0.6 };
}

export function groupTimelineEventsByDay(events) {
  const map = new Map(); // x -> { x, labels: [], kinds: Set }
  for (const e of events) {
    const key = e.x; // "YYYY-MM-DD"
    if (!map.has(key)) map.set(key, { x: key, items: [] });
    map.get(key).items.push(e);
  }

  const grouped = [];
  for (const [x, g] of map.entries()) {
    // Orden interno estable: ingresos antes que tratamientos (ajústalo si quieres)
    const order = (k) => {
      if (k === "hospital_admission") return 10;
      if (k === "hospital_discharge") return 20;
      if (k === "treatment_start") return 30;
      if (k === "treatment_end") return 40;
      return 99;
    };

    g.items.sort((a, b) => order(a.kind) - order(b.kind));

    const label = g.items.map(it => it.label).join(" · ");
    // Elegimos el “kind principal” para el estilo de la línea (prioridad configurable)
    const kind = g.items[0]?.kind || "other";

    grouped.push({
      x,
      kind,
      label,
      count: g.items.length,
      items: g.items,
    });
  }

  grouped.sort((a, b) => String(a.x).localeCompare(String(b.x)));
  return grouped;
}

export function buildTimelineEvents(timeline, defaultTreatmentDays) {
  const events = [];
  if (!timeline) return events;

  const stays = timeline.hospital_stays || [];
  for (const s of stays) {
    const a = safeParseTs(s.admission_date);
    const d = safeParseTs(s.discharge_date);

    if (a != null) {
      events.push({
        x: a,
        kind: "hospital_admission",
        label: "Ingreso",
        detail: s.notes || "",
      });
    }
    if (d != null) {
      events.push({
        x: d,
        kind: "hospital_discharge",
        label: "Alta",
        detail: s.notes || "",
      });
    }
  }

  const treatments = timeline.treatments || [];
  for (const t of treatments) {
    const start = safeParseTs(t.start_date);
    const end = safeParseTs(t.end_date);

    if (start != null) {
      events.push({
        x: start,
        kind: "treatment_start",
        label: `Inicio tto${t.name ? `: ${t.name}` : ""}`,
        detail: t.notes || "",
      });
    }

    // Si no hay end_date, NO pintamos fin aún (lo haremos más adelante con fin teórico)
    if (end != null) {
      events.push({
        x: end,
        kind: "treatment_end",
        label: `Fin tto${t.name ? `: ${t.name}` : ""}`,
        detail: t.notes || "",
      });
    }
  }

  // Orden + dedupe por kind+ts+label (evita duplicados si backend repite)
  const ordered = events
    .filter((e) => e.x != null)
    .sort((a, b) => a.x - b.x);

  return uniqByKey(ordered, (e) => `${e.kind}|${e.x}|${e.label}`);
}

export function buildTimelineMarkLineData(events) {
  if (!events || events.length === 0) return [];

  return events.map((e) => ({
    name: e.label,
    xAxis: e.x,                 // <-- ahora string "YYYY-MM-DD"
    lineStyle: timelineStyle(e.kind),
  }));
}

export function buildGlobalTimelineMarkLine(events, globalExtent) {
  if (!events || events.length === 0) return null;

  const { minTs, maxTs } = globalExtent || {};
  // Si tenemos extent, filtramos eventos fuera del rango para no “ensuciar” el zoom
  const filtered = (minTs != null && maxTs != null)
    ? events.filter((e) => e.x >= minTs && e.x <= maxTs)
    : events;

  if (filtered.length === 0) return null;

  // ECharts markLine requiere data: [{ xAxis: <value>, name: <...>, lineStyle: {...} }, ...]
  const data = filtered.map((e) => ({
    name: e.label,
    xAxis: e.x,               // xAxis time → timestamp OK
    lineStyle: timelineStyle(e.kind),
    // Tooltip: usamos un formatter general, pero dejamos info en el nombre.
  }));

  return {
    silent: true,
    symbol: ["none", "none"],
    // label se verá arriba; si molesta lo quitamos
    label: {
      show: true,
      formatter: (p) => p.name || "",
      rotate: 90,
      position: "insideEndTop",
    },
    data,
  };
}

export function buildTimelineMarkAreas(timeline) {
  if (!timeline) return [];

  const areas = [];

  const stays = timeline.hospital_stays || [];
  for (const s of stays) {
    const a = safeParseTs(s.admission_date);
    const d = safeParseTs(s.discharge_date);
    if (a != null && d != null && d >= a) {
      areas.push({
        kind: "hospital",
        from: a,
        to: d,
        label: "Ingreso hospitalario",
      });
    }
  }

  const defaultDays =
    timeline.config?.treatment_default_days != null
      ? timeline.config.treatment_default_days
      : null;

  const treatments = timeline.treatments || [];
  for (const t of treatments) {
    const start = safeParseTs(t.start_date);
    if (start == null) continue;

    let end = safeParseTs(t.end_date);
    if (end == null) {
      const days =
        t.standard_days != null
          ? t.standard_days
          : defaultDays;
      if (days != null) {
        end = start + days * 24 * 60 * 60 * 1000;
      }
    }

    if (end != null && end >= start) {
      areas.push({
        kind: "treatment",
        from: start,
        to: end,
        label: t.name ? `Tratamiento: ${t.name}` : "Tratamiento",
      });
    }
  }

  return areas;
}

export function buildTimelineMarkAreaOption(areas) {
  if (!areas || areas.length === 0) return null;

  const hospitalColor = "rgba(59,130,246,0.10)";   // azul/gris
  const treatmentColor = "rgba(16,185,129,0.12)"; // verde

  return {
    silent: true,
    data: areas.map((a) => ([
      {
        xAxis: a.from,
        itemStyle: {
          color: a.kind === "hospital" ? hospitalColor : treatmentColor,
        },
        label: {
          show: false,
        },
      },
      {
        xAxis: a.to,
      },
    ])),
  };
}
