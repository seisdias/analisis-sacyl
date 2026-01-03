// web/assets/ui/modals/histograms/advanced_timeline.js

export function setupAdvancedTimeline({
  modal,
  getDates,          // () => dates[]
  getSelectedDate,   // () => string
  setSelectedDate,   // (date: string) => void (sin render)
  onNavigate,        // async () => render (llamado tras setSelectedDate)
  onStop,            // () => stop any play
}) {
  const advToggle = modal.querySelector("#hgAdvancedToggle");
  const advPanel = modal.querySelector("#hgAdvanced");
  const timeline = modal.querySelector("#hgTimeline");
  const tlLabel = modal.querySelector("#hgTimelineLabel");
  const btnPrev = modal.querySelector("#hgPrev");
  const btnNext = modal.querySelector("#hgNext");
  const btnPlay = modal.querySelector("#hgPlay");

  let playTimer = null;

  const stopPlay = () => {
    if (playTimer) {
      clearInterval(playTimer);
      playTimer = null;
    }
    if (btnPlay) btnPlay.textContent = "▶️";
    onStop && onStop();
  };

  const updateLabelByIndex = (idx) => {
    const dates = getDates() || [];
    if (!tlLabel) return;
    tlLabel.textContent = dates[idx] || "";
  };

  const clampIndex = (idx) => {
    const dates = getDates() || [];
    if (!dates.length) return 0;
    return Math.max(0, Math.min(idx, dates.length - 1));
  };

  const findIndex = (date) => {
    const dates = getDates() || [];
    const idx = dates.indexOf(date);
    return idx >= 0 ? idx : 0;
  };

  const setIndex = async (idx) => {
    const dates = getDates() || [];
    if (!dates.length) return;
    idx = clampIndex(idx);

    if (timeline) timeline.value = String(idx);
    updateLabelByIndex(idx);

    setSelectedDate(dates[idx]);
    await onNavigate();
  };

  const onKey = (ev) => {
    if (!advToggle?.checked) return;
    const dates = getDates() || [];
    if (!dates.length) return;

    if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      stopPlay();
      setIndex(Number(timeline?.value || "0") - 1);
    } else if (ev.key === "ArrowRight") {
      ev.preventDefault();
      stopPlay();
      setIndex(Number(timeline?.value || "0") + 1);
    }
  };

  advToggle?.addEventListener("change", () => {
    const on = !!advToggle.checked;
    if (advPanel) advPanel.style.display = on ? "block" : "none";
    stopPlay();

    if (on) {
      const dates = getDates() || [];
      if (!dates.length) return;

      const current = getSelectedDate() || dates[0];
      const idx = findIndex(current);

      if (timeline) {
        timeline.min = "0";
        timeline.max = String(Math.max(0, dates.length - 1));
        timeline.value = String(idx);
      }
      updateLabelByIndex(idx);
    }
  });

  timeline?.addEventListener("input", async () => {
    stopPlay();
    await setIndex(Number(timeline.value));
  });

  btnPrev?.addEventListener("click", async () => {
    stopPlay();
    await setIndex(Number(timeline?.value || "0") - 1);
  });

  btnNext?.addEventListener("click", async () => {
    stopPlay();
    await setIndex(Number(timeline?.value || "0") + 1);
  });

  btnPlay?.addEventListener("click", () => {
    const dates = getDates() || [];
    if (!dates.length) return;

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
      setIndex(next);
    }, 700);
  });

  document.addEventListener("keydown", onKey);

  return {
    stopPlay,
    syncFromSelectedDate: () => {
      const dates = getDates() || [];
      if (!dates.length) return;

      const current = getSelectedDate() || dates[0];
      const idx = findIndex(current);

      if (timeline) timeline.value = String(idx);
      updateLabelByIndex(idx);
    },
    initTimelineBounds: () => {
      const dates = getDates() || [];
      if (!timeline) return;
      timeline.min = "0";
      timeline.max = String(Math.max(0, dates.length - 1));
      timeline.value = "0";
      updateLabelByIndex(0);
    },
    destroy: () => {
      stopPlay();
      document.removeEventListener("keydown", onKey);
    },
  };
}
