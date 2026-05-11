(function () {
  const pill = document.getElementById("telemetry-pill");
  const status = document.getElementById("pill-status");
  const lat = document.getElementById("pill-latency");
  const tok = document.getElementById("pill-tokens");
  const cost = document.getElementById("pill-cost");
  const agents = document.getElementById("pill-agents");
  const overlay = document.getElementById("ai-overlay");
  const overlayText = document.getElementById("ai-overlay-text");
  const overlaySub = document.getElementById("ai-overlay-sub");

  let runStart = 0;
  let raf = null;
  let totalIn = 0, totalOut = 0, totalCost = 0;
  let specialistCount = null; // set when run_complete arrives

  function show() {
    pill.hidden = false;
  }
  function tickLatency() {
    const ms = Date.now() - runStart;
    lat.textContent = ms.toLocaleString();
    raf = requestAnimationFrame(tickLatency);
  }
  function stopLatency() { if (raf) cancelAnimationFrame(raf); raf = null; }

  function updateMetrics() {
    tok.textContent = (totalIn + totalOut).toLocaleString();
    cost.textContent = totalCost.toFixed(4);
    if (specialistCount !== null) {
      agents.textContent = `Orchestrator + ${specialistCount} + Synthesizer`;
    }
  }

  window.Telemetry = {
    startRun(label = "Coordinating agents…", sub = "Routing your request to the network") {
      totalIn = 0; totalOut = 0; totalCost = 0; specialistCount = null;
      runStart = Date.now();
      status.textContent = "Live";
      lat.textContent = "0";
      tok.textContent = "0";
      cost.textContent = "0.0000";
      agents.textContent = "–";
      show();
      tickLatency();
      // Brief overlay flash for "wow"
      overlayText.textContent = label;
      overlaySub.textContent = sub;
      overlay.hidden = false;
      setTimeout(() => { if (overlay) overlay.hidden = true; }, 1100);
    },
    onAgentStart(label) {
      status.textContent = label;
      // Pop micro-overlay text
      overlayText.textContent = label;
      overlaySub.textContent = "Specialist working…";
    },
    onAgentComplete(ev) {
      totalIn += ev.input_tokens || 0;
      totalOut += ev.output_tokens || 0;
      totalCost += ev.cost_usd || 0;
      updateMetrics();
    },
    setAgentSummary(n) {
      specialistCount = n;
      updateMetrics();
    },
    setAgentLabel(text) {
      agents.textContent = text;
    },
    finishRun() {
      status.textContent = "Complete";
      stopLatency();
      // Keep pill visible — user can see final totals.
    },
    error(msg) {
      status.textContent = "Error";
      stopLatency();
      overlayText.textContent = "Run failed";
      overlaySub.textContent = msg || "See console.";
    },
  };
})();
