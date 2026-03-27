// web/assets/ui/modals/export_analytics_modal.js
import { apiJson } from "./modal_utils.js";

export async function openExportAnalyticsModal({ sessionId } = {}){
  let modal = document.getElementById("exportAnalyticsModal");

  if(!modal){
    modal = document.createElement("div");
    modal.id = "exportAnalyticsModal";
    modal.className = "modal hidden";
    modal.innerHTML = `
      <div class="modal-backdrop" id="eaBackdrop"></div>
      <div class="modal-card panel export-analytics-modal-card">
        <div class="row" style="justify-content:space-between; align-items:center;">
          <b>Exportar analítica</b>
          <button id="eaClose">Cerrar</button>
        </div>

        <div class="row" style="margin-top:10px;">
          <div class="grow">
            <div class="muted">Fecha de analítica</div>
            <select id="eaDateSelect"></select>
          </div>
        </div>

        <div class="row">
          <div class="grow">
            <div class="muted">Plantilla</div>
            <textarea id="eaTemplate" class="ea-textarea" spellcheck="false"></textarea>
          </div>
        </div>

        <div class="row">
          <div class="grow">
            <div class="muted">
              Tokens disponibles:
              <span id="eaTokens"></span>
            </div>
          </div>
        </div>

        <div class="row">
          <button id="eaResetTemplate" class="ghost">Reset plantilla</button>
          <button id="eaSaveTemplate" class="ghost">Guardar plantilla</button>
          <button id="eaGenerate">Generar</button>
          <button id="eaCopy" class="ghost">Copiar</button>
        </div>

        <div class="row" style="margin-top:12px;">
          <div class="grow">
            <div class="muted">Resultado</div>
            <textarea id="eaResult" class="ea-textarea" readonly></textarea>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    const hide = () => {
      modal.classList.add("hidden");
      modal.setAttribute("aria-hidden", "true");
      modal.style.display = "none";
    };

    modal.addEventListener("click", (ev) => {
      if (ev.target.closest("#eaClose")) return hide();
      if (ev.target.closest("#eaBackdrop")) return hide();
    });

    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && !modal.classList.contains("hidden")) hide();
    });

    modal._hide = hide;
  }

  const show = () => {
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    modal.style.removeProperty("display");
  };

  const qs = (sel) => modal.querySelector(sel);

  const dateSelect = qs("#eaDateSelect");
  const templateEl = qs("#eaTemplate");
  const tokensEl = qs("#eaTokens");
  const resultEl = qs("#eaResult");
  const btnGenerate = qs("#eaGenerate");
  const btnCopy = qs("#eaCopy");
  const btnSaveTemplate = qs("#eaSaveTemplate");
  const btnResetTemplate = qs("#eaResetTemplate");

  const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";

  const datesResp = await apiJson("GET", `/export_analytics/dates${suffix}`);
  const tplResp = await apiJson("GET", `/export_analytics/template${suffix}`);

  const dates = datesResp.dates || [];
  const selected = datesResp.selected || "";
  const defaultTemplate = tplResp.default_template || "";
  const allowedTokens = tplResp.allowed_tokens || [];

  if(dates.length === 0){
    throw new Error("No hay analíticas de hematología disponibles");
  }

  dateSelect.innerHTML = "";
  for(const d of dates){
    const opt = document.createElement("option");
    opt.value = d;
    opt.textContent = d;
    if(d === selected){
      opt.selected = true;
    }
    dateSelect.appendChild(opt);
  }

  templateEl.value = tplResp.template || defaultTemplate;
  tokensEl.textContent = allowedTokens.join("  ");
  resultEl.value = "";

  btnResetTemplate.onclick = () => {
    templateEl.value = defaultTemplate;
  };

  btnSaveTemplate.onclick = async () => {
    await apiJson("PUT", `/export_analytics/template${suffix}`, {
      template: templateEl.value,
    });
  };

  btnGenerate.onclick = async () => {
    const fecha = dateSelect.value;
    const template = templateEl.value;

    await apiJson("PUT", `/export_analytics/template${suffix}`, {
      template,
    });

    const resp = await apiJson("POST", `/export_analytics/generate${suffix}`, {
      fecha,
    });

    resultEl.value = resp.text || "";
  };

  btnCopy.onclick = async () => {
    const txt = resultEl.value || "";
    if(!txt){
      return;
    }
    await navigator.clipboard.writeText(txt);
  };

  show();
}