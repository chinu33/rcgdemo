(function () {
  // Network visualization. Renders nodes positioned on a grid + animated edges.
  // Layouts:
  //   store_manager: router → [5 specialists in parallel] → synthesizer
  //   disruption: detector → [supplier, rebalancer, impact] → comms → synthesizer

  const ICONS = {
    orchestrator: "🧭",
    sales: "📈",
    inventory: "📦",
    labor: "👥",
    promo: "🎯",
    reviews: "💬",
    synthesizer: "✨",
    detector: "📡",
    supplier: "🚚",
    rebalancer: "🔁",
    impact: "🏬",
    comms: "📨",
  };

  const LAYOUTS = {
    store_manager: {
      nodes: {
        router:       { x: 50,  y: 50, label: "Router" },
        sales:        { x: 50,  y: 18, label: "Sales" },
        inventory:    { x: 50,  y: 82, label: "Inventory" },
        labor:        { x: 18,  y: 30, label: "Labor" },
        promo:        { x: 82,  y: 30, label: "Promo" },
        reviews:      { x: 50,  y: 50, label: "Reviews" },
        synthesizer:  { x: 50,  y: 50, label: "Synthesizer" },
      },
      // Grid layout for SM is too crammed — use a 7-column linear arrangement
    },
  };

  // A simpler programmatic layout for either workflow:
  // Layout uses absolute pixel spacing so nodes never overlap, regardless of
  // how tall the agent-flow container ends up being.
  const NODE_H = 44;     // visible node height (allows 2-line labels)
  const ROW_PITCH = 64;  // distance between vertical neighbors

  function distributeY(count, h) {
    const total = (count - 1) * ROW_PITCH;
    const top = Math.max(NODE_H / 2 + 6, (h - total) / 2);
    return Array.from({ length: count }, (_, i) => top + i * ROW_PITCH);
  }

  // Half of node width + padding from edge (extra room for glow/scale animation)
  const EDGE_PAD = 100;

  function computeLayout(workflow, w, h) {
    if (workflow === "store_manager") {
      const xs = {
        orchestrator: Math.max(EDGE_PAD, 0.08 * w),
        specialists: w / 2,
        synth: Math.min(w - EDGE_PAD, 0.92 * w),
      };
      const specialists = ["sales", "inventory", "labor", "promo", "reviews"];
      const ys = distributeY(specialists.length, h);
      const layout = {
        orchestrator: { x: xs.orchestrator, y: h / 2 },
        synthesizer: { x: xs.synth, y: h / 2 },
      };
      specialists.forEach((s, i) => {
        layout[s] = { x: xs.specialists, y: ys[i] };
      });
      const edges = [];
      specialists.forEach(s => {
        edges.push(["orchestrator", s]);
        edges.push([s, "synthesizer"]);
      });
      return { layout, edges, nodes: ["orchestrator", ...specialists, "synthesizer"] };
    }
    // Disruption: 4 columns evenly distributed across available width
    const ys3 = distributeY(3, h);
    const dPad = 84; // edge padding for disruption (4-column layout needs less margin)
    const dPitch = (w - 2 * dPad) / 3;
    const layout = {
      detector:    { x: dPad,              y: h / 2 },
      supplier:    { x: dPad + dPitch,     y: ys3[0] },
      rebalancer:  { x: dPad + dPitch,     y: ys3[1] },
      impact:      { x: dPad + dPitch,     y: ys3[2] },
      comms:       { x: dPad + dPitch * 2, y: h / 2 },
      synthesizer: { x: w - dPad,          y: h / 2 },
    };
    const edges = [
      ["detector", "supplier"],
      ["detector", "rebalancer"],
      ["detector", "impact"],
      ["supplier", "comms"],
      ["rebalancer", "comms"],
      ["impact", "comms"],
      ["comms", "synthesizer"],
    ];
    return { layout, edges, nodes: Object.keys(layout) };
  }

  class AgentFlow {
    constructor(container, logEl, workflow) {
      this.container = container;
      this.logEl = logEl;
      this.workflow = workflow;
      this.nodes = {};
      this.edges = [];
      this.svg = null;
      this.render();
      window.addEventListener("resize", () => this.render(true));
      // Container may be 0×0 when its panel is hidden — observe size changes
      // and re-render once it becomes visible.
      if (typeof ResizeObserver !== "undefined") {
        this._ro = new ResizeObserver(() => this.render(true));
        this._ro.observe(container);
      }
    }

    render(reposition = false) {
      const w = this.container.clientWidth;
      const h = this.container.clientHeight;
      if (!w || !h) return;
      // If we haven't built the DOM yet, this must be a full render even if
      // the caller asked for reposition-only.
      if (!this.svg) reposition = false;
      const { layout, edges, nodes } = computeLayout(this.workflow, w, h);
      this.layoutMap = layout;

      if (!reposition) {
        this.container.innerHTML = "";
        // SVG for edges
        const svgNS = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("class", "flow-svg");
        svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
        svg.setAttribute("preserveAspectRatio", "none");
        edges.forEach(([from, to]) => {
          const line = document.createElementNS(svgNS, "path");
          line.setAttribute("class", "flow-edge");
          line.dataset.from = from;
          line.dataset.to = to;
          this.edges.push({ from, to, el: line });
          svg.appendChild(line);
        });
        this.svg = svg;
        this.container.appendChild(svg);

        nodes.forEach(name => {
          const el = document.createElement("div");
          el.className = "agent-node";
          el.dataset.agent = name;
          el.dataset.state = "idle";
          el.innerHTML = `
            <div class="node-icon">${ICONS[name] || "•"}</div>
            <div class="node-text">
              <div class="node-label">${this.labelFor(name)}</div>
              <div class="node-meta" data-meta></div>
            </div>
          `;
          this.nodes[name] = el;
          this.container.appendChild(el);
        });
      }

      // Position nodes + edges
      Object.entries(layout).forEach(([name, p]) => {
        const el = this.nodes[name];
        if (!el) return;
        el.style.left = `${p.x}px`;
        el.style.top = `${p.y}px`;
      });
      this.edges.forEach(({ from, to, el }) => {
        const a = layout[from], b = layout[to];
        if (!a || !b) return;
        const dx = (b.x - a.x);
        const cx1 = a.x + dx * 0.5, cy1 = a.y;
        const cx2 = a.x + dx * 0.5, cy2 = b.y;
        el.setAttribute("d", `M ${a.x} ${a.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${b.x} ${b.y}`);
      });
    }

    labelFor(name) {
      return ({
        orchestrator: "Orchestrator",
        sales: "Sales",
        inventory: "Inventory",
        labor: "Labor",
        promo: "Promo",
        reviews: "Reviews",
        synthesizer: "Synthesizer",
        detector: "Detector",
        supplier: "Supplier Researcher",
        rebalancer: "Store Inventory Analyst",
        impact: "Store Impact Analyst",
        comms: "Comms",
      })[name] || name;
    }

    setState(agent, state, meta = "") {
      const el = this.nodes[agent];
      if (!el) return;
      el.dataset.state = state;
      const m = el.querySelector("[data-meta]");
      if (m) m.textContent = meta;
      // Activate edges
      this.edges.forEach(({ from, to, el: line }) => {
        const fromState = this.nodes[from]?.dataset.state;
        const toState = this.nodes[to]?.dataset.state;
        if (fromState === "complete" && toState === "running") {
          line.classList.add("active");
        } else if (toState === "complete") {
          line.classList.remove("active");
          line.style.opacity = "0.85";
          line.setAttribute("stroke", "var(--accent-good)");
        }
      });
    }

    log(tag, message) {
      const time = new Date();
      const ts = `${fmt.pad2(time.getHours())}:${fmt.pad2(time.getMinutes())}:${fmt.pad2(time.getSeconds())}`;
      const line = document.createElement("div");
      line.className = "log-line";
      line.innerHTML = `<span class="log-time">${ts}</span><span class="log-tag ${tag}">${tag.toUpperCase()}</span><span class="log-msg">${message}</span>`;
      this.logEl.appendChild(line);
      this.logEl.scrollTop = this.logEl.scrollHeight;
    }

    reset() {
      Object.values(this.nodes).forEach(el => { el.dataset.state = "idle"; const m = el.querySelector("[data-meta]"); if (m) m.textContent = ""; });
      this.edges.forEach(({ el }) => { el.classList.remove("active"); el.removeAttribute("stroke"); el.style.opacity = ""; });
      this.logEl.innerHTML = "";
    }
  }

  window.AgentFlow = AgentFlow;
})();
