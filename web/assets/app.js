// web/assets/app.js

import { getBaseUrl, apiGet } from "./api.js";
import { state } from "./state.js";
import { initChart, refreshChart } from "./charts/chart.js";
import { setStatus, buildGroupSelect, setDefaultEnabled, buildParamList, bindEvents, openLimitsModal } from "./ui.js";
import { openRangesModal } from "./ui/modals/ranges_modal.js"
import { openTimelineModal, apiJson } from "./ui/modals/timeline_modal.js"

async function init(){
  const statusEl = document.getElementById("status");
  const groupSelect = document.getElementById("groupSelect");
  const paramList = document.getElementById("paramList");
  const search = document.getElementById("search");
  const btnAll = document.getElementById("btnAll");
  const btnNone = document.getElementById("btnNone");
  const chartDom = document.getElementById("chart");

  try{
    state.base = getBaseUrl();
    if(!state.base) throw new Error("Falta parámetro ?base= en la URL");

    const urlParams = new URLSearchParams(window.location.search);
    state.sessionId = urlParams.get("session_id") || "";
    if(!state.sessionId) throw new Error("Falta parámetro ?session_id= en la URL");

    const url = new URL(window.location.href);
    state.sessionId = url.searchParams.get("session_id");

    if(!state.sessionId){
    console.warn("Dashboard sin session_id (modo legacy)");
}

    state.meta = await apiGet(state.base, "/meta");
    const rangesResp = await apiGet(
        state.base,
        state.sessionId ? `/ranges?session_id=${encodeURIComponent(state.sessionId)}` : "/ranges"
    );

    state.ranges = rangesResp.ranges || {};
    // --- Sustitución total del selector: grupos por categorías clínicas (como Rangos)
    state.meta.groups = buildGroupsFromRanges(state.meta, state.ranges);



    setStatus(true, statusEl, "Conectado");

    initChart(chartDom);
    buildGroupSelect(groupSelect);
    setDefaultEnabled();
    buildParamList(paramList, search, { onToggle: refreshChart });
    bindEvents({ groupSelect, search, btnAll, btnNone, paramList, onChange: refreshChart });
    bindImportPdfs();
    bindTimelineCrud();
    bindRanges();
    bindLimits();



    await refreshChart();
  } catch(e){
    console.error(e);
    setStatus(false, statusEl, "Error");
  }
}

init();

function hasPywebview(){
  return !!(window.pywebview && window.pywebview.api);
}

function buildGroupsFromRanges(meta, ranges) {
  const defs = meta?.defs || {};
  const originalGroups = meta?.groups || [];

  // category -> Set(params)
  const byCat = new Map();

  for (const [param, r] of Object.entries(ranges || {})) {
    const cat = (r && r.category) ? String(r.category).trim() : "";
    if (!cat) continue;
    if (!defs[param]) continue; // solo params que existan en meta.defs
    if (!byCat.has(cat)) byCat.set(cat, new Set());
    byCat.get(cat).add(param);
  }

  // Si por lo que sea no tenemos categorías, caemos al comportamiento legacy
  if (byCat.size === 0) return originalGroups;

  const groups = Array.from(byCat.entries()).map(([name, set]) => {
    const params = Array.from(set);

    // Orden estable: por label si existe, si no por key
    params.sort((a, b) => {
      const la = (defs[a]?.label || a).toLowerCase();
      const lb = (defs[b]?.label || b).toLowerCase();
      return la.localeCompare(lb);
    });

    return { name, params };
  });

  // Orden de grupos: Hematología primero, y dentro blanca/roja/plaquetas al inicio
  const prio = (name) => {
    const n = String(name);
    if (n === "Hematología — Serie blanca") return 10;
    if (n === "Hematología — Serie roja") return 20;
    if (n === "Hematología — Plaquetas") return 30;
    if (n.startsWith("Hematología —")) return 40;
    if (n.startsWith("Bioquímica —")) return 50;
    if (n.startsWith("Orina —")) return 60;
    if (n.startsWith("Gasometría —")) return 70;
    return 99;
  };

  groups.sort((a, b) => {
    const pa = prio(a.name);
    const pb = prio(b.name);
    if (pa !== pb) return pa - pb;
    return String(a.name).localeCompare(String(b.name), "es");
  });

  return groups;
}


