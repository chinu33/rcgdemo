---
title: PULSE — Multi-Agent Command Center for Retail & Consumer Goods
markmap:
  colorFreezeLevel: 2
  initialExpandLevel: 2
  maxWidth: 360
  spacingHorizontal: 80
  spacingVertical: 14
---

# 🟣 **PULSE Platform**

## 🏬 The Problem (Retail Ops Today)
- Store managers drown in 12+ dashboards every morning
- Disruption response is manual, slow, fragmented across teams
- POS, WMS, HRIS, promos, reviews, supplier data — all siloed
- Decisions take hours when they need to take minutes
- Industry leakage: ~$112B annual shrink + billions in poorly-timed markdowns
- LLM pilots stall because there's no clean tool / data boundary

## ✅ The Solution: PULSE
- **Multi-agent AI Command Center** for Retail & Consumer Goods
- Two production-grade flows in one app
  - 🛒 **Store Manager** — ask anything, 5 specialists answer
  - 🌪 **Disruption War Room** — inject an event, agents coordinate response
- **True agentic tool discovery** — every specialist calls `server.list_tools()` at runtime; LLM autonomously selects tools via `bind_tools()` — no hardcoded assignments
- **MCP-backed tool layer** — 10 typed, schema-validated tools; agents discover and call them autonomously
- **Real-time token streaming** — answers appear word-by-word
- **End-to-end observability** — LangSmith trace per agent, per tool call
- **Glass-morphism UI** — Dashboard, Store Manager, War Room, MCP Console, Analytics

## 🛠 End-to-End Workflow
### 1. 🎤 Question Captured
- Manager asks via UI ("Why are dairy sales down today?")
- OR a disruption is injected (Hurricane Ingrid, Port of Long Beach stoppage…)
- WebSocket stream opens to backend
### 2. 🧭 Orchestrator Routes Intent
- LLM decides which specialist subset to invoke
- Returns a typed list e.g. `["sales","inventory","promo"]`
- Replaces brittle "always call all" routing
### 3. 📡 Specialist Fan-Out (parallel)
- Store Manager: up to **5 specialists** in parallel
- War Room: **3 specialists** in parallel after the Detector
- Each agent has a focused role system prompt — **no hardcoded tool assignments**
### 4. 🔍 True Agentic Tool Discovery
- Each specialist calls `server.list_tools()` → discovers **all 10 MCP tools** at runtime
- `llm.bind_tools(all_tools)` — LLM reads every tool's name, description, and input schema
- LLM **autonomously decides** which tool(s) to call based on its role and the question
- **LLM call 1 of 2**: tool selection — no Python code chooses the tool
### 5. 🔌 Autonomous MCP Tool Execution
- MCP server validates arguments against JSON Schema before touching the database
- Tool handler queries `rcg.db` (25 tables, ~540 rows) — under 60ms
- **Live MCP Monitor** drawer pops up showing every call, caller, args, latency
- Typed JSON-RPC contract — schema-validated at the tool boundary
### 6. 📊 Specialist Briefings
- **LLM call 2 of 2**: LLM reasons over tool results → produces 3–5 bullet briefing
- Token usage, latency, $ cost captured per agent across both LLM calls
### 7. ✨ Synthesizer Streams Final Brief
- Composes the executive answer from all specialist briefs
- Token-level streaming via Gemini `astream` → blinking cursor in UI
### 8. ⚡ Live Telemetry
- Pill below topbar shows: ms latency · tokens · $ cost · agent count
- Per-tool stats (calls, avg latency, last-called) update on every run
### 9. 📋 Actions + Trace
- Recommended actions with **Owner** + **ETA** for each
- Auto-actions enumerated (drafted emails, transfer plans)
- Full run captured in **LangSmith** for audit & replay

## 📊 Executive Dashboard & Analytics
### Dashboard tab
- 6 live KPI tiles — Revenue, Variance, Traffic, Basket, Stockouts, Labor %
- Hourly sales vs forecast (Chart.js, gradient fill)
- Critical alerts panel (rules-driven from real data)
- Inventory health by category (10 cats with days-of-supply pills)
- Customer voice — recent reviews + sentiment delta
### Analytics tab
- 90-day daily revenue trend (with disruption dip story)
- 30-day category trajectories — 10 categories
- Agent activity ramp + cost/latency breakdown
- 90-day disruption response history + minutes-to-response
- Live SQLite stats strip — tables, rows, schema visible

