# PULSE — Pitch Talk Track
### Speaker Notes · Chinmoy Chakraborty · May 2026

> **How to use this document**
> Each section maps 1:1 to a slide. The *Say* block is what you speak aloud.
> The *Anticipate* block handles the question a sharp CIO is most likely to ask.
> Keep the deck moving — you have ~12 minutes before the live demo.

---

## Slide 1 — Cover
**"Multi-Agent Command Center for Retail & Consumer Goods"**

### Say
> "Good morning. What I'm going to show you today is not a prototype and not a concept deck.
> It is a running system — the entire backend is live on my laptop right now, connected to real AI models.
> We built this to answer one question: what does a *production-grade* multi-agent system actually look like in a retail operations context?
> The answer is PULSE."

### Anticipate
- *"What does PULSE stand for?"* — It's a name, not an acronym. The idea is that the system has a continuous heartbeat — it monitors, it thinks, it acts.
- *"Is this connected to our actual data?"* — No. It runs against a synthetic but structurally realistic SQLite database — same schema shape as your POS/WMS outputs. Swapping the data layer is a config change, not a rewrite.

---

## Slide 2 — Agenda
**Six chapters, then a live demo**

### Say
> "Here is what we will cover. Five short chapters to set context, then I will hand the floor to the actual running system.
> By the time we get to the demo, you will know exactly what you are looking at and why it is architecturally different from the LLM experiments you have probably seen before."

### Note
Pause briefly on the "Live Demo" row (highlighted in amber). Let the audience register that this is the destination.

---

## Slide 3 — PULSE Overview
**Introducing PULSE**

### Say
> "PULSE is a multi-agent command center. It is not a chatbot.
> The difference matters: a chatbot is one model answering one question.
> PULSE is a network of specialist AI agents — each with a defined role and tool access — that collaborate to produce a coordinated answer.
>
> Four properties make this production-worthy, not just a demo:
> - **Multi-agent** — five domain specialists run in parallel, not sequentially
> - **MCP-backed** — every agent accesses data through a typed, observable tool interface — more on this in slide 5
> - **Streaming** — you see tokens as they arrive; no waiting for a spinner
> - **Observable** — every agent call, every tool dispatch, every token is traced in LangSmith"

### Anticipate
- *"How is this different from a ReAct agent or a plain GPT-4 call?"* — A single ReAct loop plans and acts sequentially. PULSE fans out 5 specialists at the same moment, each doing one thing well, then synthesizes. It's parallel, typed, and each agent boundary is enforced by a schema contract.

---

## Slide 4 — The Problem
**Retail operations are losing $112B a year**

*[The animated counter runs from 0 to 112 as the slide enters.]*

### Say
> "The dollar number is from NRF and McKinsey research — it covers operational leakage from inefficient replenishment, manual disruption response, and slow decision loops.
>
> But the real story is the five cards on this slide. These are not abstract pain points — they are the actual workflows we replaced:
>
> **01 — 12 dashboards every morning.**
> Your store manager opens POS, then WMS, then the labor app, then the promo portal. Each in a different system. Thirty minutes before they have an actionable picture.
>
> **02 — Disruption response is manual.**
> A hurricane warning hits. Someone books a conference room, dials the supplier, builds a spreadsheet. Hours pass. By the time a decision is made, the window has closed.
>
> **03 — Siloed systems.**
> POS knows what sold. WMS knows what's in stock. HRIS knows who's working. But none of these systems talk to each other. The manager is the integration layer — in their head.
>
> **04 — Decisions take hours.**
> Markdown timing, replenishment approval, labor reallocation — each requires a human to aggregate data that already exists but is spread across five systems.
>
> **05 — LLM pilots stall.**
> Most enterprise AI pilots fail not because the LLM is wrong, but because there is no clean boundary between the AI and the data. No schema, no audit trail, no way to know what the model actually saw."

### Anticipate
- *"$112B seems very high."* — That's an industry-wide figure. At the store level, McKinsey estimates 2-5% of revenue is lost to suboptimal in-season decisions. For a $500M banner, that's $10-25M. PULSE addresses the decision-speed component directly.

