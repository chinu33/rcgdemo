window.StoreManager = (function () {
  let flow = null;
  let ws = null;
  const SUGGESTIONS = [
    "Why are dairy sales down today?",
    "Give me my morning briefing.",
    "What's the impact of the competitor promo?",
    "Are we covered for tonight's shift?",
    "Which categories are at risk?",
  ];

  function init() {
    const c = document.getElementById("sm-flow");
    const log = document.getElementById("sm-log");
    flow = new AgentFlow(c, log, "store_manager");

    const sug = document.getElementById("sm-suggestions");
    sug.innerHTML = SUGGESTIONS.map(s => `<button class="suggestion-chip">${s}</button>`).join("");
    sug.querySelectorAll(".suggestion-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        document.getElementById("sm-input").value = btn.textContent;
      });
    });

    document.getElementById("sm-submit").addEventListener("click", run);
    document.getElementById("sm-input").addEventListener("keydown", e => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") run();
    });

    document.getElementById("btn-run-briefing").addEventListener("click", () => {
      App.switchTab("store-manager");
      document.getElementById("sm-input").value = "Give me my morning briefing.";
      run();
    });
  }

  function run() {
    const q = document.getElementById("sm-input").value.trim() || "Give me my morning briefing.";
    flow.reset();
    document.getElementById("sm-flow-status").textContent = "Live";
    const empty = document.getElementById("sm-empty");
    if (empty) empty.hidden = true;
    document.getElementById("sm-answer-card").hidden = true;
    document.getElementById("sm-briefs-card").hidden = true;
    document.getElementById("sm-briefs").innerHTML = "";

    Telemetry.startRun("Coordinating Store Manager network…", "Routing to specialists");
    if (window.MCP) MCP.openMonitor();

    if (ws) try { ws.close(); } catch (e) {}
    ws = API.ws("/ws/store-manager");
    ws.addEventListener("open", () => ws.send(JSON.stringify({ question: q })));
    ws.addEventListener("message", ev => handle(JSON.parse(ev.data)));
    ws.addEventListener("error", () => Telemetry.error("WebSocket error"));
  }

  let streamBuffer = "";

  function handle(ev) {
    if (ev.type === "agent_start") {
      flow.setState(ev.agent, "running");
      flow.log("start", `${ev.label} started`);
      Telemetry.onAgentStart(ev.label);
      if (ev.agent === "synthesizer") {
        streamBuffer = "";
        document.getElementById("sm-answer-card").hidden = false;
        document.getElementById("sm-answer").innerHTML = '<span class="cursor"></span>';
      }
    } else if (ev.type === "fanout_start") {
      flow.log("fan", `Fan-out → ${ev.agents.join(", ")}`);
    } else if (ev.type === "mcp_tool_call") {
      flow.log(ev.ok ? "mcp" : "err",
        `MCP · ${ev.caller} → ${ev.tool} (${ev.latency_ms}ms)${ev.ok ? "" : " · " + (ev.error || "fail")}`);
      if (window.MCP) MCP.recordCall(ev);
    } else if (ev.type === "token" && ev.agent === "synthesizer") {
      streamBuffer += ev.text;
      document.getElementById("sm-answer").innerHTML = markdown(streamBuffer) + '<span class="cursor"></span>';
    } else if (ev.type === "agent_complete") {
      const meta = `${ev.latency_ms}ms · ${ev.input_tokens + ev.output_tokens} tok`;
      flow.setState(ev.agent, "complete", meta);
      flow.log("done", `${ev.label} · ${meta} · $${ev.cost_usd.toFixed(5)}`);
      Telemetry.onAgentComplete(ev);
      if (ev.agent !== "orchestrator" && ev.agent !== "synthesizer" && ev.output?.brief) {
        renderBrief(ev.agent, ev.label, ev.output.brief, ev);
      }
      if (ev.agent === "synthesizer" && ev.output?.answer) {
        document.getElementById("sm-answer").innerHTML = renderSynthesis(ev.output.answer);
      }
    } else if (ev.type === "run_complete") {
      document.getElementById("sm-flow-status").textContent = "Complete";
      if (ev.selected_agents) Telemetry.setAgentSummary(ev.selected_agents.length);
      Telemetry.finishRun();
      if (window.MCP) MCP.scheduleMonitorClose();
    } else if (ev.type === "error") {
      Telemetry.error(ev.message);
      if (window.MCP) MCP.scheduleMonitorClose();
    }
  }

  function renderSynthesis(raw) {
    // Parse raw markdown by section label — do NOT rely on rendered HTML structure
    // because the LLM may omit blank lines between sections, collapsing them into one <p>.
    const sections = { headline: "", rootCause: "", actionsMd: "" };
    let current = null;

    raw.split("\n").forEach(line => {
      const t = line.trim();
      if (t.startsWith("## ")) {
        sections.headline = t.slice(3).trim();
      } else if (/^\*{1,2}Root Cause\*{1,2}/i.test(t)) {
        current = "root";
      } else if (/^\*{1,2}Recommended Actions?\*{1,2}/i.test(t)) {
        current = "actions";
      } else if (current === "root" && t) {
        // Strip any lingering ** markers the LLM added inline
        sections.rootCause += (sections.rootCause ? " " : "") + t.replace(/\*\*/g, "");
      } else if (current === "actions") {
        sections.actionsMd += line + "\n";
      }
    });

    let html = "";

    if (sections.headline) {
      html += `<div class="synth-headline"><h2>${sections.headline}</h2></div>`;
    }
    if (sections.rootCause) {
      html += `<div class="synth-root-cause">
        <span class="synth-lbl">Root Cause</span>
        <p>${sections.rootCause}</p>
      </div>`;
    }
    if (sections.actionsMd.trim()) {
      html += `<div class="synth-actions-wrap">
        <span class="synth-lbl synth-lbl-actions">Recommended Actions</span>
        <div class="synth-actions">${markdown(sections.actionsMd.trim())}</div>
      </div>`;
    }

    return html || markdown(raw);
  }

  function renderBrief(agent, label, text, ev) {
    document.getElementById("sm-briefs-card").hidden = false;
    const icons  = { sales: "📈", inventory: "📦", labor: "👥", promo: "🎯", reviews: "💬" };
    const colors = { sales: "#7c5cff", inventory: "#22d3ee", labor: "#f59e0b", promo: "#f472b6", reviews: "#34d399" };
    const lbls   = { sales: "Revenue & Category Performance", inventory: "Stock Levels & Supply Risk", labor: "Staffing & Coverage", promo: "Promotions & Competitive Intel", reviews: "Customer Sentiment" };
    const div = document.createElement("div");
    div.className = "brief-item";
    div.dataset.agent = agent;
    div.innerHTML = `
      <div class="brief-head">
        <span class="brief-icon">${icons[agent] || "•"}</span>
        <span class="brief-name">${label}</span>
        <span class="brief-meta">${ev.latency_ms}ms · ${ev.input_tokens + ev.output_tokens} tok · $${ev.cost_usd.toFixed(5)}</span>
      </div>
      <div class="brief-body markdown">
        <span class="synth-lbl" style="color:${colors[agent] || "var(--accent-1)"}; margin-bottom:10px; display:block">${lbls[agent] || label}</span>
        ${markdown(text)}
      </div>`;
    document.getElementById("sm-briefs").appendChild(div);
  }

  return { init };
})();
