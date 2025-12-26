// web/assets/ui/modals/limits_modal.js
import { state } from "../../state.js";

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