---

## Slide 5 — The Solution
**An agent network that thinks together**

*[The SVG network animates: Orchestrator appears, five specialist nodes fan out, edges draw in, Synthesizer lights up.]*

### Say
> "Here is how PULSE answers those five pain points.
>
> The network you see has three tiers:
>
> **The Orchestrator** (left node) receives your question and decides which specialists to activate. Not all five run every time — if you ask about sales trends, it routes to Sales and maybe Inventory. It doesn't bother Labor or Reviews.
>
> **Five Specialist Agents** (middle tier) each own one domain:
> - Sales Performance — revenue, category trends, hour-of-day signals
> - Inventory & Stockout — days of supply, critical replenishment, category risk
> - Labor & Scheduling — coverage gaps, callouts, cost vs target
> - Promotion & Competitive Intel — promo lift, competitor threats, recommended moves
> - Customer Voice — review sentiment, complaint themes, NPS shifts
>
> These five run **simultaneously**. Not one after the other. In parallel.
>
> **The Synthesizer** (right node) waits for all specialist briefings, then produces the final answer — headline, root cause, three recommended actions with owners and ETAs.
>
> The four pillars at the bottom are the non-negotiables that make this enterprise-ready:
> multi-agent orchestration, schema-validated MCP tools, token-streaming, and a full LangSmith audit trail."

### Anticipate
- *"What prevents one agent from contradicting another?"* — The Synthesizer's job. It's explicitly prompted to connect dots across signals and surface conflicts, not just concatenate. If Sales says revenue is up but Reviews says customer satisfaction is cratering, the Synthesizer flags that tension.

---

## Slide 6 — How It Works
**One question. Five specialists. Automatic.**

*[Nine workflow steps light up in sequence as the slide enters.]*

### Say
> "Let me walk through the nine steps — this is the actual execution path, not a diagram invented for a slide.
>
> **1 — Question captured.** You type a question in the UI. A WebSocket connection opens.
>
> **2 — Orchestrator routes.** The Orchestrator LLM reads your question and returns a JSON array of agent names. Selective — it only calls what's needed. 'Why are dairy sales down?' returns `["sales", "inventory"]`. 'Morning briefing' returns all five.
>
> **3 — Specialist fan-out.** Selected specialists are launched as parallel async tasks. If three are called, they run concurrently — not waiting for each other.
>
> **4 — Tool Discovery.** This is where it gets architecturally interesting — and honest. Each specialist calls `server.list_tools()` at runtime to discover every tool registered on the MCP server. There are ten. The specialist then calls `llm.bind_tools()` — handing all ten tool schemas to the LLM. The model reads each tool's name, description, and input schema, and decides for itself which one to call. No hardcoded assignments. No Python list that says 'Sales agent always calls this tool.' The LLM makes that decision based on its role and the question.
>
> **5 — Autonomous Tool Call.** The LLM returns a tool call — or a set of them. The system executes those calls through the MCP server, which validates the arguments against the JSON Schema before touching the database. Data comes back in under 60 milliseconds. These are the calls you see lighting up in the MCP Monitor popup during the demo.
>
> **6 — Specialist briefings.** With tool results in hand, a second LLM call produces the specialist's structured 3-5 bullet briefing. This is where domain reasoning happens — the model interprets the numbers and draws conclusions.
>
> **7 — Streaming synthesis.** The Synthesizer receives all briefings and begins composing the final answer. You see tokens streaming to the screen in real time — no waiting.
>
> **8 — Live telemetry.** While this runs, the token counter, latency pill, cost estimate, and agent summary update live in the header. The MCP Monitor shows every tool call with caller, arguments, latency.
>
> **9 — Actions + trace.** The final answer includes recommended actions with owners and ETAs. The complete run — every prompt, every tool call, every response — is recorded in LangSmith.
>
> The bottom callout captures the business case: what your ops team spent two hours doing manually — gathering data across five systems, synthesizing it, writing the brief — happens automatically in one query. With an agent that figured out which data to pull on its own."

