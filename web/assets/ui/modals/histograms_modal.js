// web/assets/ui/modals/histograms_modal.js
import { state } from "../../state.js";
import { apiJson } from "./modal_utils.js";

export async function openHistogramsModal(){
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
        <button id="hgClose">Cerrar</button>
      </div>

      <div class="row" style="margin-top:12px; gap:12px; align-items:end;">
        <label>
          <div class="muted">Fecha</div>
          <select id="hgDate" style="min-width:180px;"></select>
        </label>

        <label>
          <div class="muted">Tipo</div>
          <select id="hgType" style="min-width:260px;">
            <option value="rbc">Distribución eritrocitaria (proxy)</option>
            <option value="plt">Distribución plaquetaria (proxy)</option>
            <option value="wbc">Diferencial leucocitario</option>
          </select>
        </label>

        <span class="muted" style="margin-left:auto;">
          ⚠ Proxy · No diagnóstico
        </span>
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

    // ---- eCharts: init seguro (cero riesgo)
  const chartHost = modal.querySelector("#hgChart");
  let hgChart = null;

  if (!chartHost) {
    console.warn("[histograms] No existe #hgChart en el modal");
  } else if (!window.echarts) {
    chartHost.innerHTML = `<div class="muted" style="padding:12px;">ECharts no está disponible (no cargado).</div>`;
  } else {
    // borrar placeholder
    chartHost.innerHTML = "";
    hgChart = window.echarts.init(chartHost);

    // render dummy mínimo
    hgChart.setOption({
      title: { text: "Histograma (dummy)", left: "center" },
      grid: { left: 50, right: 18, top: 50, bottom: 42 },
      xAxis: { type: "value", name: "X (dummy)" },
      yAxis: { type: "value", name: "Y (dummy)" },
      series: [{
        type: "line",
        smooth: true,
        showSymbol: false,
        data: [[0,0],[10,0.2],[20,0.6],[30,1.0],[40,0.6],[50,0.2],[60,0]],
      }]
    }, { notMerge: true });

        function rerenderDummy() {
          const selDate = modal.querySelector("#hgDate");
          const selType = modal.querySelector("#hgType");
          const type = selType ? selType.value : "rbc";

          const title =
            type === "plt" ? "Distribución plaquetaria (dummy)"
            : type === "wbc" ? "Diferencial leucocitario (dummy)"
            : "Distribución eritrocitaria (dummy)";

          hgChart.setOption(
            {
              title: { text: title, left: "center", top: 6 },
            },
            { notMerge: false }
          );
        }

        modal.querySelector("#hgDate")?.addEventListener("change", rerenderDummy);
        modal.querySelector("#hgType")?.addEventListener("change", rerenderDummy);
  }


  // ---- cierre robusto (patrón existente)
  const close = () => {
    try {
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

  document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") close();
    },
    { once: true }
  );

modal.querySelector("#hgClose")?.addEventListener("click", close);


  // ---- cargar fechas desde backend
  const selDate = modal.querySelector("#hgDate");

  try {
    const res = await apiJson(
      "GET",
      `/histograms/dates?session_id=${encodeURIComponent(state.sessionId || "")}`
    );

    if (!res.dates || res.dates.length === 0) {
      selDate.innerHTML = `<option value="">(sin datos)</option>`;
      selDate.disabled = true;
      return;
    }

    for (const d of res.dates) {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = d;
      selDate.appendChild(opt);
    }
  } catch (e) {
    selDate.innerHTML = `<option value="">Error cargando fechas</option>`;
    selDate.disabled = true;
  }
}


