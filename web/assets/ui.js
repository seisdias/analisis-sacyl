// web/assets/ui.js
import { state, labelOf } from "./state.js";
import { setDefaultEnabled } from "./clinical/defaults.js"

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








