import { getBaseUrl, apiGet } from "./api.js";
import { state } from "./state.js";
import { initChart, refreshChart } from "./chart.js";
import { setStatus, buildGroupSelect, setDefaultEnabled, buildParamList, bindEvents } from "./ui.js";

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

    state.meta = await apiGet(state.base, "/meta");
    const rangesResp = await apiGet(state.base, "/ranges");
    state.ranges = rangesResp.ranges || {};


    setStatus(true, statusEl, "Conectado");

    initChart(chartDom);
    buildGroupSelect(groupSelect);
    setDefaultEnabled();
    buildParamList(paramList, search);

    bindEvents({ groupSelect, search, btnAll, btnNone, paramList });

    await refreshChart();
  } catch(e){
    console.error(e);
    setStatus(false, statusEl, "Error");
  }
}

init();