### Anticipate
- *"How long does it actually take?"* — In this demo, 30-90 seconds depending on Gemini's reasoning depth and how many specialists run. The bottleneck is two LLM calls per specialist — one for tool selection, one for the briefing. Data retrieval itself is under 60ms. In production with a faster model or parallel caching, this compresses significantly. The value isn't raw latency — it's replacing a 2-hour manual process.
- *"Why does each agent need two LLM calls?"* — The first call is tool selection via `bind_tools()` — the LLM reads all tool schemas and decides what data it needs. The second call is reasoning — it takes the actual data and produces the briefing. These are fundamentally different cognitive tasks. Conflating them produces worse output than separating them.

---

## Slide 7 — Architecture
**Standards all the way down**

*[Architecture stack slides in from left. MCP demo button is on the right.]*

### Say
> "Five layers, all standards-based. I will move quickly and point you to the one that matters most for the enterprise conversation.
>
> **UI layer** — Plain HTML/CSS/JS served by FastAPI. No framework dependencies. WebSocket connection for streaming. Dark and light theme.
>
> **FastAPI + WebSockets** — The backend. Async Python. Each agent run is a streaming WebSocket session — tokens and events arrive as they are produced, not buffered.
>
> **LangGraph Orchestration** — Seven agents across two workflows (Store Manager and War Room), modeled as a directed acyclic graph. LangSmith traces every node.
>
> **MCP Tool Server** — This is the layer I want to spend a moment on. It is the key architectural differentiator. Ten typed tools with JSON Schema-validated inputs. Every tool call is logged. Agents cannot touch data any other way. I will demonstrate this live in a moment.
>
> **SQLite Data Layer** — 25 tables, 540 rows, auto-seeded. Swap this for your data warehouse and nothing else changes.
>
> *(Click the ▶ Fire MCP Call button on the right)*
>
> Watch the right panel. That was a live call to the MCP server — you can see the tool count, the version, and a sample of tool definitions as a JSON response. This is exactly what each specialist agent does at runtime."

### Deep Dive: What is the MCP Tool Server?

> **MCP (Model Context Protocol)** is a standard interface that defines how AI agents discover and invoke tools.
>
> Think of it as a REST API, but specifically designed for LLMs. Each tool has:
> - A **name** (what the agent calls it by)
> - A **description** (what the LLM reads to decide whether to use it — this is the intelligence interface)
> - An **input schema** (JSON Schema defining valid arguments and types)
> - A **handler** (the actual function that runs and returns data)
>
> The critical point: in this system, no specialist agent has a hardcoded tool assignment in Python. Each agent calls `server.list_tools()` at runtime, gets all ten tool schemas, binds them to the LLM via `bind_tools()`, and the model autonomously decides which to invoke based on its role identity and the tool descriptions. The tool descriptions **are** the agent-to-data contract.
>
> The ten tools in this system and what each one returns:
>
> | Tool | Returns |
> |------|---------|
> | `get_sales_snapshot` | Today's revenue vs forecast, transactions, traffic, hourly curve, top/bottom category movers |
> | `get_inventory_health` | On-hand inventory, days of supply, stockout SKUs, critical replenishment priorities |
> | `get_labor_status` | Scheduled vs actual hours, department coverage gaps, callouts, labor cost vs target |
> | `get_promotions_and_competitive` | Active promos with redemption and lift data, competitor promo intel |
> | `get_customer_voice` | Review sentiment scores, top complaint themes, recent verbatim feedback |
> | `get_store_directory` | All stores — location, format, square footage, manager |
> | `get_supplier_directory` | Supplier catalogue with lead times, reliability scores, alternate options, risk flags |
> | `get_disruption_scenarios` | Pre-modeled disruption events — hurricane, port strike, cyber, supplier failure |
> | `get_historical_analytics` | 90-day revenue trends, 30-day category trajectories, agent run history |
> | `get_dashboard_snapshot` | Composite KPI snapshot — alerts, top movers, review highlights for the active store |

