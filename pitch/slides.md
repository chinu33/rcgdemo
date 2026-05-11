---
theme: default
title: PULSE — Multi-Agent Command Center
info: |
  ## PULSE
  A multi-agent AI command center for Retail & Consumer Goods.
  Built with LangGraph, MCP, Gemini, FastAPI, and SQLite.
class: text-center
highlighter: shiki
lineNumbers: false
mdc: true
fonts:
  sans: 'Inter'
  mono: 'JetBrains Mono'
transition: slide-left
drawings:
  persist: false
---

<style>
@import './style.css';

.slide-1-title {
  font-size: clamp(80px, 14vw, 200px);
  line-height: 0.95;
  letter-spacing: -0.04em;
  margin: 0;
}
.slide-1-tagline {
  font-size: clamp(18px, 2.4vw, 28px);
  color: var(--pulse-text);
  margin-top: 24px;
  font-weight: 500;
}
.slide-1-tagline em {
  background: linear-gradient(135deg, var(--pulse-accent-1), var(--pulse-accent-2));
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
  font-style: normal;
}
.slide-1-meta {
  display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;
  margin-top: 30px;
}
.eyebrow-cyan { color: var(--pulse-accent-2); }
.eyebrow-warm { color: var(--pulse-accent-warm); }
.eyebrow-good { color: var(--pulse-accent-good); }
.eyebrow-bad  { color: var(--pulse-accent-bad);  }
.eyebrow-pink { color: var(--pulse-accent-3);    }
</style>

<div class="pulse-eyebrow eyebrow-cyan">INTRODUCING</div>

<h1 class="slide-1-title">PULSE</h1>

<div class="slide-1-tagline">
Multi-Agent Command Center for <em>Retail & Consumer Goods</em>
</div>

<div class="slide-1-meta">
  <span class="pulse-pill"><span class="dot purple"></span>Multi-agent</span>
  <span class="pulse-pill"><span class="dot amber"></span>MCP-backed</span>
  <span class="pulse-pill"><span class="dot cyan"></span>Streaming</span>
  <span class="pulse-pill"><span class="dot green"></span>Observable</span>
</div>

<div class="abs-b mb-8 text-sm opacity-60">
Press <kbd>Space</kbd> or <kbd>→</kbd> to advance
</div>

<!--
Speaker note: Open with energy. The audience just needs to know "this is a real, working multi-agent system for retail." Don't read the meta pills — they'll see them.
-->

---
layout: default
---

<div class="pulse-eyebrow eyebrow-warm">THE STATUS QUO</div>

# Retail operations are losing <span class="pulse-num">$112B</span> a year

<div class="pulse-grid-cards mt-10">

<div class="pulse-card" v-click>
  <div class="text-3xl mb-2">📊</div>
  <div class="font-bold">12+ dashboards every morning</div>
  <div class="text-sm opacity-70 mt-1">Store managers drown in fragmented data sources</div>
</div>

<div class="pulse-card" v-click>
  <div class="text-3xl mb-2">🌪</div>
  <div class="font-bold">Disruption response is manual</div>
  <div class="text-sm opacity-70 mt-1">Hours of war-rooming for every weather, port, supplier event</div>
</div>

<div class="pulse-card" v-click>
  <div class="text-3xl mb-2">🔌</div>
  <div class="font-bold">Siloed systems</div>
  <div class="text-sm opacity-70 mt-1">POS, WMS, HRIS, promos, reviews, supplier master — none talk</div>
</div>

<div class="pulse-card" v-click>
  <div class="text-3xl mb-2">⏱</div>
  <div class="font-bold">Decisions take hours</div>
  <div class="text-sm opacity-70 mt-1">Markdown, replenishment, transfer choices arrive too late</div>
</div>

<div class="pulse-card" v-click>
  <div class="text-3xl mb-2">🤖</div>
  <div class="font-bold">LLM pilots stall</div>
  <div class="text-sm opacity-70 mt-1">No clean tool/data boundary, no audit trail, no observability</div>
</div>

</div>

<!--
The goal of this slide is to make the CIO nod 5 times. Each pain point lands separately.
-->

---
layout: default
---

<div class="pulse-eyebrow eyebrow-good">THE SOLUTION</div>

# An agent network that <em style="background: linear-gradient(135deg, var(--pulse-accent-1), var(--pulse-accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-style: normal;">thinks together</em>

<div class="grid grid-cols-2 gap-6 mt-8">

<div>

### Two production-grade flows

<v-clicks>

- 🛒 **Store Manager** — ask anything, 5 specialists answer in parallel
- 🌪 **War Room** — inject a disruption, agents coordinate response

</v-clicks>

</div>

<div>

### Backed by

<v-clicks>

- **MCP** — 10 typed, schema-validated tools
- **Token streaming** — answers appear word-by-word
- **LangSmith** — every agent + tool call traced
- **Glass UI** — dashboard, analytics, MCP console

</v-clicks>

</div>

</div>

<div class="mt-10 grid grid-cols-4 gap-3" v-click>
  <div class="pulse-card text-center">
    <div class="pulse-num text-2xl">7</div>
    <div class="text-xs opacity-70 mt-1">Agents</div>
  </div>
  <div class="pulse-card text-center">
    <div class="pulse-num text-2xl">10</div>
    <div class="text-xs opacity-70 mt-1">MCP Tools</div>
  </div>
  <div class="pulse-card text-center">
    <div class="pulse-num text-2xl">25</div>
    <div class="text-xs opacity-70 mt-1">DB Tables</div>
  </div>
  <div class="pulse-card text-center">
    <div class="pulse-num text-2xl">~5s</div>
    <div class="text-xs opacity-70 mt-1">End-to-end</div>
  </div>
</div>

---
layout: default
---

