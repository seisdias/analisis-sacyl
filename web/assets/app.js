import { getBaseUrl, apiGet } from "./api.js";
import { state } from "./state.js";
import { initChart, refreshChart } from "./chart.js";
import { setStatus, buildGroupSelect, setDefaultEnabled, buildParamList, bindEvents, openTimelineModal, openRangesModal } from "./ui.js";


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


    setStatus(true, statusEl, "Conectado");

    initChart(chartDom);
    buildGroupSelect(groupSelect);
    setDefaultEnabled();
    buildParamList(paramList, search, { onToggle: refreshChart });
    bindEvents({ groupSelect, search, btnAll, btnNone, paramList, onChange: refreshChart });
    bindImportPdfs();
    bindTimelineCrud();
    bindRanges();


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
      // refrescamos ranges por si han cambiado
      const r = await apiGet(
        state.base,
        state.sessionId ? `/ranges?session_id=${encodeURIComponent(state.sessionId)}` : "/ranges"
      );
      state.ranges = r.ranges || {};

      openRangesModal({
        ranges: state.ranges,
        onReset: async () => {
          await fetch(`${state.base}/ranges/reset`, { method: "POST" });
          const rr = await apiGet(
            state.base,
            state.sessionId ? `/ranges?session_id=${encodeURIComponent(state.sessionId)}` : "/ranges"
          );
          state.ranges = rr.ranges || {};
          await refreshChart();
        },
        onUpdate: async (key, min, max) => {
          await fetch(`${state.base}/ranges/${encodeURIComponent(key)}`, {
            method: "PUT",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ min, max }),
          });
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




