// web/assets/ui.js
import { state, labelOf } from "./state.js";

export function setStatus(ok, el, text) {
  el.textContent = text;
  el.style.borderColor = ok ? "#bbf7d0" : "#fecaca";
  el.style.color = ok ? "#166534" : "#991b1b";
  el.style.background = ok ? "#f0fdf4" : "#fef2f2";
}

export function buildGroupSelect(selectEl) {
  selectEl.innerHTML = "";
  state.meta.groups.forEach((g) => {
    const opt = document.createElement("option");
    opt.value = g.name;
    opt.textContent = g.name;
    selectEl.appendChild(opt);
  });

  state.currentGroup = state.meta.groups[0].name;
  selectEl.value = state.currentGroup;
}

/*export function setDefaultEnabled() {
  const g = state.meta.groups.find((x) => x.name === state.currentGroup);
  state.enabledParams = new Set((g?.params || []).slice(0, 4));
}*/

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

export function buildParamList(listEl, searchEl, { onToggle } = {}) {
  const g = state.meta.groups.find((x) => x.name === state.currentGroup);
  const query = (searchEl.value || "").toLowerCase().trim();

  const params = (g?.params || []).filter((p) => {
    if (!query) return true;
    return (
      p.toLowerCase().includes(query) ||
      labelOf(p).toLowerCase().includes(query)
    );
  });

  listEl.innerHTML = "";

  for (const p of params) {
    const row = document.createElement("label");
    row.className = "param-row";

    // Creamos nodos reales (sin ids) => sin colisiones, sin getElementById
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = state.enabledParams.has(p);
    cb.dataset.param = p;

    const text = document.createElement("span");
    text.textContent = labelOf(p);

    row.appendChild(cb);
    row.appendChild(document.createTextNode(" "));
    row.appendChild(text);

    cb.addEventListener("change", async () => {
      if (cb.checked) state.enabledParams.add(p);
      else state.enabledParams.delete(p);

      if (typeof onToggle === "function") {
        await onToggle();
      }
    });

    listEl.appendChild(row);
  }
}

export function bindEvents({ groupSelect, search, btnAll, btnNone, paramList, onChange }) {
  const notify = async () => {
    if (typeof onChange === "function") {
      await onChange();
    }
  };

  groupSelect.addEventListener("change", async () => {
    state.currentGroup = groupSelect.value;
    setDefaultEnabled();
    buildParamList(paramList, search, { onToggle: notify });
    await notify();
  });

  // Search solo reconstruye lista (no refresca chart) porque NO cambia enabledParams
  search.addEventListener("input", () => {
    buildParamList(paramList, search, { onToggle: notify });
  });

  btnAll.addEventListener("click", async () => {
    const g = state.meta.groups.find((x) => x.name === state.currentGroup);
    state.enabledParams = new Set(g?.params || []);
    buildParamList(paramList, search, { onToggle: notify });
    await notify();
  });

  btnNone.addEventListener("click", async () => {
    state.enabledParams = new Set();
    buildParamList(paramList, search, { onToggle: notify });
    await notify();
  });
}


/******************
Boton Timelines
******************/



