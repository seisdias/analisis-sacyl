// web/assets/clinical/defaults.js

import { state } from "../state.js";

export function setDefaultEnabled() {
  const g = state.meta.groups.find((x) => x.name === state.currentGroup);
  const params = g?.params || [];

  // Defaults clínicos por categoría
  const DEFAULTS_BY_GROUP = {
    // ─── HEMATOLOGÍA ─────────────────────────────
    "Hematología — Serie blanca": [
      "leucocitos",
      "neutrofilos_abs",
      "linfocitos_abs",
      "monocitos_abs",
    ],

    "Hematología — Serie roja": [
      "hematies",
      "hematocrito",
      "hemoglobina",
    ],

    "Hematología — Plaquetas": [
      "plaquetas",
      "vcm",
    ],

    // ─── BIOQUÍMICA ──────────────────────────────
    "Bioquímica — Electrolitos": [
      "calcio",
      "fosforo",
      "potasio",
      "cloro",
      "sodio",
    ],

    "Bioquímica — Lípidos": [
      "colesterol_total",
      "trigliceridos",
    ],

    "Bioquímica — Metabolismo": [
      "urea",
      "glucosa",
      "creatinina",
    ],

    "Bioquímica — Hierro": [
      "ferritina",
      "hierro",
    ],

    "Bioquímica — Vitaminas": [
      "vitamina_b12",
    ],

    // ─── ORINA ───────────────────────────────────
    "Orina — Cuantitativa": [
      "ph_orina",
      "sodio_orina",
    ],
  };

  const preferred = DEFAULTS_BY_GROUP[state.currentGroup];

  if (preferred && preferred.length) {
    // solo los parámetros que existan realmente en este grupo
    const valid = preferred.filter((p) => params.includes(p));
    if (valid.length) {
      state.enabledParams = new Set(valid);
      return;
    }
  }

  // Fallback: comportamiento actual
  state.enabledParams = new Set(params.slice(0, 4));
}