function bindImportPdfs(){
  const btn = document.getElementById("btnImportPdfs");
  const input = document.getElementById("fileImportPdfs");
  const statusEl = document.getElementById("status");
  if(!btn) return;

  btn.addEventListener("click", async () => {
    try{
      // --- pywebview: rutas nativas ---
      if(hasPywebview() && window.pywebview.api.pick_import_pdfs){
        const paths = await window.pywebview.api.pick_import_pdfs();
        if(!paths || paths.length === 0) return;

        setStatus(true, statusEl, "Importando PDFs…");

        const res = await fetch(`${state.base}/imports/from_paths?session_id=${encodeURIComponent(state.sessionId)}`, {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify({ pdf_paths: paths }),
        });
        if(!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const j = await res.json();

        await refreshChart();

        if(j.errors && j.errors.length){
          setStatus(false, statusEl, `Importado: ${j.imported}, Errores: ${j.errors.length}`);
        } else {
          setStatus(true, statusEl, `Importado: ${j.imported}`);
        }
        return;
      }

      // --- navegador: upload ---
      if(input){
        input.value = "";
        input.click();
      } else {
        alert("Importación no disponible: falta input file");
      }
    } catch(e){
      console.error(e);
      setStatus(false, statusEl, `Error importando: ${e.message}`);
    }
  });

  // Upload en navegador
  if(input){
    input.addEventListener("change", async () => {
      const statusEl = document.getElementById("status");
      try{
        const files = Array.from(input.files || []);
        if(files.length === 0) return;

        setStatus(true, statusEl, "Subiendo PDFs…");

        const fd = new FormData();
        for(const f of files){
          fd.append("pdf_files", f);
        }

        const res = await fetch(`${state.base}/imports/upload?session_id=${encodeURIComponent(state.sessionId)}`, {
          method: "POST",
          body: fd,
        });
        if(!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const j = await res.json();

        await refreshChart();

        if(j.errors && j.errors.length){
          setStatus(false, statusEl, `Importado: ${j.imported}, Errores: ${j.errors.length}`);
        } else {
          setStatus(true, statusEl, `Importado: ${j.imported}`);
        }
      } catch(e){
        console.error(e);
        setStatus(false, statusEl, `Error importando: ${e.message}`);
      }
    });
  }
}

/*****
Timelines
*****/



function bindTimelineCrud(){
  const btn = document.getElementById("btnTimeline");
  if(!btn) return;

  btn.addEventListener("click", async () => {
    try{
      const t = await apiJson("GET", `/timeline?session_id=${encodeURIComponent(state.sessionId)}`);
      openTimelineModal(t, { onChanged: refreshChart });
    }catch(e){
      console.error(e);
      const statusEl = document.getElementById("status");
      setStatus(false, statusEl, `Error timeline: ${e.message}`);
    }
  });
}

function bindRanges(){
  const btn = document.getElementById("btnRanges");
  if(!btn) return;

  btn.addEventListener("click", async () => {
    try{
      const currentResp = await apiGet(state.base, "/ranges");
      const defaultsResp = await apiGet(state.base, "/ranges/defaults");

      const current = currentResp.ranges || {};
      const defaults = defaultsResp.ranges || {};

      openRangesModal({
        current,
        defaults,
        onSave: async (rangesToSave) => {
          // Bulk save
          await fetch(`${state.base}/ranges/bulk`, {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ ranges: rangesToSave }),
          });

          // Refrescar chart al cerrar tras guardar
          const refreshed = await apiGet(state.base, "/ranges");
          state.ranges = refreshed.ranges || {};
          await refreshChart();
        }
      });

    }catch(e){
      console.error(e);
      const statusEl = document.getElementById("status");
      setStatus(false, statusEl, `Error rangos: ${e.message}`);
    }
  });
}

function bindLimits(){
  const btnLimits = document.getElementById("btnLimits");
  if(!btnLimits){
    return
  }

  btnLimits?.addEventListener("click", async () => {
    await openLimitsModal();
    await refreshChart();
  });

}





