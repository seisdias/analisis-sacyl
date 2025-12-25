// web/assets/shell.js

// -----------------------------
// UI helpers
// -----------------------------
function setPill(ok, el, text) {
  el.textContent = text;
  el.style.borderColor = ok ? "#bbf7d0" : "#fecaca";
  el.style.color = ok ? "#166534" : "#991b1b";
  el.style.background = ok ? "#f0fdf4" : "#fef2f2";
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  }[c]));
}

function apiBase() {
  // FastAPI sirve /web desde el mismo origen
  return window.location.origin;
}

function fileNameFromPath(p) {
  const parts = String(p).split(/[\\/]/);
  return parts[parts.length - 1] || "Paciente";
}

// -----------------------------
// HTTP helpers
// -----------------------------
async function requestJson(method, path, body, { signal } = {}) {
  const opts = { method, signal, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(`${apiBase()}${path}`, opts);

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      detail = j.detail || j.error || JSON.stringify(j);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  // Algunas respuestas podrían no tener JSON (por ahora todas sí)
  return await res.json();
}

const postJson = (path, body, opts) => requestJson("POST", path, body, opts);
const getJson  = (path, opts) => requestJson("GET", path, undefined, opts);
const delJson  = (path, opts) => requestJson("DELETE", path, undefined, opts);

async function postFormData(path, formData, { signal } = {}) {
  const res = await fetch(`${apiBase()}${path}`, {
    method: "POST",
    body: formData,
    signal,
  });

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      detail = j.detail || j.error || JSON.stringify(j);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return await res.json();
}


// -----------------------------
// Tabs state
// -----------------------------
const tabsBar = document.getElementById("tabsBar");
const tabsContent = document.getElementById("tabsContent");
const shellStatus = document.getElementById("shellStatus");

let tabs = []; // { id, title, sessionId, iframeUrl }
let activeId = null;

// Para evitar carreras si se hace doble click rápido en abrir/crear
let openAbort = null;

function render() {
  // Tabs
  tabsBar.innerHTML = "";
  for (const t of tabs) {
    const el = document.createElement("div");
    el.className = "tab" + (t.id === activeId ? " active" : "");
    el.innerHTML = `
      <span class="t">${escapeHtml(t.title)}</span>
      <span class="x" title="Cerrar">×</span>
    `;

    el.addEventListener("click", (ev) => {
      if (ev.target?.classList?.contains("x")) return;
      setActive(t.id);
    });

    el.querySelector(".x").addEventListener("click", async (ev) => {
      ev.stopPropagation();
      await closeTab(t.id);
    });

    tabsBar.appendChild(el);
  }

  // Panes
  tabsContent.innerHTML = "";
  for (const t of tabs) {
    const pane = document.createElement("div");
    pane.className = "tabpane" + (t.id === activeId ? " active" : "");
    pane.dataset.tabId = t.id;

    if (t.iframeUrl) {
      const iframe = document.createElement("iframe");
      iframe.src = t.iframeUrl;
      pane.appendChild(iframe);
    } else {
      const empty = document.createElement("div");
      empty.style.padding = "16px";
      empty.innerHTML = `
        <div class="panel">
          <b>Pestaña vacía</b>
          <div class="muted" style="margin-top:6px;">
            Usa “Archivo · Abrir BD…” o “Archivo · Nueva BD…” para abrir un paciente en una pestaña.
          </div>
        </div>
      `;
      pane.appendChild(empty);
    }

    tabsContent.appendChild(pane);
  }
}

function setActive(id) {
  activeId = id;
  render();
}

function addTab({ title, sessionId = null, iframeUrl = null }) {
  const id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}_${Math.random()}`);
  tabs.push({ id, title, sessionId, iframeUrl });
  activeId = id;
  render();
  return id;
}

function updateTabTitleBySession(sessionId, title) {
  const t = tabs.find(x => x.sessionId === sessionId);
  if (!t) return;
  if (t.title === title) return;
  t.title = title;
  render();
}

async function closeTab(id) {
  const t = tabs.find(x => x.id === id);
  if (!t) return;

  if (t.sessionId) {
    try {
      await delJson(`/sessions/${encodeURIComponent(t.sessionId)}`);
    } catch (e) {
      // No bloqueamos el cierre de pestaña por esto
      setPill(false, shellStatus, `Aviso al cerrar sesión: ${e.message}`);
    }
  }

  const idx = tabs.findIndex(x => x.id === id);
  tabs.splice(idx, 1);

  if (activeId === id) {
    activeId = tabs.length ? tabs[Math.max(0, idx - 1)].id : null;
  }

  render();
  if (!tabs.length) setPill(true, shellStatus, "Listo");
}

// -----------------------------
// Modal (open / new)
// -----------------------------
const modal = document.getElementById("modal");
const dbPathInput = document.getElementById("dbPathInput");
const modalTitle = document.getElementById("modalTitle");
const modalHint = document.getElementById("modalHint");

const btnOpenDb = document.getElementById("btnOpenDb");
const btnCreateDb = document.getElementById("btnCreateDb");
const btnUploadDb = document.getElementById("btnUploadDb");


function updateDesktopUiVisibility(){
  const isDesktop = !!(window.pywebview && window.pywebview.api);
  // Ocultamos "Cargar BD…" en desktop (porque ya podemos abrir por path)
  btnUploadDb.style.display = isDesktop ? "none" : "";
  // Si quieres, también podrías ocultar el input file:
  const fileUploadDb = document.getElementById("fileUploadDb");
  if (fileUploadDb) fileUploadDb.style.display = isDesktop ? "none" : "none"; // sigue hidden
}

updateDesktopUiVisibility();

// pywebview dispara este evento cuando está listo (según versión)
window.addEventListener("pywebviewready", updateDesktopUiVisibility);

// fallback: reintentos cortos por si no hay evento
let tries = 0;
const t = setInterval(() => {
  updateDesktopUiVisibility();
  tries++;
  if ((window.pywebview && window.pywebview.api) || tries >= 20) clearInterval(t);
}, 100);




const fileUploadDb = document.getElementById("fileUploadDb");
const btnNewTab = document.getElementById("btnNewTab");

const btnCancel = document.getElementById("btnCancel");
const btnOk = document.getElementById("btnOpen");
const modalBackdrop = document.getElementById("modalBackdrop");

let modalMode = "open"; // "open" | "new"

function showModal(mode) {
  modalMode = mode;

  if (mode === "new") {
    modalTitle.textContent = "Crear nueva base de datos";
    modalHint.textContent = "Pega la ruta completa del nuevo fichero .db (se creará vacío).";
  } else {
    modalTitle.textContent = "Abrir base de datos";
    modalHint.textContent = "Pega la ruta completa del fichero .db (por ahora).";
  }

  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
  dbPathInput.value = "";
  dbPathInput.focus();
}

function hideModal() {
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
}


btnOpenDb.addEventListener("click", async () => {
  // Desktop: diálogo nativo
  if (hasPywebview() && window.pywebview.api.pick_open_db) {
    try {
      const path = await window.pywebview.api.pick_open_db();
      if (!path) return;

      try { openAbort?.abort(); } catch {}
      openAbort = new AbortController();

      setPill(true, shellStatus, "Abriendo BD…");

      const resp = await postJson("/sessions/open", { db_path: path }, { signal: openAbort.signal });
      const sid = resp.session_id;

      const base = apiBase();
      const url = `${base}/web/dashboard.html?base=${encodeURIComponent(base)}&session_id=${encodeURIComponent(sid)}`;

      addTab({ title: fileNameFromPath(path), sessionId: sid, iframeUrl: url });

      // Mejorar título con el nombre del paciente (si existe)
      try {
        const patient = await getJson(`/patient?session_id=${encodeURIComponent(sid)}`, { signal: openAbort.signal });
        const displayName = patient?.display_name ? String(patient.display_name).trim() : "";
        if (displayName) updateTabTitleBySession(sid, displayName);
      } catch (e) {
        console.warn("No se pudo obtener el nombre del paciente:", e);
      }

      setPill(true, shellStatus, "Conectado");
    } catch (e) {
      if (e.name === "AbortError") return;
      setPill(false, shellStatus, `Error: ${e.message}`);
    }
    return;
  }

  // Navegador fallback: modal
  showModal("open");
});

btnCreateDb.addEventListener("click", async () => {
  // Desktop: diálogo nativo (guardar como)
  if (hasPywebview() && window.pywebview.api.pick_new_db) {
    try {
      const path = await window.pywebview.api.pick_new_db();
      if (!path) return;

      try { openAbort?.abort(); } catch {}
      openAbort = new AbortController();

      setPill(true, shellStatus, "Creando BD…");

      const resp = await postJson("/sessions/new", { db_path: path, overwrite: true }, { signal: openAbort.signal });
      const sid = resp.session_id;

      const base = apiBase();
      const url = `${base}/web/dashboard.html?base=${encodeURIComponent(base)}&session_id=${encodeURIComponent(sid)}`;

      addTab({ title: fileNameFromPath(path), sessionId: sid, iframeUrl: url });

      // Mejorar título con el nombre del paciente (si existe)
      try {
        const patient = await getJson(`/patient?session_id=${encodeURIComponent(sid)}`, { signal: openAbort.signal });
        const displayName = patient?.display_name ? String(patient.display_name).trim() : "";
        if (displayName) updateTabTitleBySession(sid, displayName);
      } catch (e) {
        console.warn("No se pudo obtener el nombre del paciente:", e);
      }

      setPill(true, shellStatus, "Conectado");
    } catch (e) {
      if (e.name === "AbortError") return;
      setPill(false, shellStatus, `Error: ${e.message}`);
    }
    return;
  }

  // Navegador fallback: modal
  showModal("new");
});


// --- Cargar BD (modo navegador, sin teclear ruta) ---
btnUploadDb.addEventListener("click", () => {
  // Abrimos el selector de archivo del navegador
  fileUploadDb.value = "";
  fileUploadDb.click();
});

fileUploadDb.addEventListener("change", async () => {
  const file = fileUploadDb.files && fileUploadDb.files[0];
  if (!file) return;

  // Cancelar intentos previos si existieran
  try { openAbort?.abort(); } catch {}
  openAbort = new AbortController();

  setPill(true, shellStatus, "Subiendo BD…");

  try {
    const fd = new FormData();
    // OJO: el nombre "db_file" debe coincidir con el backend: db_file: UploadFile = File(...)
    fd.append("db_file", file);

    // 1) Subir BD y abrir sesión backend
    const resp = await postFormData("/sessions/upload", fd, { signal: openAbort.signal });
    const sid = resp.session_id;

    // 2) Construir URL del dashboard (exige ?base=)
    const base = apiBase();
    const url = `${base}/web/dashboard.html?base=${encodeURIComponent(base)}&session_id=${encodeURIComponent(sid)}`;

    // 3) Crear pestaña con título provisional (nombre del fichero subido)
    const fallbackTitle = file.name || "Paciente";
    addTab({ title: fallbackTitle, sessionId: sid, iframeUrl: url });

    // 4) Mejorar título con el nombre del paciente (si existe)
    try {
      const patient = await getJson(`/patient?session_id=${encodeURIComponent(sid)}`, { signal: openAbort.signal });
      const displayName = patient?.display_name ? String(patient.display_name).trim() : "";
      if (displayName) updateTabTitleBySession(sid, displayName);
    } catch (e) {
      console.warn("No se pudo obtener el nombre del paciente:", e);
    }

    setPill(true, shellStatus, "Conectado");
  } catch (e) {
    if (e.name === "AbortError") return;
    setPill(false, shellStatus, `Error: ${e.message}`);
  }
});


btnCancel.addEventListener("click", hideModal);
modalBackdrop.addEventListener("click", hideModal);

btnNewTab.addEventListener("click", () => {
  addTab({ title: "Nueva pestaña" });
  setPill(true, shellStatus, "Listo");
});

btnOk.addEventListener("click", async () => {
  const dbPath = (dbPathInput.value || "").trim();
  if (!dbPath) {
    setPill(false, shellStatus, "Ruta vacía");
    return;
  }

  // Cancelar intentos previos si existieran
  try { openAbort?.abort(); } catch {}
  openAbort = new AbortController();

  const endpoint = (modalMode === "new") ? "/sessions/new" : "/sessions/open";
  const verbText = (modalMode === "new") ? "Creando BD…" : "Abriendo BD…";
  setPill(true, shellStatus, verbText);

  try {
    // 1) Crear/Abrir sesión backend
    const resp = await postJson(endpoint, { db_path: dbPath }, { signal: openAbort.signal });
    const sid = resp.session_id;

    // 2) Construir URL del dashboard (exige ?base=)
    const base = apiBase();
    const url = `${base}/web/dashboard.html?base=${encodeURIComponent(base)}&session_id=${encodeURIComponent(sid)}`;

    // 3) Crear pestaña con título provisional (nombre de fichero)
    const fallbackTitle = fileNameFromPath(dbPath);
    addTab({ title: fallbackTitle, sessionId: sid, iframeUrl: url });

    // 4) Mejorar título con el nombre del paciente (si existe)
    try {
      const patient = await getJson(`/patient?session_id=${encodeURIComponent(sid)}`, { signal: openAbort.signal });
      const displayName = patient?.display_name ? String(patient.display_name).trim() : "";
      if (displayName) {
        updateTabTitleBySession(sid, displayName);
      }
    } catch (e) {
      // No bloquea UX: para BD nueva puede no existir paciente todavía
      console.warn("No se pudo obtener el nombre del paciente:", e);
    }

    setPill(true, shellStatus, "Conectado");
    hideModal();
  } catch (e) {
    if (e.name === "AbortError") return;
    setPill(false, shellStatus, `Error: ${e.message}`);
  }
});

// -----------------------------
// Boot
// -----------------------------
function boot() {
  addTab({ title: "Inicio" });
  setPill(true, shellStatus, "Listo");
}

function hasPywebview(){
  return !!(window.pywebview && window.pywebview.api);
}


if (window.pywebview && window.pywebview.api) btnUploadDb.style.display = "none";

boot();