### The Critical Question: What is "Typed JSON-RPC contract, schema-validated arguments"?

**The plain-English explanation:**

Every MCP tool is defined with a formal contract before any agent is allowed to call it. That contract says: "If you want to call `get_supplier_directory`, you may pass one optional argument named `category`, it must be a string, here is an example." The system validates this contract *before* the call reaches the database.

**Why does this matter? Four reasons a CIO should care:**

1. **Reliability at the AI boundary.**
   LLMs can hallucinate. They might try to pass `store_id: 42` when the spec says `store_id` must be a string like `"ST-014"`. Schema validation catches this at the tool boundary and returns a structured error — the agent never silently feeds garbage to your database.

2. **Auditability and compliance.**
   Every tool call is logged with the exact arguments passed and the exact data returned. When your compliance team asks "what data did the AI see when it recommended that markdown?", you have a precise, timestamped answer. Not a guess — a record.

3. **Interoperability.**
   Any client — a different LLM, a human operator, an automated pipeline — can call the same MCP tools using the same schema. The intelligence layer (which model, which agent framework) is completely decoupled from the data access layer.

4. **Safe extension.**
   When you add a new tool — say, `get_loyalty_data` — you define its schema once. Every agent that uses MCP automatically discovers it. You do not rewrite agent prompts or update connection strings. The contract handles it.

**The analogy that lands with CTOs:** Think of it as Swagger/OpenAPI for your AI agents. The schema is the contract. The agents are the consumers. The tools are the microservices. You already manage this discipline for human-facing APIs — MCP brings the same discipline to AI-facing data access.

### Anticipate
- *"Is MCP a Anthropic/Gemini proprietary thing?"* — No. MCP is an open standard published by Anthropic (the company behind Claude), but it is model-agnostic. This demo runs on Gemini. The tool layer doesn't care which model is calling it.
- *"Can multiple agents call the same tool simultaneously?"* — Yes. Each call is independently logged with a caller identifier (which agent made the call, when, with what arguments).

---

## Slide 8 — Live Demo Handoff
**You've seen the pitch**

### Say
> "We have covered the problem, the solution, how it works, and the architecture.
>
> Now I am going to show you all of it running.
>
> Three paths from this screen:
>
> **Run the Morning Briefing** — click this and the five specialists activate in parallel. You will see the agent network light up live, the MCP monitor pop up showing every tool call, and a streaming brief arrive in real time. The question is already pre-filled: 'Give me my morning briefing.'
>
> **Trigger the War Room** — this activates the six-agent Disruption Response workflow against a hurricane scenario. Different specialist topology, same architectural principles.
>
> **Open the Markmap** — a visual walkthrough of every layer of the system in an interactive mind map.
>
> Let's start with the Morning Briefing."

*(Click 'Run the Morning Briefing' button or the Store Manager handoff card)*

---

## General Q&A Prep

**"How long to production-ize this for our environment?"**
The data layer swap (SQLite → your warehouse/API) and auth integration are the main workstreams. The agent topology, tool server, and UI are all production-grade today. Realistic estimate: 8-12 weeks for a single use case with a dedicated team.

**"What model are you using? Can we use our own?"**
Gemini 2.5 Pro today. Because agents call the LLM through LangChain's model interface, swapping to GPT-4o, Claude, or a self-hosted Llama is a one-line config change. The tool layer and orchestration don't care.

**"What about hallucination?"**
Every specialist is grounded — it only sees data returned by its MCP tool. The Synthesizer is explicitly instructed "do not invent numbers." LangSmith traces let you verify exactly what data the model had. Hallucination risk is at its lowest when the model is not asked to recall facts but to reason over facts you hand it.

**"What does this cost to run?"**
The telemetry in the header shows live cost-per-run. A full Store Manager briefing with Gemini 2.5 Pro typically costs $0.05-0.10. At 20 runs per day per store, that is roughly $1/day per store — orders of magnitude cheaper than the analyst time it replaces.
