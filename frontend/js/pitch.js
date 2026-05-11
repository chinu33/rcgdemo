window.Pitch = (function () {
  const TOTAL = 8;
  let currentSlide = 1;
  let keyHandler = null;
  let presenting = false;
  let cursorTimer = null;

  function init() {
    document.getElementById("pitch-prev")?.addEventListener("click", prev);
    document.getElementById("pitch-next")?.addEventListener("click", next);
    document.querySelectorAll(".pitch-dot").forEach(dot => {
      dot.addEventListener("click", () => goTo(parseInt(dot.dataset.go)));
    });

    document.getElementById("arch-demo-btn")?.addEventListener("click", fireMcpDemo);
    document.getElementById("handoff-store")?.addEventListener("click", () => handoff("store-manager", true));
    document.getElementById("handoff-war")?.addEventListener("click", () => handoff("war-room", false));

    document.getElementById("pitch-present")?.addEventListener("click", enterPresent);
    document.getElementById("fs-prev")?.addEventListener("click", prev);
    document.getElementById("fs-next")?.addEventListener("click", next);
    document.getElementById("fs-exit")?.addEventListener("click", exitPresent);

    document.addEventListener("fullscreenchange", onFullscreenChange);
  }

  // ── Presentation mode ──────────────────────────────────────────────────────

  function enterPresent() {
    presenting = true;
    document.body.classList.add("presenting");
    updateFsArrows();
    const el = document.documentElement;
    if (el.requestFullscreen) el.requestFullscreen().catch(() => {});
    bindCursorActivity();
  }

  function exitPresent() {
    window.Annotate?.disable();
    presenting = false;
    document.body.classList.remove("presenting");
    clearCursorActivity();
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  }

  function onFullscreenChange() {
    // Browser Escape key exited fullscreen — sync our state
    if (!document.fullscreenElement && presenting) {
      window.Annotate?.disable();
      presenting = false;
      document.body.classList.remove("presenting");
      clearCursorActivity();
    }
  }

  function bindCursorActivity() {
    const stage = document.querySelector(".pitch-stage");
    stage?.addEventListener("mousemove", onCursorMove);
    stage?.addEventListener("click", onCursorMove);
    onCursorMove(); // show controls immediately on enter
  }

  function clearCursorActivity() {
    const stage = document.querySelector(".pitch-stage");
    stage?.removeEventListener("mousemove", onCursorMove);
    stage?.removeEventListener("click", onCursorMove);
    stage?.classList.remove("fs-controls-visible");
    clearTimeout(cursorTimer);
  }

  function onCursorMove() {
    const stage = document.querySelector(".pitch-stage");
    if (!stage) return;
    stage.classList.add("fs-controls-visible");
    clearTimeout(cursorTimer);
    cursorTimer = setTimeout(() => stage.classList.remove("fs-controls-visible"), 2500);
  }

  function updateFsArrows() {
    const p = document.getElementById("fs-prev");
    const n = document.getElementById("fs-next");
    if (p) p.disabled = currentSlide === 1;
    if (n) n.disabled = currentSlide === TOTAL;
  }

  // ── Key handling ───────────────────────────────────────────────────────────

  function activate() {
    goTo(1, /*resetCounters*/ true);
    if (!keyHandler) {
      keyHandler = handleKey;
      document.addEventListener("keydown", keyHandler);
    }
  }

  function deactivate() {
    if (presenting) exitPresent();
    if (keyHandler) {
      document.removeEventListener("keydown", keyHandler);
      keyHandler = null;
    }
  }

  function handleKey(e) {
    if (e.target.matches("input, textarea, select, [contenteditable]")) return;
    if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
      e.preventDefault(); next();
    } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
      e.preventDefault(); prev();
    } else if (e.key === "Home") {
      e.preventDefault(); goTo(1);
    } else if (e.key === "End") {
      e.preventDefault(); goTo(TOTAL);
    } else if (e.key === "f" || e.key === "F") {
      if (!presenting) enterPresent(); else exitPresent();
    } else if (e.key === "Escape") {
      e.preventDefault();
      if (window.Annotate?.isActive()) { window.Annotate.disable(); return; } // first Escape exits draw mode
      if (presenting) { exitPresent(); return; }
      if (window.App) App.switchTab("dashboard");
    }
  }

  function goTo(n, resetCounters = false) {
    n = Math.max(1, Math.min(TOTAL, n));
    if (n !== currentSlide) window.Annotate?.clear();
    currentSlide = n;
    document.querySelectorAll(".pslide").forEach(slide => {
      const num = parseInt(slide.dataset.slide);
      slide.classList.toggle("active", num === n);
      // For exit-direction styling
      slide.classList.toggle("exit-left", num < n);
    });
    document.querySelectorAll(".pitch-dot").forEach(dot => {
      dot.classList.toggle("active", parseInt(dot.dataset.go) === n);
    });
    document.getElementById("pitch-counter").textContent = n;
    document.getElementById("pitch-prev").disabled = n === 1;
    document.getElementById("pitch-next").disabled = n === TOTAL;
    updateFsArrows();
    runSlideEntry(n, resetCounters);
  }

  function next() { goTo(currentSlide + 1); }
  function prev() { goTo(currentSlide - 1); }

  function runSlideEntry(n, resetCounters) {
    // Slide indices match the numbering in index.html.
    if (n === 4) animateCounter(resetCounters);       // Problem
    if (n === 6) animateWorkflowSteps(resetCounters); // Workflow
  }

  // ─── Slide 2 — animated counter ──────────────────────────────────────────
  function animateCounter(reset) {
    const el = document.querySelector("[data-count-to]");
    if (!el) return;
    if (reset) el.dataset.done = "";
    if (el.dataset.done === "1") return;
    const to = parseInt(el.dataset.countTo);
    const duration = 1400;
    const start = performance.now();
    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.floor(eased * to);
      if (t < 1) requestAnimationFrame(tick);
      else { el.textContent = to; el.dataset.done = "1"; }
    }
    requestAnimationFrame(tick);
  }

  // ─── Slide 4 — light up workflow steps in sequence ──────────────────────
  function animateWorkflowSteps(reset) {
    const steps = document.querySelectorAll(".wf-step");
    if (reset) steps.forEach(s => s.classList.remove("lit"));
    steps.forEach((s, i) => {
      setTimeout(() => s.classList.add("lit"), 200 + i * 180);
    });
  }

  // ─── Slide 5 — fire a real MCP tool call ────────────────────────────────
  async function fireMcpDemo() {
    const btn = document.getElementById("arch-demo-btn");
    const box = document.getElementById("arch-result");
    if (!btn || !box) return;

    btn.disabled = true;
    btn.textContent = "Calling MCP server…";
    box.hidden = false;
    box.innerHTML = '<div style="color: var(--text-muted)">Sending request to /api/mcp/tools…</div>';

    try {
      const start = performance.now();
      const data = await API.get("/api/mcp/tools");
      const ms = Math.round(performance.now() - start);
      const sample = data.tools.slice(0, 5).map(t => ({ name: t.name, category: t.category }));
      box.innerHTML = `
        <div class="arch-result-head">
          <span class="ok">OK</span>
          <span>${data.tool_count} tools registered · ${data.name} v${data.version}</span>
          <span class="ms" style="margin-left:auto">${ms}ms</span>
        </div>
        <pre>${JSON.stringify(sample, null, 2)}</pre>
        <div style="margin-top:8px; color: var(--text-muted); font-size:10.5px;">↑ Same call your specialist agents make on every run.</div>
      `;
    } catch (e) {
      box.innerHTML = `<div style="color: var(--accent-bad)">Failed: ${e.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "▶ Fire another MCP call";
    }
  }

  // ─── Slide 6 — handoff to live demo ─────────────────────────────────────
  function handoff(tabName, autoRun) {
    if (!window.App) return;
    App.switchTab(tabName);
    if (!autoRun) return;
    setTimeout(() => {
      if (tabName === "store-manager") {
        const input = document.getElementById("sm-input");
        const submit = document.getElementById("sm-submit");
        if (input && submit) {
          input.value = "Give me my morning briefing.";
          submit.click();
        }
      }
    }, 600);
  }

  return { init, activate, deactivate, goTo };
})();
