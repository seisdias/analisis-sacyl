// web/assets/ui/modals/ranges_modal.js
import { escapeHtml, deepCopy, numOrNull } from "../utils/dom.js";

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
