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

export function setDefaultEnabled() {
  const g = state.meta.groups.find((x) => x.name === state.currentGroup);
  state.enabledParams = new Set((g?.params || []).slice(0, 4));
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

export function openTimelineModal(timeline, { onChanged } = {}){
  // Crear modal si no existe
  let modal = document.getElementById("timelineModal");

  if(!modal){
    modal = document.createElement("div");
    modal.id = "timelineModal";
    modal.className = "modal hidden";
    modal.innerHTML = `
      <div class="modal-backdrop" id="tlBackdrop"></div>
      <div class="modal-card panel" style="max-width:920px; width: 92vw; margin: 40px auto 0 auto;">
        <div class="row" style="justify-content:space-between; align-items:center;">
          <b>Timeline</b>
          <button id="tlClose">Cerrar</button>
        </div>

        <div class="row" style="margin-top:10px; gap:8px;">
          <button id="tlTabStays" class="ghost">Ingresos</button>
          <button id="tlTabTx" class="ghost">Tratamientos</button>
          <span class="muted" id="tlHint" style="margin-left:auto;"></span>
        </div>

        <div id="tlBody" style="margin-top:10px;"></div>
      </div>
    `;
    document.body.appendChild(modal);

    // listeners SOLO después de crear el modal
    //const show = () => {
    //  modal.classList.remove("hidden");
    //  modal.setAttribute("aria-hidden", "false");

    //  // IMPORTANTÍSIMO: elimina cualquier inline que pueda impedir el cierre
    //  modal.style.removeProperty("display");
    //};

    const hide = () => {
      modal.classList.add("hidden");
      modal.setAttribute("aria-hidden", "true");

      // Cierre forzado aunque haya inline display:block
      modal.style.display = "none";
    };


    // Delegación robusta: funciona aunque el contenido interno cambie
    modal.addEventListener("click", (ev) => {
      // 1) botón cerrar (o cualquier elemento dentro con id tlClose)
      if (ev.target.closest("#tlClose")) {
        hide();
        return;
      }

      // 2) click en backdrop si existe
      if (ev.target.closest("#tlBackdrop")) {
        hide();
        return;
      }

      // 3) click fuera del card (overlay)
      const card = modal.querySelector(".modal-card");
      if (card && !card.contains(ev.target)) {
        hide();
      }
    });

    // Escape para cerrar
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && !modal.classList.contains("hidden")) {
        hide();
      }
    });

  }


