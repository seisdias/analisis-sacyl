import { state, labelOf } from "./state.js";
import { refreshChart } from "./chart.js";

export function setStatus(ok, el, text){
  el.textContent = text;
  el.style.borderColor = ok ? "#bbf7d0" : "#fecaca";
  el.style.color = ok ? "#166534" : "#991b1b";
  el.style.background = ok ? "#f0fdf4" : "#fef2f2";
}

export function buildGroupSelect(selectEl){
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

export function setDefaultEnabled(){
  const g = state.meta.groups.find(x => x.name === state.currentGroup);
  state.enabledParams = new Set(g.params.slice(0, 4));
}

export function buildParamList(listEl, searchEl){
  const g = state.meta.groups.find(x => x.name === state.currentGroup);
  const query = (searchEl.value || "").toLowerCase().trim();
  const params = g.params.filter(p =>
    !query || p.toLowerCase().includes(query) || labelOf(p).toLowerCase().includes(query)
  );

  listEl.innerHTML = "";
  params.forEach(p => {
    const id = `chk_${p}`;
    const row = document.createElement("label");
    row.innerHTML = `<input type="checkbox" id="${id}"> <span>${labelOf(p)}</span>`;
    listEl.appendChild(row);

    const cb = document.getElementById(id);
    cb.checked = state.enabledParams.has(p);
    cb.addEventListener("change", async () => {
      if(cb.checked) state.enabledParams.add(p);
      else state.enabledParams.delete(p);
      await refreshChart();
    });
  });
}

export function bindEvents({ groupSelect, search, btnAll, btnNone, paramList }){
  groupSelect.addEventListener("change", async () => {
    state.currentGroup = groupSelect.value;
    setDefaultEnabled();
    buildParamList(paramList, search);
    await refreshChart();
  });

  search.addEventListener("input", () => buildParamList(paramList, search));

  btnAll.addEventListener("click", async () => {
    const g = state.meta.groups.find(x => x.name === state.currentGroup);
    state.enabledParams = new Set(g.params);
    buildParamList(paramList, search);
    await refreshChart();
  });

  btnNone.addEventListener("click", async () => {
    state.enabledParams = new Set();
    buildParamList(paramList, search);
    await refreshChart();
  });
}