## 🤖 AI & Intelligence Layer
### LLM
- **Google Gemini 2.5 Pro** (configurable model)
- Token-level streaming via the Gemini async API
- Pricing knobs in `.env` for live $/run calculation
### Orchestration
- **LangChain** primitives (`ChatGoogleGenerativeAI`, messages, `bind_tools`)
- **LangGraph** `StateGraph` per workflow
- Parallel fan-out with `asyncio.wait` + WS-friendly event queue
- **Two LLM calls per specialist**: (1) `bind_tools` tool selection, (2) briefing generation
### Observability
- **LangSmith** tracing — every node decorated with `@traceable`
- Project: `rcgdemo` — full run trees with inputs/outputs, per-tool call details
- Structured logging: every agent step, tool call, and exception logged server-side
- Demo-mode fallback so traces still appear without API quota
### Prompt Engineering
- One system prompt per specialist — defines role identity and domain discipline
- Role prompts guide the LLM to call appropriate tools without hardcoding in Python
- Synthesizer prompt enforces Headline / Root Cause / Actions format
- Disruption prompts emit structured comms (supplier email + customer notice)

## ⚙ Architecture & Tech Stack
### Backend
- **Python 3.10** + **FastAPI** + Uvicorn
- WebSocket endpoints stream agent + MCP events to UI
- **SQLite** (`data/rcg.db`) — auto-seeded on first start
- Demo-mode fallback so the UI works offline / without API key
### MCP Layer
- In-process **MCP-compatible tool server** (`backend/mcp_tools/`)
- **10 tools** across 10 categories (sales, inventory, labor, cx, supply_chain, risk, …)
- **No hardcoded tool assignments** — agents call `list_tools()` + `bind_tools()` at runtime
- Tool `description` field is the agent-data contract — LLM reads it to decide what to call
- JSON Schema argument validation before any DB access — rejects hallucinated params
- Every call recorded in server `history` + emitted as WS event
- `/api/mcp/tools` and `/api/mcp/history` endpoints
### Frontend
- Vanilla **HTML / CSS / JS** — no build step
- **Glass Morphism** with animated aurora background
- **Chart.js** for analytics, custom SVG/HTML for agent network viz
- Floating **MCP Live Monitor** drawer during runs
- Token-streaming markdown answer with blinking cursor
- **Dark + Light** themes, persisted to localStorage

## 🔗 Connected Pipeline (Workflow Bridges)
- 🛒 **POS** → `get_sales_snapshot` → Sales Performance Agent
- 📦 **WMS / ERP** → `get_inventory_health` → Inventory & Stockout Agent
- 👥 **HRIS / Workforce Mgmt** → `get_labor_status` → Labor & Scheduling Agent
- 🎯 **Promo Engine + Competitor feeds** → `get_promotions_and_competitive` → Promo Agent
- 💬 **Review Platforms (Yelp/Google/internal)** → `get_customer_voice` → Reviews Agent
- 🚚 **Supplier Master** → `get_supplier_directory` → Supplier Researcher
- 🌪 **Weather / Logistics feeds** → `get_disruption_scenarios` → Disruption Detector
- 🏬 **Store Master** → `get_store_directory` → Impact Modeler
- 📈 **Data Warehouse** → `get_historical_analytics` → Analytics tab
- 🧭 **Composite snapshot** → `get_dashboard_snapshot` → Morning briefing

## 🎯 Why a CIO Cares
- **True agentic architecture** — agents discover and select tools autonomously via `bind_tools()`; no hardcoded assignments, no brittle mappings
- **Architecture credibility** — agents + MCP + observability is the production pattern, not a chatbot wrapper
- **Vendor-neutral tool layer** — MCP works across Anthropic, Google, OpenAI; swap LLMs without touching the tool layer
- **Auditability** — every tool call schema-validated, every agent step logged, full SQL provenance, LangSmith trace
- **Safe AI boundary** — LLM-hallucinated arguments are rejected at the schema layer before reaching the database
- **Time-to-value** — 25-table SQLite seed; same architecture plugs into Snowflake/BigQuery via MCP tools
- **Demonstrable ROI surfaces** — markdown leakage, shrink, disruption response time, labor variance