//  function show(){
//    modal.classList.remove("hidden");
//    modal.setAttribute("aria-hidden", "false");
//    modal.style.position = "fixed";
//    modal.style.inset = "0";
//    modal.style.zIndex = "9999";
//    modal.style.display = "block";
//    modal.style.padding = "18px";
//  }

  function show(){
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    // Muy importante: si hide puso display:none, lo quitamos
    modal.style.removeProperty("display");
  }


  // Render tabs
  let active = "stays";

  const render = () => {
    const body = modal.querySelector("#tlBody");
    const hint = modal.querySelector("#tlHint");

    const stays = timeline.hospital_stays || [];
    const tx = timeline.treatments || [];

    if(active === "stays"){
      hint.textContent = `Ingresos: ${stays.length}`;
      body.innerHTML = renderStaysTable(stays);
      wireStays(body, stays);
    }else{
      hint.textContent = `Tratamientos: ${tx.length}`;
      body.innerHTML = renderTxTable(tx);
      wireTx(body, tx);
    }
  };

  modal.querySelector("#tlTabStays").onclick = () => { active = "stays"; render(); };
  modal.querySelector("#tlTabTx").onclick = () => { active = "tx"; render(); };

  render();
  show();

  // ---------- templates ----------
  function renderStaysTable(stays){
    return `
      <div class="row" style="justify-content:flex-end; margin-bottom:8px;">
        <button id="stAdd">+ Añadir ingreso</button>
      </div>
      <table class="table" style="width:100%;">
        <thead><tr>
          <th>Ingreso</th><th>Alta</th><th>Notas</th><th></th>
        </tr></thead>
        <tbody>
          ${stays.map(s => `
            <tr data-id="${s.id}">
              <td><input data-k="admission_date" type="date" value="${s.admission_date || ""}"></td>
              <td><input data-k="discharge_date" type="date" value="${s.discharge_date || ""}"></td>
              <td><input data-k="notes" type="text" value="${escapeHtml(s.notes || "")}"></td>
              <td style="white-space:nowrap;">
                <button data-act="save">Guardar</button>
                <button data-act="del" class="ghost">Borrar</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderTxTable(tx){
    return `
      <div class="row" style="justify-content:flex-end; margin-bottom:8px;">
        <button id="txAdd">+ Añadir tratamiento</button>
      </div>
      <table class="table" style="width:100%;">
        <thead><tr>
          <th>Nombre</th><th>Inicio</th><th>Fin</th><th>Días estándar</th><th>Notas</th><th></th>
        </tr></thead>
        <tbody>
          ${tx.map(t => `
            <tr data-id="${t.id}">
              <td><input data-k="name" type="text" value="${escapeHtml(t.name || "")}"></td>
              <td><input data-k="start_date" type="date" value="${t.start_date || ""}"></td>
              <td><input data-k="end_date" type="date" value="${t.end_date || ""}"></td>
              <td><input data-k="standard_days" type="number" value="${t.standard_days ?? ""}" style="width:90px"></td>
              <td><input data-k="notes" type="text" value="${escapeHtml(t.notes || "")}"></td>
              <td style="white-space:nowrap;">
                <button data-act="save">Guardar</button>
                <button data-act="del" class="ghost">Borrar</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  // ---------- wiring (calls API) ----------
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

  async function reloadAndRefresh(){
    timeline = await apiJson("GET", `/timeline?session_id=${encodeURIComponent(state.sessionId)}`);
    render();
    if (typeof onChanged === "function") {
      await onChanged();
    }
  }

  function readRow(tr){
    const data = {};
    tr.querySelectorAll("input[data-k]").forEach(inp => {
      data[inp.dataset.k] = inp.value === "" ? null : inp.value;
    });
    return data;
  }

  function wireStays(root){
    root.querySelector("#stAdd").onclick = async () => {
      await apiJson("POST",
        `/hospital_stays?session_id=${encodeURIComponent(state.sessionId)}`,
        { admission_date: null, discharge_date: null, notes: "" }
      );
      await reloadAndRefresh();
    };

    root.querySelectorAll("tr[data-id]").forEach(tr => {
      const id = tr.dataset.id;
      tr.querySelector('[data-act="save"]').onclick = async () => {
        const d = readRow(tr);
        await apiJson("PUT",
          `/hospital_stays/${encodeURIComponent(id)}?session_id=${encodeURIComponent(state.sessionId)}`,
          d
        );
        await reloadAndRefresh();
      };
      tr.querySelector('[data-act="del"]').onclick = async () => {
        await apiJson("DELETE",
          `/hospital_stays/${encodeURIComponent(id)}?session_id=${encodeURIComponent(state.sessionId)}`
        );
        await reloadAndRefresh();
      };
    });
  }

  function wireTx(root){
    root.querySelector("#txAdd").onclick = async () => {
      await apiJson("POST",
        `/treatments?session_id=${encodeURIComponent(state.sessionId)}`,
        { name: "", start_date: null, end_date: null, standard_days: null, notes: "" }
      );
      await reloadAndRefresh();
    };

    root.querySelectorAll("tr[data-id]").forEach(tr => {
      const id = tr.dataset.id;
      tr.querySelector('[data-act="save"]').onclick = async () => {
        const d = readRow(tr);
        // standard_days -> number/null
        if(d.standard_days !== null) d.standard_days = Number(d.standard_days);
        await apiJson("PUT",
          `/treatments/${encodeURIComponent(id)}?session_id=${encodeURIComponent(state.sessionId)}`,
          d
        );
        await reloadAndRefresh();
      };
      tr.querySelector('[data-act="del"]').onclick = async () => {
        await apiJson("DELETE",
          `/treatments/${encodeURIComponent(id)}?session_id=${encodeURIComponent(state.sessionId)}`
        );
        await reloadAndRefresh();
      };
    });
  }
}

function escapeHtml(s){
  const re = new RegExp('[&<>"\']', 'g');
  return String(s).replace(re, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function deepCopy(obj){
  return JSON.parse(JSON.stringify(obj || {}));
}

function numOrNull(v){
  if(v === "" || v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function openRangesModal({ current, defaults, onSave } = {}){
  let modal = document.getElementById("rangesModal");

  if(!modal){
    modal = document.createElement("div");
    modal.id = "rangesModal";
    modal.className = "modal hidden";
    modal.innerHTML = `
      <div class="modal-backdrop" id="rgBackdrop"></div>
      <div class="modal-card panel" style="max-width:980px; width:92vw; margin:40px auto 0 auto;">
        <div class="row" style="justify-content:space-between; align-items:center;">
          <b>Rangos normales</b>
          <button id="rgClose">Cerrar</button>
        </div>

        <div class="row" style="margin-top:10px; gap:8px; flex-wrap:wrap;" id="rgTabs"></div>

        <div style="margin-top:10px; max-height:60vh; overflow:auto;">
          <table class="table" style="width:100%;">
            <thead>
              <tr>
                <th style="min-width:260px;">Parámetro</th>
                <th style="width:140px;">Mín</th>
                <th style="width:140px;">Máx</th>
                <th style="width:120px;">Unidad</th>
              </tr>
            </thead>
            <tbody id="rgBody"></tbody>
          </table>
        </div>

        <div class="row" style="margin-top:12px; justify-content:flex-end; gap:8px;">
          <button id="rgReset" class="ghost">Reset (defaults)</button>
          <button id="rgCancel" class="ghost">Cancelar</button>
          <button id="rgSave">Guardar cambios</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    // Cierre robusto
    const hide = () => {
      modal.classList.add("hidden");
      modal.setAttribute("aria-hidden", "true");
      modal.style.display = "none";
    };

    modal.addEventListener("click", (ev) => {
      if (ev.target.closest("#rgClose")) return hide();
      if (ev.target.closest("#rgCancel")) return hide();
      if (ev.target.closest("#rgBackdrop")) return hide();

      /*const card = modal.querySelector(".modal-card");
      if (card && !card.contains(ev.target)) return hide();*/
    });

    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && !modal.classList.contains("hidden")) hide();
    });

    modal._hide = hide;
  }

  const show = () => {
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    modal.style.removeProperty("display"); // por si hide puso display:none
  };

  // --- staging local (no toca backend hasta Guardar)
  let working = deepCopy(current);
  const defaultsCopy = deepCopy(defaults);

  const allEntries = Object.entries(working).map(([key, r]) => ({
    key,
    ...(r || {}),
    category: (r && r.category) ? r.category : "Otros",
  }));

  const categories = Array.from(new Set(allEntries.map(e => e.category))).sort((a,b) => a.localeCompare(b));
  let activeCat = categories[0] || "Otros";

  const tabs = modal.querySelector("#rgTabs");
  const body = modal.querySelector("#rgBody");

  function renderTabs(){
    tabs.innerHTML = "";
    for(const cat of categories){
      const b = document.createElement("button");
      b.className = "ghost";
      b.textContent = cat;
      if(cat === activeCat){
        b.style.fontWeight = "700";
        b.style.textDecoration = "underline";
      }
      b.addEventListener("click", (ev) => {
        ev.stopPropagation();
        activeCat = cat;
        renderTable();
        renderTabs();
      });
      tabs.appendChild(b);
    }
  }

  function renderTable(){
    body.innerHTML = "";

    const rows = allEntries
      .filter(e => e.category === activeCat)
      .sort((a,b) => (a.label || a.key).localeCompare((b.label || b.key)));

    for(const e of rows){
      const r = working[e.key] || {};
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${escapeHtml(e.label || e.key)}</td>
        <td><input class="rgMin" type="number" step="any" value="${r.min ?? ""}" style="width:120px;"></td>
        <td><input class="rgMax" type="number" step="any" value="${r.max ?? ""}" style="width:120px;"></td>
        <td class="muted">${escapeHtml(e.unit || "")}</td>
      `;

      const inpMin = tr.querySelector(".rgMin");
      const inpMax = tr.querySelector(".rgMax");

      const markDirty = () => {
        // marca fila si difiere de current original (no defaults)
        const orig = (current && current[e.key]) ? current[e.key] : {};
        const curMin = numOrNull(inpMin.value);
        const curMax = numOrNull(inpMax.value);

        const dirty = (curMin !== (orig.min ?? null)) || (curMax !== (orig.max ?? null));
        tr.style.opacity = dirty ? "1" : "0.85";
        tr.style.fontWeight = dirty ? "600" : "400";
      };

      inpMin.addEventListener("input", () => {
        working[e.key] = { ...working[e.key], min: numOrNull(inpMin.value) };
        markDirty();
      });
      inpMax.addEventListener("input", () => {
        working[e.key] = { ...working[e.key], max: numOrNull(inpMax.value) };
        markDirty();
      });

      // estado inicial
      markDirty();

      body.appendChild(tr);
    }
  }

  // Reset local a defaults (no toca backend)
  modal.querySelector("#rgReset").onclick = () => {
    working = deepCopy(defaultsCopy);

    // refrescar referencias usadas por render (allEntries)
    // mantenemos mismas keys/categorías basadas en current; si defaults trae más/menos, lo normal es que sea igual
    for(const [k, v] of Object.entries(working)){
      // nada: ya está
    }
    renderTable();
  };

  // Guardar (bulk) + cerrar
  modal.querySelector("#rgSave").onclick = async () => {
    if (typeof onSave === "function") {
      // Solo enviamos {key:{min,max}} como espera el backend
      const payload = {};
      for(const [key, r] of Object.entries(working)){
        payload[key] = { min: r.min ?? null, max: r.max ?? null };
      }
      await onSave(payload);
    }
    modal._hide();
  };

  renderTabs();
  renderTable();
  show();
}

export async function openLimitsModal(){
  const sid = state.sessionId || "";

  const modal = document.createElement("div");
  modal.className = "modal";

  modal.innerHTML = `
    <div class="modal-card" style="max-width: 900px;">
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








