window.WarRoom = (function () {
  let flow = null;
  let scenarios = [];
  let selectedId = null;
  let ws = null;

  async function init() {
    const c = document.getElementById("wr-flow");
    const log = document.getElementById("wr-log");
    flow = new AgentFlow(c, log, "disruption");

    const data = await API.get("/api/scenarios");
    scenarios = data.scenarios;
    document.getElementById("wr-scn-count").textContent = `${scenarios.length} ready`;
    renderScenarios();

    document.getElementById("wr-run").addEventListener("click", run);
  }

  function renderScenarios() {
    const grid = document.getElementById("wr-scenarios");
    grid.innerHTML = scenarios.map(s => `
      <div class="scenario" data-id="${s.id}">
        <div class="scenario-head">
          <span class="scenario-type">${s.type}</span>
          <span class="scenario-sev ${s.severity}">${s.severity}</span>
        </div>
        <div class="scenario-title">${s.title}</div>
        <div class="scenario-detail">${s.details}</div>
        <div class="scenario-stores">Affected stores: ${s.affected_stores.join(", ")}</div>
      </div>`).join("");

    grid.querySelectorAll(".scenario").forEach(el => {
      el.addEventListener("click", () => {
        grid.querySelectorAll(".scenario").forEach(e => e.classList.remove("selected"));
        el.classList.add("selected");
        selectedId = el.dataset.id;
        document.getElementById("wr-run").disabled = false;
      });
    });
  }

  function run() {
    if (!selectedId) return;
    flow.reset();
    document.getElementById("wr-flow-status").textContent = "Live";
    document.getElementById("wr-brief-status").textContent = "Pending";
    document.getElementById("wr-brief").innerHTML = "";
    document.getElementById("wr-artifacts").hidden = true;
    document.getElementById("wr-comms-card").hidden = true;

    Telemetry.startRun("Activating Disruption War Room…", "Detector parsing event");
    if (window.MCP) MCP.openMonitor();

    if (ws) try { ws.close(); } catch (e) {}
    ws = API.ws("/ws/disruption");
    ws.addEventListener("open", () => ws.send(JSON.stringify({ scenario_id: selectedId })));
    ws.addEventListener("message", ev => handle(JSON.parse(ev.data)));
    ws.addEventListener("error", () => Telemetry.error("WebSocket error"));
  }

  let streamBuffer = "";

  function handle(ev) {
    if (ev.type === "agent_start") {
      flow.setState(ev.agent, "running");
      flow.log("start", `${ev.label} engaged`);
      Telemetry.onAgentStart(ev.label);
      if (ev.agent === "synthesizer") {
        streamBuffer = "";
        document.getElementById("wr-brief-status").textContent = "Streaming";
        document.getElementById("wr-brief").innerHTML = '<span class="cursor"></span>';
      }
    } else if (ev.type === "fanout_start") {
      flow.log("fan", `Parallel: ${ev.agents.join(", ")}`);
    } else if (ev.type === "mcp_tool_call") {
      flow.log(ev.ok ? "mcp" : "err",
        `MCP · ${ev.caller} → ${ev.tool} (${ev.latency_ms}ms)${ev.ok ? "" : " · " + (ev.error || "fail")}`);
      if (window.MCP) MCP.recordCall(ev);
    } else if (ev.type === "token" && ev.agent === "synthesizer") {
      streamBuffer += ev.text;
      // Stream as plain markdown during typing; apply rich layout on completion
      document.getElementById("wr-brief").innerHTML = markdown(streamBuffer) + '<span class="cursor"></span>';
    } else if (ev.type === "agent_complete") {
      const meta = `${ev.latency_ms}ms · ${ev.input_tokens + ev.output_tokens} tok`;
      flow.setState(ev.agent, "complete", meta);
      flow.log("done", `${ev.label} · ${meta} · $${ev.cost_usd.toFixed(5)}`);
      Telemetry.onAgentComplete(ev);

      if (ev.agent === "supplier") {
        document.getElementById("wr-artifacts").hidden = false;
        document.getElementById("wr-supplier").innerHTML =
          '<span class="synth-lbl artifact-lbl">Supplier Risk Assessment</span>' + markdown(ev.output.brief);
      } else if (ev.agent === "rebalancer") {
        document.getElementById("wr-artifacts").hidden = false;
        document.getElementById("wr-rebalance").innerHTML =
          '<span class="synth-lbl artifact-lbl">Inventory Rebalancing Plan</span>' + markdown(ev.output.brief);
      } else if (ev.agent === "impact") {
        document.getElementById("wr-artifacts").hidden = false;
        document.getElementById("wr-impact").innerHTML =
          '<span class="synth-lbl artifact-lbl">Store Impact Analysis</span>' + markdown(ev.output.brief);
      } else if (ev.agent === "comms") {
        renderComms(ev.output.brief);
      } else if (ev.agent === "synthesizer" && ev.output?.brief) {
        document.getElementById("wr-brief").innerHTML = renderWarRoomBrief(ev.output.brief);
      }
    } else if (ev.type === "run_complete") {
      document.getElementById("wr-flow-status").textContent = "Complete";
      document.getElementById("wr-brief-status").textContent = "Ready";
      Telemetry.setAgentLabel("Detector + 3 + Comms + Synthesizer");
      Telemetry.finishRun();
      if (window.MCP) MCP.scheduleMonitorClose();
    } else if (ev.type === "error") {
      Telemetry.error(ev.message);
      if (window.MCP) MCP.scheduleMonitorClose();
    }
  }

  function renderWarRoomBrief(raw) {
    // Parse raw markdown by section label — same pattern as renderSynthesis in store-manager.js
    const sections = { headline: "", decisionsMd: "", autoMd: "" };
    let current = null;

    raw.split("\n").forEach(line => {
      const t = line.trim();
      if (t.startsWith("## ")) {
        sections.headline = t.slice(3).trim();
      } else if (/^\*{1,2}Decisions Needed/i.test(t)) {
        current = "decisions";
      } else if (/^\*{1,2}Auto-?Actions/i.test(t)) {
        current = "auto";
      } else if (current === "decisions") {
        sections.decisionsMd += line + "\n";
      } else if (current === "auto") {
        sections.autoMd += line + "\n";
      }
    });

    let html = "";

    if (sections.headline) {
      html += `<div class="synth-headline"><h2>${sections.headline}</h2></div>`;
    }
    if (sections.decisionsMd.trim()) {
      html += `<div class="synth-actions-wrap">
        <span class="synth-lbl synth-lbl-decisions">Decisions Needed — Next 60 Minutes</span>
        <div class="synth-actions synth-decisions">${markdown(sections.decisionsMd.trim())}</div>
      </div>`;
    }
    if (sections.autoMd.trim()) {
      html += `<div class="synth-actions-wrap" style="margin-top:14px">
        <span class="synth-lbl synth-lbl-auto">Auto-Actions Taken</span>
        <div class="synth-auto-actions">${markdown(sections.autoMd.trim())}</div>
      </div>`;
    }

    return html || markdown(raw);
  }

  function renderComms(text) {
    document.getElementById("wr-comms-card").hidden = false;
    const blocks = text.split(/===\s*([A-Z_]+)\s*===/).slice(1);
    const html = [];
    for (let i = 0; i < blocks.length; i += 2) {
      const tag = blocks[i].replace("_", " ");
      const body = (blocks[i + 1] || "").trim();
      html.push(`
        <div class="comm-block">
          <div class="comm-label">${tag}</div>
          <div class="comm-text">${body}</div>
        </div>`);
    }
    if (!html.length) {
      html.push(`<div class="comm-block"><div class="comm-text">${text}</div></div>`);
    }
    document.getElementById("wr-comms").innerHTML = html.join("");
  }

  return { init };
})();
