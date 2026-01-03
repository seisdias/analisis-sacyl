// web/assets/ui/modals/histograms_modal.js
import { apiJson } from "./modal_utils.js";
import { state } from "../../state.js";

import { createProxyClient } from "./histograms/proxy_client.js";
import { renderXYCurve, renderXYCurveCompare, renderWbcBars } from "./histograms/renderers.js";
import { setupAdvancedTimeline } from "./histograms/advanced_timeline.js";

const HG_DEBUG = true;
const hgLog = (...args) => {
  if (HG_DEBUG) console.debug("[histograms]", ...args);
};

export async function openHistogramsModal() {
  const modal = document.createElement("div");
  modal.className = "modal";

  modal.innerHTML = `
    <div class="modal-card panel" style="max-width:900px; width:92vw;">
      <div class="modal-head">
        <div>
          <div style="font-weight:700;">Histogramas (Hematología)</div>
          <div class="muted" style="margin-top:4px;">
            Visualización proxy (no bins reales del analizador)
          </div>
        </div>
        <button id="hgClose" class="btn">Cerrar</button>
      </div>

      <div class="row" style="gap:12px; align-items:flex-end; margin-top:10px;">
        <div style="flex:1; min-width:240px;">
          <label class="muted" style="display:block; font-size:12px; margin-bottom:6px;">Fecha</label>
          <select id="hgDate" class="input" style="width:100%;">
            <option value="">Cargando…</option>
          </select>
        </div>

        <div style="width:320px; min-width:240px;">
          <label class="muted" style="display:block; font-size:12px; margin-bottom:6px;">Tipo</label>
          <select id="hgType" class="input" style="width:100%;">
            <option value="">Seleccione…</option>
            <option value="rbc">RBC proxy (VCM + RDW)</option>
            <option value="plt">PLT proxy (VPM)</option>
            <option value="wbc">WBC diferencial (barras)</option>
          </select>
        </div>
      </div>

      <div class="row" style="justify-content:space-between; align-items:center; margin-top:10px;">
        <label style="display:flex; gap:8px; align-items:center; user-select:none;">
          <input type="checkbox" id="hgAdvancedToggle" />
          <span class="muted">Modo avanzado (timeline)</span>
        </label>
        <div class="muted" style="font-size:12px;">
          ←/→ para navegar (solo en avanzado)
        </div>
      </div>

      <div id="hgAdvanced" class="panel" style="display:none; margin-top:10px; padding:10px;">
        <div class="row" style="gap:10px; align-items:center; margin-bottom:8px;">
          <button id="hgPrev" class="btn" title="Anterior">⏮️</button>
          <button id="hgPlay" class="btn" title="Reproducir/Pausa">▶️</button>
          <button id="hgNext" class="btn" title="Siguiente">⏭️</button>

          <div style="flex:1; min-width:220px;">
            <input id="hgTimeline" type="range" min="0" max="0" value="0" step="1" style="width:100%;" />
            <div class="muted" id="hgTimelineLabel" style="font-size:12px; margin-top:4px;"></div>
          </div>
        </div>

        <!-- NUEVO: compare toggle (solo afecta RBC/PLT) -->
        <label class="muted" style="display:flex; gap:8px; align-items:center; user-select:none; font-size:12px;">
          <input type="checkbox" id="hgComparePrev" />
          Comparar con día anterior (RBC/PLT)
        </label>
      </div>

      <div id="hgChart" class="panel"
        style="height:360px; margin-top:14px; display:flex; align-items:center; justify-content:center;">
        <div class="muted">(Gráfico se renderizará en el siguiente hito)</div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // ---- estado mínimo
  let dates = []; // cronológico (antiguo -> nuevo) para timeline
  const proxy = createProxyClient({ debug: HG_DEBUG });

  hgLog("openHistogramsModal", { sessionId: state.sessionId });
  hgLog("window.echarts?", typeof window.echarts);

  // ---- eCharts init
  const chartHost = modal.querySelector("#hgChart");
  let hgChart = null;

  const showMsg = (msg) => {
    if (!hgChart) return;
    hgChart.setOption(
      {
        title: { text: msg, left: "center", top: "middle" },
        xAxis: { show: false },
        yAxis: { show: false },
        series: [],
      },
      { notMerge: true }
    );
  };

  if (!chartHost) {
    console.warn("[histograms] No existe #hgChart en el modal");
  } else if (!window.echarts) {
    chartHost.innerHTML = `<div class="muted" style="padding:12px;">ECharts no está disponible (no cargado).</div>`;
  } else {
    chartHost.innerHTML = "";
    hgChart = window.echarts.init(chartHost);

    requestAnimationFrame(() => {
      try {
        hgChart && hgChart.resize();
      } catch {}
    });

    // dummy inicial
    hgChart.setOption(
      {
        title: { text: "Histograma (dummy)", left: "center" },
        grid: { left: 50, right: 18, top: 50, bottom: 42 },
        xAxis: { type: "value", name: "X (dummy)" },
        yAxis: { type: "value", name: "Y (dummy)" },
        series: [
          {
            type: "line",
            smooth: true,
            showSymbol: false,
            data: [
              [0, 0],
              [10, 0.2],
              [20, 0.6],
              [30, 1.0],
              [40, 0.6],
              [50, 0.2],
              [60, 0],
            ],
          },
        ],
      },
      { notMerge: true }
    );
  }

  const getPrevDate = (date) => {
    const idx = dates.indexOf(date);
    if (idx > 0) return dates[idx - 1];
    return null;
  };

  // ---- render principal (reutilizable por básico y avanzado)
  const renderCurrent = async () => {
    if (!hgChart) return;

    const selDate = modal.querySelector("#hgDate");
    const selType = modal.querySelector("#hgType");
    const cmp = modal.querySelector("#hgComparePrev");

    const date = selDate ? selDate.value : "";
    const type = selType ? selType.value : "";
    const compareOn = !!cmp?.checked;

    hgLog("renderCurrent()", { date, type, compareOn });

    if (!date) return showMsg("Seleccione una fecha.");
    if (!type) return showMsg("Seleccione un tipo de histograma.");

    try {
      // Compare solo para XY (RBC/PLT) y si hay fecha anterior disponible
      const canCompare = compareOn && (type === "rbc" || type === "plt");
      const prevDate = canCompare ? getPrevDate(date) : null;

      if (canCompare && prevDate) {
        const [todayRes, prevRes] = await Promise.all([
          proxy.getProxy({ date, type }),
          proxy.getProxy({ date: prevDate, type }),
        ]);
        renderXYCurveCompare(hgChart, todayRes, prevRes);
      } else {
        const res = await proxy.getProxy({ date, type });
        if (type === "wbc") renderWbcBars(hgChart, res);
        else renderXYCurve(hgChart, res);
      }

      requestAnimationFrame(() => {
        try {
          hgChart && hgChart.resize();
        } catch {}
      });
    } catch (e) {
      console.error("[histograms] Error cargando proxy", e);
      showMsg("No se pudo cargar el histograma (revise consola y que haya datos para esa fecha).");
    }
  };

  // ---- advanced timeline helper
  const timelineCtl = setupAdvancedTimeline({
    modal,
    getDates: () => dates,
    getSelectedDate: () => modal.querySelector("#hgDate")?.value || "",
    setSelectedDate: (d) => {
      const selDate = modal.querySelector("#hgDate");
      if (selDate) selDate.value = d;
    },
    onNavigate: renderCurrent,
    onStop: () => {}, // placeholder
  });

  // ---- listeners básicos
  modal.querySelector("#hgDate")?.addEventListener("change", async () => {
    timelineCtl.stopPlay();
    await renderCurrent();
    timelineCtl.syncFromSelectedDate();
  });

  modal.querySelector("#hgType")?.addEventListener("change", async () => {
    timelineCtl.stopPlay();
    await renderCurrent();
  });

  // ---- NUEVO: compare toggle (solo render; cero riesgo)
  modal.querySelector("#hgComparePrev")?.addEventListener("change", async () => {
    timelineCtl.stopPlay();
    await renderCurrent();
  });

  // ---- cierre robusto + limpieza
  const close = () => {
    try {
      timelineCtl.destroy();
      if (hgChart) {
        hgChart.dispose();
        hgChart = null;
      }
    } catch {}
    modal.remove();
  };

  modal.addEventListener("click", (ev) => {
    const card = modal.querySelector(".modal-card");
    if (card && !card.contains(ev.target)) close();
  });

  document.addEventListener(
    "keydown",
    (ev) => {
      if (ev.key === "Escape") close();
    },
    { once: true }
  );

  modal.querySelector("#hgClose")?.addEventListener("click", close);

  // ---- cargar fechas
  const selDate = modal.querySelector("#hgDate");

  try {
    const res = await apiJson("GET", `/histograms/dates?session_id=${encodeURIComponent(state.sessionId || "")}`);

    if (!res.dates || res.dates.length === 0) {
      selDate.innerHTML = `<option value="">(sin datos)</option>`;
      selDate.disabled = true;
      return;
    }

    // Cronológico para “película” (antiguo -> nuevo)
    dates = res.dates.slice().reverse();

    // Select se mantiene como antes (más nuevo primero)
    selDate.innerHTML = `<option value="">Seleccione…</option>`;
    for (const d of res.dates) {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = d;
      selDate.appendChild(opt);
    }

    hgLog("dates loaded", res.dates);

    timelineCtl.initTimelineBounds();
    await renderCurrent();
  } catch (e) {
    console.error("[histograms] Error cargando fechas", e);
    selDate.innerHTML = `<option value="">Error cargando fechas</option>`;
    selDate.disabled = true;
  }
}