<div class="pulse-eyebrow eyebrow-bad">END-TO-END</div>

# From question to action in <em style="color: var(--pulse-accent-3); font-style: normal;">seconds</em>

<div class="grid grid-cols-3 gap-3 mt-6">

<v-clicks>

<div class="pulse-step"><div class="pulse-step-num">1</div><div><strong>Question Captured</strong><div class="text-xs opacity-70">UI input or disruption injection</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">2</div><div><strong>Orchestrator Routes</strong><div class="text-xs opacity-70">LLM picks specialists</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">3</div><div><strong>Specialist Fan-Out</strong><div class="text-xs opacity-70">Up to 5 in parallel</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">4</div><div><strong>MCP Tool Calls</strong><div class="text-xs opacity-70">Typed JSON-RPC contract</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">5</div><div><strong>SQL Retrieval</strong><div class="text-xs opacity-70">SQLite, 25 tables</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">6</div><div><strong>Specialist Briefings</strong><div class="text-xs opacity-70">3–5 bullet markdown</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">7</div><div><strong>Streaming Synthesis</strong><div class="text-xs opacity-70">Gemini astream → UI</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">8</div><div><strong>Live Telemetry</strong><div class="text-xs opacity-70">ms · tokens · $ · agents</div></div></div>

<div class="pulse-step"><div class="pulse-step-num">9</div><div><strong>Actions + Trace</strong><div class="text-xs opacity-70">Owner, ETA, LangSmith</div></div></div>

</v-clicks>

</div>

<!--
The story arc: question in, action out. The intermediate steps are observable but bounded.
-->

---
layout: default
---

<div class="pulse-eyebrow eyebrow-pink">PRODUCTION-READY STACK</div>

# Standards all the way down

<div class="grid grid-cols-2 gap-6 mt-8">

<div>

<div class="pulse-arch-row" v-click>
  <div class="pulse-arch-icon">🎨</div>
  <div>
    <div class="pulse-arch-title">UI Layer</div>
    <div class="pulse-arch-sub">Glass morphism · Dark + Light · WS-streamed</div>
  </div>
</div>

<div class="pulse-arch-row" v-click>
  <div class="pulse-arch-icon">🔌</div>
  <div>
    <div class="pulse-arch-title">FastAPI + WebSockets</div>
    <div class="pulse-arch-sub">Async Python · streaming events to UI</div>
  </div>
</div>

<div class="pulse-arch-row" v-click>
  <div class="pulse-arch-icon">🧠</div>
  <div>
    <div class="pulse-arch-title">LangGraph Orchestration</div>
    <div class="pulse-arch-sub">7 agents · 2 workflows · LangSmith-traced</div>
  </div>
</div>

<div class="pulse-arch-row mcp" v-click>
  <div class="pulse-arch-icon">⚙</div>
  <div>
    <div class="pulse-arch-title">MCP Tool Server</div>
    <div class="pulse-arch-sub">10 typed tools · JSON Schema validated</div>
  </div>
</div>

<div class="pulse-arch-row" v-click>
  <div class="pulse-arch-icon">🗄</div>
  <div>
    <div class="pulse-arch-title">SQLite Data Layer</div>
    <div class="pulse-arch-sub">25 tables · 540 rows · auto-seeded</div>
  </div>
</div>

</div>

<div class="pulse-card" v-click>

### Why this stack

- **MCP** is vendor-neutral — same tools work with Anthropic, Google, OpenAI
- **LangGraph** state graphs are visible & replayable
- **LangSmith** gives audit-grade observability
- **SQLite** here, **Snowflake / BigQuery** in production via the same MCP contract
- **No build step** on the frontend — vanilla HTML/CSS/JS, deploys anywhere

```python
# A real specialist's data fetch
call = await mcp_server.call_tool(
    "get_inventory_health",
    {"store_id": "ST-014"},
    caller="inventory_agent",
)
```

</div>

</div>

---
layout: center
class: text-center
---

<div class="pulse-eyebrow eyebrow-cyan">YOU'VE SEEN THE PITCH</div>

# Now watch the agents <em style="background: linear-gradient(135deg, var(--pulse-accent-1), var(--pulse-accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-style: normal;">actually do it</em>

<div class="grid grid-cols-3 gap-4 mt-12 max-w-4xl mx-auto">

<a href="http://localhost:8000/" target="_blank" class="pulse-card text-center no-underline" style="text-decoration: none; color: inherit;">
  <div class="text-4xl mb-3" style="background: linear-gradient(135deg, var(--pulse-accent-1), var(--pulse-accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">▶</div>
  <div class="font-bold">Open the Live App</div>
  <div class="text-sm opacity-70 mt-1">localhost:8000</div>
</a>

<a href="http://localhost:8000/markmap" target="_blank" class="pulse-card text-center no-underline" style="text-decoration: none; color: inherit;">
  <div class="text-4xl mb-3" style="background: linear-gradient(135deg, var(--pulse-accent-warm), var(--pulse-accent-3)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🗺</div>
  <div class="font-bold">Markmap Walkthrough</div>
  <div class="text-sm opacity-70 mt-1">/markmap (dark mind-map)</div>
</a>

<a href="https://smith.langchain.com" target="_blank" class="pulse-card text-center no-underline" style="text-decoration: none; color: inherit;">
  <div class="text-4xl mb-3" style="background: linear-gradient(135deg, var(--pulse-accent-good), var(--pulse-accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">📈</div>
  <div class="font-bold">LangSmith Traces</div>
  <div class="text-sm opacity-70 mt-1">Project: rcgdemo</div>
</a>

</div>

<div class="mt-12 text-sm opacity-50">
PULSE · Multi-Agent · MCP-backed · Built for Retail & Consumer Goods
</div>
