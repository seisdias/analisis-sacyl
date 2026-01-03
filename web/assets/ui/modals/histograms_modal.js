// web/assets/ui/modals/histograms_modal.js
import { state } from "../../state.js";
import { apiJson } from "./modal_utils.js";

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

      <!-- Toggle modo avanzado (apagado por defecto) -->
      <div class="row" style="justify-content:space-between; align-items:center; margin-top:10px;">
        <label style="display:flex; gap:8px; align-items:center; user-select:none;">
          <input type="checkbox" id="hgAdvancedToggle" />
          <span class="muted">Modo avanzado (timeline)</span>
        </label>
        <div class="muted" style="font-size:12px;">
          ←/→ para navegar (solo en avanzado)
        </div>
      </div>

      <!-- Panel avanzado: oculto por defecto -->
      <div id="hgAdvanced" class="panel" style="display:none; margin-top:10px; padding:10px;">
        <div class="row" style="gap:10px; align-items:center;">
          <button id="hgPrev" class="btn" title="Anterior">⏮️</button>
          <button id="hgPlay" class="btn" title="Reproducir/Pausa">▶️</button>
          <button id="hgNext" class="btn" title="Siguiente">⏭️</button>

          <div style="flex:1; min-width:220px;">
            <input id="hgTimeline" type="range" min="0" max="0" value="0" step="1" style="width:100%;" />
            <div class="muted" id="hgTimelineLabel" style="font-size:12px; margin-top:4px;"></div>
          </div>
        </div>
      </div>

      <div
        id="hgChart"
        class="panel"
        style="height:360px; margin-top:14px; display:flex; align-items:center; justify-content:center;">
        <div class="muted">
          (Gráfico se renderizará en el siguiente hito)
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // rerenderProxy se define en este scope para poder llamarla tras cargar fechas
  let rerenderProxy = null;

  // ---- estado para modo avanzado (cero riesgo: si no se activa, no impacta)
  let dates = [];
  let playTimer = null;
  const proxyCache = new Map(); // key: `${type}|${date}` -> payload

  const advToggle = modal.querySelector("#hgAdvancedToggle");
  const advPanel = modal.querySelector("#hgAdvanced");
  const timeline = modal.querySelector("#hgTimeline");
  const tlLabel = modal.querySelector("#hgTimelineLabel");
  const btnPrev = modal.querySelector("#hgPrev");
  const btnNext = modal.querySelector("#hgNext");
  const btnPlay = modal.querySelector("#hgPlay");

  const stopPlay = () => {
    if (playTimer) {
      clearInterval(playTimer);
      playTimer = null;
    }
    if (btnPlay) btnPlay.textContent = "▶️";
  };

  const updateTimelineLabel = (idx) => {
    if (!tlLabel) return;
    if (!dates.length) {
      tlLabel.textContent = "";
      return;
    }
    const d = dates[idx] || "";
    tlLabel.textContent = d;
  };

  const findDateIndex = (d) => {
    if (!dates.length) return 0;
    const idx = dates.indexOf(d);
    return idx >= 0 ? idx : 0;
  };

  const clampIndex = (idx) => {
    if (!dates.length) return 0;
    return Math.max(0, Math.min(idx, dates.length - 1));
  };

  const setTimelineIndex = async (idx) => {
    if (!dates.length) return;
    idx = clampIndex(idx);

    if (timeline) timeline.value = String(idx);
    updateTimelineLabel(idx);

    // sincroniza con el modo básico
    const selDate = modal.querySelector("#hgDate");
    if (selDate) selDate.value = dates[idx];

    if (typeof rerenderProxy === "function") {
      await rerenderProxy();
    }
  };

  const onKey = (ev) => {
    // solo navegamos si el modo avanzado está activo (opt-in)
    if (!advToggle?.checked) return;
    if (!dates.length) return;

    if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      stopPlay();
      const idx = Number(timeline?.value || "0") - 1;
      setTimelineIndex(idx);
    } else if (ev.key === "ArrowRight") {
      ev.preventDefault();
      stopPlay();
      const idx = Number(timeline?.value || "0") + 1;
      setTimelineIndex(idx);
    }
  };

  // ---- eCharts: init seguro (cero riesgo)
  const chartHost = modal.querySelector("#hgChart");
  let hgChart = null;

  hgLog("openHistogramsModal", { sessionId: state.sessionId });
  hgLog("window.echarts?", typeof window.echarts);

  if (!chartHost) {
    console.warn("[histograms] No existe #hgChart en el modal");
  } else if (!window.echarts) {
    chartHost.innerHTML = `<div class="muted" style="padding:12px;">ECharts no está disponible (no cargado).</div>`;
  } else {
    // borrar placeholder (antes de init)
    chartHost.innerHTML = "";
    hgChart = window.echarts.init(chartHost);

    // Asegurar layout estable tras insert en DOM
    requestAnimationFrame(() => {
      try {
        hgChart && hgChart.resize();
      } catch (e) {}
    });
    hgLog("ECharts init OK");

    // render dummy mínimo (para validar que eCharts pinta)
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

    rerenderProxy = async function rerenderProxy() {
      if (!hgChart) return;

      const selDate = modal.querySelector("#hgDate");
      const selType = modal.querySelector("#hgType");
      const date = selDate ? selDate.value : "";
      const type = selType ? selType.value : "";

      hgLog("rerenderProxy()", { date, type });

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

      // Guardas UI
      if (!date) {
        showMsg("Seleccione una fecha.");
        return;
      }
      if (!type) {
        showMsg("Seleccione un tipo de histograma.");
        return;
      }

      // ---- cache (cero riesgo): si existe, evita fetch repetido
      const cacheKey = `${type}|${date}`;
      let res = proxyCache.get(cacheKey);

      try {
        if (!res) {
          const url =
            `/histograms/proxy?date=${encodeURIComponent(date)}&type=${encodeURIComponent(type)}` +
            `&session_id=${encodeURIComponent(state.sessionId || "")}`;

          hgLog("fetch", url);
          res = await apiJson("GET", url);
          hgLog("apiJson response", res);

          // Compat: si apiJson envuelve en {data: ...}
          if (
            res &&
            typeof res === "object" &&
            res.data &&
            (res.x || res.y || res.categories || res.pct || res.abs) == null
          ) {
            res = res.data;
            hgLog("unwrapped res.data", res);
          }

          proxyCache.set(cacheKey, res);
        } else {
          hgLog("cache hit", cacheKey);
        }

        if (type === "wbc") {
          renderWbcBars(hgChart, res);
        } else {
          renderXYCurve(hgChart, res);
        }

        // Por si el modal cambió de tamaño / fonts
        requestAnimationFrame(() => {
          try {
            hgChart && hgChart.resize();
          } catch (e) {}
        });
      } catch (e) {
        console.error("[histograms] Error cargando proxy", e);
        showMsg("No se pudo cargar el histograma (revise consola y que haya datos para esa fecha).");
      }
    };

    function renderXYCurve(chart, res) {
      const x = res.x || [];
      const y = res.y || [];
      const labelX = res.labels && res.labels.x ? res.labels.x : "X";
      const labelY = res.labels && res.labels.y ? res.labels.y : "Y";

      const data = [];
      for (let i = 0; i < Math.min(x.length, y.length); i++) {
        data.push([x[i], y[i]]);
      }

      // markers: vcm / vpm / etc.
      const markLines = [];
      if (res.markers && typeof res.markers === "object") {
        for (const [k, v] of Object.entries(res.markers)) {
          if (v == null || Number.isNaN(Number(v))) continue;
          markLines.push({
            xAxis: Number(v),
            name: k,
            label: { formatter: k },
          });
        }
      }

      // bandas (ej. RDW proxy) -> markArea xAxis
      const markAreas = [];
      if (Array.isArray(res.bands)) {
        for (const b of res.bands) {
          if (!b) continue;
          const from = Number(b.from);
          const to = Number(b.to);
          if (Number.isFinite(from) && Number.isFinite(to)) {
            markAreas.push([
              { xAxis: from, name: b.label || "" },
              { xAxis: to },
            ]);
          }
        }
      }

      chart.setOption(
        {
          title: { text: `${(res.title || "Histograma")} · ${res.date || ""}`.trim(), left: "center", top: 6 },
          grid: { left: 60, right: 18, top: 52, bottom: 46 },
          tooltip: { trigger: "axis", confine: true },
          xAxis: { type: "value", name: labelX, nameLocation: "middle", nameGap: 28 },
          yAxis: { type: "value", name: labelY, nameLocation: "middle", nameGap: 40 },
          series: [
            {
              type: "line",
              smooth: true,
              showSymbol: false,
              lineStyle: { width: 3 },
              areaStyle: { opacity: 0.1 },
              data,
              markLine: markLines.length ? { data: markLines } : undefined,
              markArea: markAreas.length ? { data: markAreas } : undefined,
            },
          ],
        },
        { notMerge: true }
      );
    }

    function renderWbcBars(chart, res) {
      const cats = res.categories || [];
      const pct = res.pct || [];
      const abs = res.abs || [];

      chart.setOption(
        {
          title: { text: `WBC diferencial · ${res.date || ""}`.trim(), left: "center", top: 6 },
          grid: { left: 60, right: 18, top: 52, bottom: 46 },
          tooltip: {
            trigger: "axis",
            confine: true,
            axisPointer: { type: "shadow" },
            formatter: (params) => {
              const p = params && params[0];
              if (!p) return "";
              const idx = p.dataIndex;
              const a = abs[idx];
              const aTxt = a == null ? "" : `<br/>Abs: <b>${a}</b>`;
              return `${cats[idx]}<br/>%: <b>${(pct[idx] ?? 0).toFixed(1)}</b>${aTxt}`;
            },
          },
          xAxis: { type: "category", data: cats },
          yAxis: { type: "value", name: "Porcentaje (%)", nameLocation: "middle", nameGap: 40, max: 100 },
          series: [
            {
              type: "bar",
              data: pct,
            },
          ],
        },
        { notMerge: true }
      );
    }

    // listeners básicos
    modal.querySelector("#hgDate")?.addEventListener("change", async () => {
      stopPlay(); // si el usuario toca manualmente, paramos “película”
      await rerenderProxy?.();
      // si avanzado activo, re-sincroniza timeline al valor seleccionado
      if (advToggle?.checked && dates.length) {
        const idx = findDateIndex(modal.querySelector("#hgDate")?.value || "");
        if (timeline) timeline.value = String(idx);
        updateTimelineLabel(idx);
      }
    });

    modal.querySelector("#hgType")?.addEventListener("change", async () => {
      stopPlay();
      await rerenderProxy?.();
      // el tipo cambia: el cache sigue funcionando por type|date (ok)
    });

    // listeners modo avanzado (solo UI; no rompe básico)
    advToggle?.addEventListener("change", async () => {
      const on = !!advToggle.checked;
      if (advPanel) advPanel.style.display = on ? "block" : "none";
      stopPlay();

      if (on && dates.length) {
        const current = modal.querySelector("#hgDate")?.value || dates[0];
        const idx = findDateIndex(current);
        if (timeline) {
          timeline.min = "0";
          timeline.max = String(Math.max(0, dates.length - 1));
          timeline.value = String(idx);
        }
        updateTimelineLabel(idx);
      }
    });

    timeline?.addEventListener("input", async () => {
      stopPlay();
      await setTimelineIndex(Number(timeline.value));
    });

    btnPrev?.addEventListener("click", async () => {
      stopPlay();
      await setTimelineIndex(Number(timeline?.value || "0") - 1);
    });

    btnNext?.addEventListener("click", async () => {
      stopPlay();
      await setTimelineIndex(Number(timeline?.value || "0") + 1);
    });

    btnPlay?.addEventListener("click", async () => {
      if (!dates.length) return;

      // toggle play/pause
      if (playTimer) {
        stopPlay();
        return;
      }
      btnPlay.textContent = "⏸️";

      playTimer = setInterval(() => {
        const idx = Number(timeline?.value || "0");
        const next = idx + 1;

        if (next >= dates.length) {
          stopPlay();
          return;
        }
        // no await dentro de interval: sencillo y suficiente
        setTimelineIndex(next);
      }, 700);
    });

    // teclado para navegación (solo en avanzado)
    document.addEventListener("keydown", onKey);

    // Asegurar resize al mostrar/ocultar panel avanzado
    advToggle?.addEventListener("change", () => {
      requestAnimationFrame(() => {
        try {
          hgChart && hgChart.resize();
        } catch (e) {}
      });
    });
  }

  // ---- cierre robusto (patrón existente) + limpieza avanzada
  const close = () => {
    try {
      stopPlay();
      document.removeEventListener("keydown", onKey);

      if (hgChart) {
        hgChart.dispose();
        hgChart = null;
      }
    } catch (e) {
      // no rompemos el cierre por un dispose
    }
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

  // ---- cargar fechas desde backend
  const selDate = modal.querySelector("#hgDate");

  try {
    const res = await apiJson("GET", `/histograms/dates?session_id=${encodeURIComponent(state.sessionId || "")}`);

    if (!res.dates || res.dates.length === 0) {
      selDate.innerHTML = `<option value="">(sin datos)</option>`;
      selDate.disabled = true;
      return;
    }

    dates = res.dates.slice().reverse(); // copia defensiva

    // reset select
    selDate.innerHTML = `<option value="">Seleccione…</option>`;

    for (const d of res.dates) {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = d;
      selDate.appendChild(opt);
    }

    hgLog("dates loaded", res.dates);

    // inicializa timeline (aunque esté oculto)
    if (timeline) {
      timeline.min = "0";
      timeline.max = String(Math.max(0, dates.length - 1));
      timeline.value = "0";
    }
    updateTimelineLabel(0);

    if (typeof rerenderProxy === "function") {
      await rerenderProxy();
    }
  } catch (e) {
    console.error("[histograms] Error cargando fechas", e);
    selDate.innerHTML = `<option value="">Error cargando fechas</option>`;
    selDate.disabled = true;
  }
}
