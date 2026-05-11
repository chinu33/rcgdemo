# RCG Multi-Agent Command Center — PULSE

A retail & consumer-goods CIO-grade demo of a **true agentic multi-agent AI command center**, combining:

1. **Store Manager Command Center** — 5 specialist agents (Sales, Inventory, Labor, Promo, Reviews) coordinated by an Orchestrator + Synthesizer to answer any operational question.
2. **Disruption War Room** — 6 specialist agents (Detector, Supplier Researcher, Inventory Rebalancer, Impact Modeler, Comms Drafter, Commander) that orchestrate a response to weather, logistics, supplier, or cyber events.

### True Agentic Architecture

Every specialist agent performs **real-time MCP tool discovery** — no hardcoded tool assignments anywhere in the codebase:

1. Agent calls `server.list_tools()` → receives all 10 registered MCP tool schemas at runtime
2. Agent calls `llm.bind_tools(all_tools)` → the LLM reads every tool's name, description, and input schema
3. LLM autonomously decides which tool(s) to call based on its role system prompt and the question
4. Tool call executes through the MCP server with JSON Schema argument validation
5. Second LLM call reasons over the returned data to produce the specialist briefing

Built with **LangChain + LangGraph** (orchestration), **LangSmith** (observability), **Google Gemini 2.5 Pro** (LLM), **FastAPI** (backend), **SQLite** (data layer), and a **glass-morphism HTML/CSS/JS** front-end with a live agent-network visualization, theme toggle, and a floating telemetry pill (latency · tokens · cost · agent summary).

---

## Quickstart

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit [.env](.env):
- `GOOGLE_API_KEY` — your Gemini API key. **If left blank, the app runs in demo mode** with high-quality scripted responses (perfect for offline pitches).
- `LANGSMITH_API_KEY` (optional) — turns on full LangSmith tracing.
- `GEMINI_INPUT_COST_PER_1M` / `GEMINI_OUTPUT_COST_PER_1M` — pricing knobs for the live cost pill.

### 3. Run

```bash
python3 -m backend.main
```

Open <http://localhost:8000>.

The SQLite database (`data/rcg.db`) is **auto-seeded on first run** from `data/seed/*.json`.

To rebuild the DB anytime:

```bash
python3 -m backend.seed --rebuild
```

---

## What's inside

### Tabs

| Tab | What it shows |
|---|---|
| **Dashboard** | KPIs, hourly sales vs forecast, category performance, critical alerts, inventory health, top movers, customer reviews. |
| **Store Manager** | Conversational interface to the agent network. Live agent-flow viz, per-specialist briefings, synthesized answer. |
| **War Room** | Pick a disruption scenario, watch agents fan out, get the commander brief + drafted supplier email + customer notice. |
| **Analytics** | 90-day revenue trend, 30-day category trajectories, agent activity ramp, cost/latency by agent, disruption response history, agent telemetry heatmap, and a live SQLite stats strip. |

### Wow-factor elements

- **Glass morphism** UI with animated aurora background and grid overlay
- **Dark-by-default**, one-click light theme toggle
- **Floating telemetry pill** — live ms latency, total tokens, cost USD, agent count
- **Behind-the-scenes overlay** — concentric rings + caption when an AI action fires
- **Live agent-flow visualization** — nodes pulse, edges animate as agents work
- **Streaming WebSocket** — every agent start/finish updates the UI in real time

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  Browser (glass UI, Chart.js, vanilla JS)                      │
│   ▲                                                            │
│   │  REST  + WebSocket (streaming events)                      │
│   ▼                                                            │
│  FastAPI (backend/main.py)                                     │
│   ├─ LangGraph: store_manager_graph.py                         │
│   │     Orchestrator → [Sales, Inventory, Labor,               │
│   │                     Promo, Reviews] → Synthesizer          │
│   │     Each specialist: list_tools() → bind_tools()           │
│   │                      → LLM selects tools → MCP call        │
│   │                      → LLM produces briefing               │
│   ├─ LangGraph: disruption_graph.py                            │
│   │     Detector → [Supplier, Rebalancer,                      │
│   │                 Impact] → Comms → Commander                │
│   ├─ MCP Tool Server (backend/mcp_tools/)                      │
│   │     10 typed tools · discovered at runtime by agents       │
│   │     JSON Schema validated · every call logged              │
│   ├─ Telemetry: latency / tokens / $ per agent                 │
│   └─ Data layer: SQLite (data/rcg.db)                          │
│        25 tables · ~540 rows · seeded from JSON                │
└────────────────────────────────────────────────────────────────┘
```

### Per-Specialist Execution (Two LLM Calls)

```
Step 1 — Tool Discovery & Selection
  server.list_tools()          →  10 tool schemas (name, description, input_schema)
  server.as_lc_tools(names)    →  LangChain StructuredTool objects
  llm.bind_tools(lc_tools)     →  LLM sees all tool schemas
  llm.ainvoke([role, question]) →  LLM returns tool_calls[] — autonomous decision

Step 2 — Execution & Briefing
  server.call_tool(name, args)  →  validates args, queries SQLite, returns JSON (<60ms)
  llm.ainvoke([role, results])  →  LLM reasons over data, produces 3-5 bullet briefing
```

---

## Data layer

The demo ships with a self-contained **SQLite database** at `data/rcg.db`. Schema and seed live in:

- [backend/db.py](backend/db.py) — schema + connection helpers
- [backend/seed.py](backend/seed.py) — seeder that mixes static JSON snapshots with procedurally-generated 90-day timeseries
- [data/seed/](data/seed/) — raw seed files (stores, suppliers, scenarios, etc.)

Tables include: `stores`, `category_health`, `critical_skus`, `sales_today/yesterday/hourly`, `sales_daily_history` (90 days), `sales_category_history` (30 days × 10 categories), `labor_today`, `departments`, `callouts`, `promotions`, `competitor_intel`, `reviews_summary`, `review_themes`, `recent_reviews`, `suppliers`, `disruption_scenarios`, `agent_runs_daily`, `agent_breakdown`, `disruptions_handled`.

The Analytics tab surfaces a live `SQLite · N tables · M rows` strip that reads directly from `/api/db-info`.

---

## Demo flow (suggested for a CIO)

1. Open **Dashboard** — explain the morning briefing surface.
2. Click **▶ Run Morning Briefing** — agents fan out, telemetry pill fires, synthesized answer lands in seconds.
3. Switch to **War Room** — select **Hurricane Ingrid** → **▶ Trigger Response**. Walk through the live agent flow + drafted comms.
4. Open **Analytics** — show 90-day trend, agent ramp, cost-per-agent, and the live SQLite layer strip. Toggle the **light theme** for contrast.

---

## File map

```
rcgdemo/
├── .env.example
├── requirements.txt
├── data/
│   ├── rcg.db              # auto-generated SQLite database
│   └── seed/               # raw JSON seed snapshots
├── backend/
│   ├── main.py             # FastAPI app + WebSocket endpoints
│   ├── config.py           # env-driven settings
│   ├── db.py               # SQLite schema + helpers
│   ├── seed.py             # DB seeder (JSON + generators)
│   ├── data_store.py       # data access layer
│   ├── llm.py              # Gemini wrapper
│   ├── telemetry.py        # latency/token/cost tracing
│   └── agents/
│       ├── prompts.py
│       ├── store_manager_graph.py
│       ├── disruption_graph.py
│       └── demo_responses.py
└── frontend/
    ├── index.html
    ├── css/                # base, themes, glass, components, animations
    └── js/                 # app, theme, api, telemetry, charts,
                            # agent-viz, dashboard, store-manager,
                            # war-room, analytics
```
