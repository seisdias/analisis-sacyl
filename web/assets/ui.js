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

export function openRangesModal( ranges, { onChanged } = {}){
  let modal = document.getElementById("rangesModal");

  if(!modal){
    modal = document.createElement("div");
    modal.id = "rangesModal";
    modal.className = "modal hidden";
    modal.innerHTML = `
      <div class="modal-backdrop" id="rgBackdrop"></div>
      <div class="modal-card panel" style="max-width:900px; width:92vw; margin:40px auto 0 auto;">
        <div class="row" style="justify-content:space-between; align-items:center;">
          <b>Rangos normales</b>
          <button id="rgClose">Cerrar</button>
        </div>

        <div class="row" style="margin-top:10px; justify-content:flex-end;">
          <button id="rgReset" class="ghost">Restaurar valores originales</button>
        </div>

        <div style="margin-top:10px; max-height:60vh; overflow:auto;">
          <table class="table" style="width:100%;">
            <thead>
              <tr>
                <th>Parámetro</th>
                <th>Mín</th>
                <th>Máx</th>
              </tr>
            </thead>
            <tbody id="rgBody"></tbody>
          </table>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    const hide = () => {
      modal.classList.add("hidden");
      modal.style.display = "none";
    };
    const show = () => {
      modal.classList.remove("hidden");
      modal.style.display = "block";
    };

    modal.addEventListener("click", (ev) => {
      if (ev.target.closest("#rgClose")) return hide();
      if (ev.target.closest("#rgBackdrop")) return hide();
      const card = modal.querySelector(".modal-card");
      if (card && !card.contains(ev.target)) return hide();
    });

    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && !modal.classList.contains("hidden")) hide();
    });

    modal._show = show;
    modal._hide = hide;
  }

  // Render tabla
  const body = modal.querySelector("#rgBody");
  body.innerHTML = "";

  Object.entries(ranges || {}).forEach(([key, r]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.label || key}</td>
      <td><input type="number" step="any" value="${r.min ?? ""}" data-k="min"></td>
      <td><input type="number" step="any" value="${r.max ?? ""}" data-k="max"></td>
    `;
    body.appendChild(tr);

    tr.querySelectorAll("input").forEach(inp => {
      inp.addEventListener("change", async () => {
        const min = tr.querySelector('[data-k="min"]').value;
        const max = tr.querySelector('[data-k="max"]').value;

        await fetch(`${state.base}/ranges/${encodeURIComponent(key)}`, {
          method: "PUT",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify({
            min: min === "" ? null : Number(min),
            max: max === "" ? null : Number(max),
          })
        });

        if (typeof onChanged === "function") await onChanged();
      });
    });
  });

  // Reset global
  modal.querySelector("#rgReset").onclick = async () => {
    await fetch(`${state.base}/ranges/reset`, { method: "POST" });
    if (typeof onChanged === "function") await onChanged();
    modal._hide();
  };

  modal._show();
}