export async function openLimitsModal(){
  const sid = state.sessionId || "";

  const modal = document.createElement("div");
  modal.className = "modal";

  modal.innerHTML = `
    <div class="modal-card panel" style="max-width: 900px;">
      <div class="modal-head">
        <div>
          <div style="font-weight:700;">Límites por parámetro</div>
          <div class="muted" style="margin-top:4px;">
            Un único valor por parámetro (ej: leucocitos=1000, neutrófilos=500). Vacío = sin límite.
          </div>
        </div>
        <div class="row" style="gap:8px;">
          <button id="plClose">Cerrar</button>
        </div>
      </div>

      <div class="row" style="margin-top:10px; gap:8px;">
        <span class="pill">Grupo: <b>${state.currentGroup}</b></span>
        <span class="muted" id="plHint" style="margin-left:auto;"></span>
      </div>

      <div id="plBody" style="margin-top:10px;"></div>

      <div class="row" style="margin-top:12px; gap:8px; justify-content:flex-end;">
        <button id="plReset" class="ghost">Vaciar todos</button>
        <button id="plCancel" class="ghost">Cancelar</button>
        <button id="plSave">Guardar</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // --- helpers API (igual patrón que Timeline)
  async function apiJson(method, path, body){
    const opts = { method, headers: {} };
    if(body !== undefined){
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(`${state.base}${path}`, opts);
    if(!res.ok){
      let txt = `${res.status} ${res.statusText}`;
      try{
        const j = await res.json();
        txt = j.detail || j.error || JSON.stringify(j);
      }catch{}
      throw new Error(txt);
    }
    return await res.json();
  }

  // --- estado local del modal
  const g = state.meta.groups.find(x => x.name === state.currentGroup);
  const params = (g?.params || []);

  let original = new Map(); // paramKey -> {id, value, label, enabled}
  let draft = new Map();    // paramKey -> string (input raw)

  // --- cargar límites actuales
  async function load(){
    const j = await apiJson("GET", `/param_limits?session_id=${encodeURIComponent(sid)}`);
    const list = (j.limits || []);
    original = new Map(list.map(x => [x.param_key, x]));
    draft = new Map();

    for(const p of params){
      const row = original.get(p);
      draft.set(p, row && row.value != null ? String(row.value) : "");
    }
  }

  // --- render tabla
  function render(){
    const plBody = modal.querySelector("#plBody");
    const hint = modal.querySelector("#plHint");

    const rows = params.map((p) => {
      const v = draft.get(p) ?? "";
      return `
        <tr data-key="${p}">
          <td style="white-space:nowrap;"><b>${labelOf(p)}</b><div class="muted">${p}</div></td>
          <td style="width:220px;">
            <input class="plVal" type="number" step="any" placeholder="(vacío = sin límite)" value="${v}" style="width:100%;"/>
          </td>
        </tr>
      `;
    }).join("");

    plBody.innerHTML = `
      <table class="table" style="width:100%;">
        <thead>
          <tr>
            <th>Parámetro</th>
            <th>Límite</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;

    // listeners inputs
    plBody.querySelectorAll("input.plVal").forEach((inp) => {
      inp.addEventListener("input", (e) => {
        const tr = e.target.closest("tr");
        const key = tr?.dataset?.key;
        if(!key) return;
        draft.set(key, e.target.value);
      });
    });

    // hint cambios
    let changed = 0;
    for(const p of params){
      const before = original.get(p)?.value;
      const nowStr = (draft.get(p) ?? "").trim();
      const now = nowStr === "" ? null : Number(nowStr);
      const b = (before == null ? null : Number(before));
      if(now !== b) changed++;
    }
    hint.textContent = changed ? `${changed} cambios pendientes` : `Sin cambios`;
  }

  function close(){
    modal.remove();
  }

  // --- acciones
  modal.querySelector("#plClose").addEventListener("click", close);
  modal.querySelector("#plCancel").addEventListener("click", close);

  modal.querySelector("#plReset").addEventListener("click", () => {
    for(const p of params) draft.set(p, "");
    render();
  });

  modal.querySelector("#plSave").addEventListener("click", async () => {
    // aplicar cambios uno a uno (simple y seguro)
    for(const p of params){
      const row = original.get(p); // puede ser undefined
      const raw = (draft.get(p) ?? "").trim();

      // vacío => borrar si existía
      if(raw === ""){
        if(row?.id != null){
          await apiJson("DELETE", `/param_limits/${encodeURIComponent(row.id)}?session_id=${encodeURIComponent(sid)}`);
        }
        continue;
      }

      const val = Number(raw);
      if(!Number.isFinite(val)) continue;

      const body = {
        param_key: p,
        value: val,
        label: null,
        enabled: 1,
      };

      if(row?.id != null){
        await apiJson("PUT", `/param_limits/${encodeURIComponent(row.id)}?session_id=${encodeURIComponent(sid)}`, body);
      }else{
        await apiJson("POST", `/param_limits?session_id=${encodeURIComponent(sid)}`, body);
      }
    }

    close();
  });

  await load();
  render();
}








