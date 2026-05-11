window.MCP = (function () {
  let loaded = false;
  let toolIndex = {};
  let monitorCallCount = 0;
  let hideTimer = null;
  const AUTO_HIDE_AFTER_RUN_MS = 6000;
  const MAX_MONITOR_ITEMS = 12;

  // Session-level rollup stats
  const stats = {
    totalCalls: 0,
    totalLatency: 0,
    errors: 0,
    perTool: {},  // {toolName: {calls, totalLatency, errors, lastCalledAt}}
  };

  const CATEGORY_TINT = {
    sales: "#34d399",
    inventory: "#7c5cff",
    labor: "#22d3ee",
    merchandising: "#ec4899",
    cx: "#f59e0b",
    reference: "#94a3b8",
    supply_chain: "#fb923c",
    risk: "#ef4444",
    analytics: "#a78bfa",
    overview: "#22d3ee",
  };

  async function load() {
    if (loaded) return;
    const data = await API.get("/api/mcp/tools");
    document.getElementById("mcp-server-name").textContent = data.name;
    document.getElementById("mcp-server-version").textContent = "v" + data.version;
    document.getElementById("mcp-tool-count").textContent = data.tool_count;
    const archCount = document.getElementById("arch-tool-count");
    if (archCount) archCount.textContent = data.tool_count;
    const cats = new Set(data.tools.map(t => t.category));
    document.getElementById("mcp-cat-count").textContent = `${cats.size} categories`;

    const list = document.getElementById("mcp-tools-list");
    list.innerHTML = data.tools.map(t => {
      toolIndex[t.name] = t;
      const tint = CATEGORY_TINT[t.category] || "#7c5cff";
      const props = (t.input_schema && t.input_schema.properties) || {};
      const params = Object.keys(props).map(k => `<code>${k}</code>`).join(", ") || "<em>no args</em>";
      return `
        <div class="mcp-tool" data-tool="${t.name}" style="--tint:${tint}">
          <div class="mcp-tool-head">
            <span class="mcp-tool-name">${t.name}</span>
            <span class="mcp-tool-cat">${t.category}</span>
          </div>
          <div class="mcp-tool-desc">${t.description}</div>
          <div class="mcp-tool-args">params: ${params}</div>
          <div class="mcp-tool-stats">
            <div class="mcp-tool-stat zero" data-stat="calls"><span class="lbl">Calls</span><span class="val">0</span></div>
            <div class="mcp-tool-stat zero" data-stat="avg"><span class="lbl">Avg</span><span class="val">—</span></div>
            <div class="mcp-tool-stat zero" data-stat="last"><span class="lbl">Last</span><span class="val">never</span></div>
          </div>
        </div>`;
    }).join("");
    loaded = true;
  }

  function _fmtAgo(ts) {
    if (!ts) return "never";
    const s = Math.floor((Date.now() - ts) / 1000);
    if (s < 5) return "just now";
    if (s < 60) return s + "s ago";
    const m = Math.floor(s / 60);
    if (m < 60) return m + "m ago";
    return Math.floor(m / 60) + "h ago";
  }

  function _updateBannerStats() {
    document.getElementById("mcp-call-count").textContent = stats.totalCalls;
    const avgEl = document.getElementById("mcp-avg-latency");
    avgEl.textContent = stats.totalCalls
      ? Math.round(stats.totalLatency / stats.totalCalls) + "ms"
      : "—";
    const successEl = document.getElementById("mcp-success-rate");
    successEl.textContent = stats.totalCalls
      ? Math.round(((stats.totalCalls - stats.errors) / stats.totalCalls) * 100) + "%"
      : "—";
  }

  function _updateToolCardStats(toolName) {
    const card = document.querySelector(`.mcp-tool[data-tool="${toolName}"]`);
    if (!card) return;
    const t = stats.perTool[toolName];
    if (!t) return;
    const callsEl = card.querySelector('[data-stat="calls"] .val');
    const callsWrap = card.querySelector('[data-stat="calls"]');
    const avgEl = card.querySelector('[data-stat="avg"] .val');
    const avgWrap = card.querySelector('[data-stat="avg"]');
    const lastEl = card.querySelector('[data-stat="last"] .val');
    const lastWrap = card.querySelector('[data-stat="last"]');
    if (callsEl) { callsEl.textContent = t.calls; callsWrap.classList.remove("zero"); }
    if (avgEl) { avgEl.textContent = Math.round(t.totalLatency / t.calls) + "ms"; avgWrap.classList.remove("zero"); }
    if (lastEl) { lastEl.textContent = _fmtAgo(t.lastCalledAt); lastWrap.classList.remove("zero"); }
    card.classList.add("recently-used");
    setTimeout(() => card.classList.remove("recently-used"), 1700);
  }

  // Refresh "Last" timestamps periodically so they say "12s ago" → "1m ago"
  setInterval(() => {
    Object.keys(stats.perTool).forEach(name => {
      const card = document.querySelector(`.mcp-tool[data-tool="${name}"]`);
      if (!card) return;
      const lastEl = card.querySelector('[data-stat="last"] .val');
      if (lastEl) lastEl.textContent = _fmtAgo(stats.perTool[name].lastCalledAt);
    });
  }, 5000);

  function recordCall(ev) {
    // Update aggregate stats
    stats.totalCalls += 1;
    stats.totalLatency += ev.latency_ms || 0;
    if (!ev.ok) stats.errors += 1;
    const t = stats.perTool[ev.tool] = stats.perTool[ev.tool] || {
      calls: 0, totalLatency: 0, errors: 0, lastCalledAt: null,
    };
    t.calls += 1;
    t.totalLatency += ev.latency_ms || 0;
    if (!ev.ok) t.errors += 1;
    t.lastCalledAt = Date.now();

    _updateBannerStats();
    _updateToolCardStats(ev.tool);

    document.getElementById("mcp-feed-status").textContent = "Live";
    addToHistory(ev);
    addToMonitor(ev);
  }

  function addToHistory(ev) {
    const feed = document.getElementById("mcp-feed");
    const empty = feed.querySelector(".mcp-feed-empty");
    if (empty) empty.remove();

    const tool = toolIndex[ev.tool] || {};
    const tint = CATEGORY_TINT[tool.category] || "#7c5cff";
    const time = new Date();
    const ts = `${fmt.pad2(time.getHours())}:${fmt.pad2(time.getMinutes())}:${fmt.pad2(time.getSeconds())}`;
    const argsStr = Object.keys(ev.arguments || {}).length
      ? JSON.stringify(ev.arguments)
      : "{}";

    const row = document.createElement("div");
    row.className = "mcp-call" + (ev.ok ? "" : " error");
    row.style.setProperty("--tint", tint);
    row.innerHTML = `
      <div class="mcp-call-head">
        <span class="mcp-call-time">${ts}</span>
        <span class="mcp-call-status">${ev.ok ? "OK" : "ERR"}</span>
        <span class="mcp-call-tool">${ev.tool}</span>
        <span class="mcp-call-caller">← ${ev.caller || "—"}</span>
        <span class="mcp-call-latency">${ev.latency_ms}ms</span>
      </div>
      <div class="mcp-call-args">${argsStr}</div>
      ${ev.result_preview ? `<div class="mcp-call-preview">${ev.result_preview}</div>` : ""}
      ${ev.error ? `<div class="mcp-call-error">${ev.error}</div>` : ""}
    `;
    feed.prepend(row);
    while (feed.children.length > 60) feed.removeChild(feed.lastChild);
  }

  // ─── Live Monitor (floating drawer) ─────────────────────────────────────────

  function addToMonitor(ev) {
    const monitor = document.getElementById("mcp-monitor");
    const body = document.getElementById("mcp-monitor-body");
    if (!monitor || !body) return;
    monitor.hidden = false;
    monitor.classList.remove("fading");

    const empty = body.querySelector(".mcp-monitor-empty");
    if (empty) empty.remove();

    monitorCallCount += 1;
    const counter = document.getElementById("mcp-monitor-count");
    if (counter) counter.textContent = monitorCallCount;

    const tool = toolIndex[ev.tool] || {};
    const tint = CATEGORY_TINT[tool.category] || "#f59e0b";
    const args = (ev.arguments && Object.keys(ev.arguments).length)
      ? JSON.stringify(ev.arguments)
      : "{}";

    const row = document.createElement("div");
    row.className = "mcp-mini-call" + (ev.ok ? "" : " error");
    row.style.setProperty("--tint", tint);
    row.innerHTML = `
      <div class="mcp-mini-call-head">
        <span class="mcp-mini-call-status">${ev.ok ? "OK" : "ERR"}</span>
        <span class="mcp-mini-call-tool">${ev.tool}</span>
        <span class="mcp-mini-call-caller">← ${ev.caller || "—"}</span>
        <span class="mcp-mini-call-latency">${ev.latency_ms}ms</span>
      </div>
      <div class="mcp-mini-call-args">${args}</div>
    `;
    body.prepend(row);
    while (body.children.length > MAX_MONITOR_ITEMS) body.removeChild(body.lastChild);
  }

  function openMonitor() {
    const monitor = document.getElementById("mcp-monitor");
    if (!monitor) return;
    if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    monitor.hidden = false;
    monitor.classList.remove("fading");
    monitorCallCount = 0;
    const counter = document.getElementById("mcp-monitor-count");
    if (counter) counter.textContent = "0";
    const body = document.getElementById("mcp-monitor-body");
    if (body) body.innerHTML = '<div class="mcp-monitor-empty">Waiting for tool calls…</div>';
  }

  function scheduleMonitorClose() {
    if (hideTimer) clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      const monitor = document.getElementById("mcp-monitor");
      if (!monitor) return;
      monitor.classList.add("fading");
      setTimeout(() => {
        monitor.hidden = true;
        monitor.classList.remove("fading");
      }, 480);
    }, AUTO_HIDE_AFTER_RUN_MS);
  }

  function closeMonitor() {
    if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    const monitor = document.getElementById("mcp-monitor");
    if (!monitor) return;
    monitor.classList.add("fading");
    setTimeout(() => {
      monitor.hidden = true;
      monitor.classList.remove("fading");
    }, 480);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const closeBtn = document.getElementById("mcp-monitor-close");
    const expandBtn = document.getElementById("mcp-monitor-expand");
    if (closeBtn) closeBtn.addEventListener("click", closeMonitor);
    if (expandBtn) expandBtn.addEventListener("click", () => {
      if (window.App) App.switchTab("mcp");
    });
  });

  return { load, recordCall, openMonitor, scheduleMonitorClose, closeMonitor };
})();
