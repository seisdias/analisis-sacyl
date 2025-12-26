// web/assets/ui/modals/timeline_modal.js
import { escapeHtml } from "../utils/dom.js";
import { state } from "../../state.js";
import { apiJson } from "./modal_utils.js"

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

