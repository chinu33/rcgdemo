# PULSE — Demo Talk Track
### Live Demo Speaker Notes · Chinmoy Chakraborty · May 2026

> **How to use this document**
> This is your script for the live, running system — after the pitch slides end.
> Each section maps to a specific UI action and what to say while it runs.
> The system takes 30-60 seconds per run — use that time to narrate what the audience is watching.

---

## Before You Begin — Setup Checklist

- [ ] App is running: `http://localhost:8000`
- [ ] Backend started: `cd /Users/data/Data/D/Codes/rcgdemo && source .rcg/bin/activate && python -m backend.main`
- [ ] `GOOGLE_API_KEY` is set in `.env` (real Gemini responses, not demo mode)
- [ ] `LANGSMITH_API_KEY` is set — so you can show the trace afterward
- [ ] LangSmith project is open in a browser tab (optional but powerful if the audience wants depth)
- [ ] Screen resolution is readable — topbar counters should be visible
- [ ] Tab open on **Pitch** slide 8 (Handoff) — that is your launch point

---

## Part 1 — Store Manager Command Center

### Action: Click "Run the Morning Briefing" on Slide 8 (or click the Store Manager tab)

The question pre-fills: *"Give me my morning briefing."*

### Say (before clicking Run Agents)
> "I'm going to ask the system the same question your store manager asks every morning: 'Give me my morning briefing.'
>
> Watch two things simultaneously — the Agent Network on the left, and the MCP Monitor that is about to appear."

### Click Run Agents — then narrate while it runs

> **As the MCP Monitor pops up (bottom-right):**
> "The MCP Monitor just opened. Watch closely — what you see here is the heart of the architecture.
>
> Each agent just called `server.list_tools()`, got all ten tool schemas back, and ran `bind_tools()` to hand those schemas to Gemini. The model read each tool's description and decided which data to fetch. No Python code assigned that — the LLM made that call.
>
> Notice: `MCP · inventory → get_inventory_health · 55ms`. The data retrieval took 55 milliseconds. That is not the AI — that is the typed tool call hitting the database and returning clean JSON. The AI reasoning part is what comes next."

> **As nodes light up in the Agent Network:**
> "The Orchestrator decided which specialists to activate — in this case all five, because 'morning briefing' is a broad question that spans every domain.
>
> Watch the nodes. Each one lights up when its specialist completes its briefing — not when it starts, but when it finishes both LLM calls: tool selection and reasoning."

> **As specialist cards appear on the right panel:**
> "Here comes the first briefing — Promotion & Competitive Intel.
>
> This is not a template. This is Gemini 2.5 Pro reading the actual promotions and competitor data from the MCP tool response and producing structured analysis.
>
> Notice the header: agent name, latency in milliseconds, token count, cost in dollars. That is real telemetry — two LLM calls per specialist baked in."

> **As the Synthesizer streams tokens:**
> "And now the Synthesizer. It has received all five specialist briefings and is composing the final answer. Watch the text arrive token by token — this is streaming, not a buffer-and-dump.
>
> The Synthesizer's output always has the same structure: a one-sentence headline, a root cause paragraph that connects dots across the five signals, and three recommended actions with owners and ETAs."

> **When run completes:**
> "Look at the header. 49,000 milliseconds, 11,000 tokens, about six cents.
>
> That is five specialist analyses plus a synthesis — produced in under a minute from one question. Your morning briefing, without opening a single dashboard."

---

## Understanding the Specialists — What Each One Does

Use these notes if the audience asks "what is the difference between the agents?" or "why not just use one?"

### 🧭 Orchestrator
**Role:** Router and task planner — not a domain expert.
**What it does:** Reads your question and returns a JSON list of which specialists to activate. For "Why are dairy sales down?", it returns `["sales", "inventory"]`. For "Give me my morning briefing", it returns all five. It is selective — it doesn't activate specialists whose domain is irrelevant to the question.
**Why separate:** Keeps the domain specialists clean and focused. The Orchestrator handles routing logic so specialists only think about their domain.
**Key detail:** This is an LLM call too — but a very short one. It returns only a JSON array like `["sales","inventory"]`. No prose, no reasoning — just routing.

### 📈 Sales Performance Agent
**Role:** Revenue analyst for the store.
**What it does:**
1. **Discovers all 10 MCP tools** at runtime by calling `server.list_tools()` — it sees every tool available on the server
2. Calls `llm.bind_tools(all_tools)` — the LLM reads every tool's name, description, and schema, then **autonomously decides** which to call based on its role and the question
3. Executes the chosen MCP tool call(s) through the server (typically `get_sales_snapshot`, with optional `category` filter for targeted questions)
4. Makes a second LLM call to reason over the tool results and produce 3-5 bullets: revenue vs forecast, surprising category movers, hour-of-day signals

**Say:** *"The Sales agent didn't have 'get_sales_snapshot' hard-wired into it. It looked at all ten available tools, read their descriptions, and decided that sales snapshot is the right data for its role. That's real tool discovery — the same way a human analyst would look at what's available and pick the right source."*

### 📦 Inventory & Stockout Agent
**Role:** Supply risk monitor.
**What it does:**
1. **Discovers all 10 MCP tools** at runtime — same discovery mechanism as every other specialist
2. LLM autonomously selects `get_inventory_health` (and `get_supplier_directory` if supplier risk is relevant to the question)
3. Executes the MCP call — gets on-hand inventory, days of supply, stockout SKU list, replenishment flags
4. Second LLM call produces 3-5 bullets: critical stockouts with lost-sales estimates, replenishment priorities, supply risk

**Say:** *"This agent tells you which item will be empty by Thursday, not which item was empty last Tuesday. It's forward-looking. And it got there by autonomously selecting the inventory tool — not because Python told it to."*

### 👥 Labor & Scheduling Agent
**Role:** Workforce coverage monitor.
**What it does:**
1. Discovers all 10 MCP tools — LLM reads descriptions and selects `get_labor_status` as the relevant tool
2. Gets scheduled vs actual headcount, callouts by department, coverage gaps, labor cost vs budget
3. Produces 3-5 bullets: department coverage risk, callout impact, suggested reallocation, labor cost vs target

**Say:** *"The Labor agent knows that Produce has two callouts and Saturday's traffic forecast is 15% above average. A human manager might not surface that conflict until noon. The agent flags it at 8 AM — and it figured out which tool to use to get there."*

### 🎯 Promotion & Competitive Intel Agent
**Role:** Commercial effectiveness monitor.
**What it does:**
1. Discovers all 10 MCP tools — LLM selects `get_promotions_and_competitive` and optionally `get_sales_snapshot` if sales lift data is needed
2. Gets active promotions with redemption rates and lift, plus competitor promotional intel
3. Produces 3-5 bullets: over/underperforming promos, competitive threats, suggested next move

**Say:** *"This agent saw that Target's 'Apparel BOGO 50%' is pulling traffic away from your clearance event. It found that by selecting the promotions tool autonomously — not because it was pre-assigned to it."*

### 💬 Customer Voice Agent
**Role:** Sentiment and complaint analyst.
**What it does:**
1. Discovers all 10 MCP tools — LLM selects `get_customer_voice` as the appropriate tool for its domain
2. Gets review sentiment scores, complaint theme clustering, NPS trend, and recent verbatim feedback
3. Produces 3-5 bullets: sentiment trend and drivers, top complaint categories with mention counts, recommended manager action

**Say:** *"Customer feedback is often the earliest signal. This agent monitors it — and it arrived at the right tool on its own by reading what each tool does and matching that to its role."*

### ✨ Synthesizer
**Role:** Chief of staff — not a specialist, but the integrator.
**What it does:**
1. Receives all specialist briefings as a combined prompt — no tool discovery needed, it works purely from prior agent outputs
2. Produces a three-part final answer: (1) one-sentence headline, (2) root cause paragraph connecting signals across domains, (3) three recommended actions with owner and ETA

**Why this matters:** *"The Synthesizer is where cross-domain intelligence happens. Sales is down AND inventory has stockouts AND a competitor just launched a BOGO — those three signals together tell a different story than any one of them alone. The Synthesizer finds that story."*

---

## MCP Tools vs. Specialist Agents — The Key Distinction

This is the most technically important concept. Use this if someone asks "what is the difference between an agent and a tool?"

### The One-Line Answer
**Specialists think. MCP Tools fetch.** One is AI reasoning; the other is data retrieval.

### The Detailed Explanation

| | MCP Tools | Specialist Agents |
|---|---|---|
| **What it is** | A typed, schema-defined function | An LLM with a focused role prompt |
| **What it does** | Fetches data from the database | Reasons over data to produce insights |
| **Is it AI?** | No — deterministic, reproducible code | Yes — probabilistic reasoning |
| **Speed** | < 60ms | 15-45 seconds (two LLM calls) |
| **Output** | Clean JSON — numbers, records, lists | Prose bullets — interpretation, flags, recommendations |
| **Can it hallucinate?** | No — returns only what is in the database | Constrained by grounding: the agent only sees data its MCP tools returned |
| **Logged?** | Yes — every call with caller, args, result visible in MCP Monitor | Yes — full trace in LangSmith |
| **How tools are selected** | N/A | LLM discovers all tools via `server.list_tools()`, reads descriptions, autonomously decides which to call via `bind_tools()` |
| **How many LLM calls?** | None — pure code | Two: (1) tool selection, (2) briefing generation |

### Why You Need Both

The tools give you ground truth. The agents give you judgment.

An MCP tool can tell you: *"Dairy revenue is $8,400 today vs $10,200 forecast, a -17.6% variance."*
A specialist agent can tell you: *"Dairy is underperforming because Kroger launched a competing yogurt promotion yesterday — recommend a weekend flash sale on a key dairy item to defend basket size."*

The tool has no opinion. The agent has no data. Together, they produce actionable intelligence.

### How Tool Discovery Actually Works (for technical audiences)

```
1. server.list_tools()           → returns all 10 tool schemas (name, description, input_schema)
2. server.as_lc_tools(names)     → converts schemas to LangChain StructuredTool objects
3. llm.bind_tools(lc_tools)      → attaches all 10 tools to the LLM's context
4. llm.ainvoke([role, question]) → LLM reads tool descriptions, returns tool_calls[]
5. server.call_tool(name, args)  → validates args against JSON Schema, executes handler
6. llm.ainvoke([role, results])  → LLM reasons over data, produces specialist briefing
```

Steps 1-5 happen autonomously — no Python code decides which tool a specialist uses. The LLM reads what's available and makes that call itself.

---

## Part 2 — Disruption War Room

### Action: Click War Room tab, choose a scenario, click Run

**Recommended scenario for a CIO audience:** Hurricane Warning (SCN-HURRICANE)

### Say (before clicking Run)
> "Now let's look at the second workflow — the Disruption War Room.
>
> Same architecture, different agent topology. This workflow is triggered by a disruption event, not a question. I'm going to select the hurricane scenario."

### While it runs — narrate the six agents

> "The War Room activates six specialists, not five. They have different roles:
>
> **Disruption Detector** — classifies the event. Type, severity, geography, timeline, initial blast radius. This is the situation room report.
>
> **Supplier Research** — cross-references the affected geography against your supplier directory. Identifies which suppliers are at risk, surfaces viable alternates with lead times, recommends a sourcing pivot.
>
> **Inventory Rebalancer** — looks at inventory positions across the store network. Recommends inter-store and DC transfers. Identifies surge categories to prioritize.
>
> **Store Impact Modeler** — estimates revenue at risk, ranks stores by exposure, models customer experience degradation.
>
> **Communications Drafter** — produces two documents: a supplier email requesting status and alternate fulfillment, and a customer-facing banner acknowledging supply impact without alarming.
>
> **Disruption Commander** (Synthesizer equivalent) — produces the executive brief: one-sentence situation summary, three decisions needed in the next 60 minutes with owners, and two or three actions the agent network can auto-execute now."

### Say when run completes
> "What you just watched normally takes three to four hours of conference calls, spreadsheets, and email chains. That is the war room scenario most of your ops teams have actually lived through.
>
> PULSE does not make the final call — that is still the human's decision. But it collapses the information gathering, analysis, and draft communications into a single automated response. The human's job becomes decision-making, not coordination."

---

## Part 3 — MCP Tools Tab (Optional Deep Dive)

### Action: Click MCP Tools tab

### Say
> "This tab is the control room for the tool server. It gives you visibility into everything the agents touch.
>
> The top row shows the server stats: 10 registered tools, the server name and version.
>
> Below that are the 10 tools with their schemas. Notice each tool has a name, a description, a category, and an input schema. That schema is what enforces the typed contract — if an agent tries to pass an argument of the wrong type, the tool server rejects it before it touches the database.
>
> The tool call history at the bottom updates in real time during a run. You can see which agent called which tool, when, with what arguments. This is your audit trail."

### If asked about the "Typed JSON-RPC contract" phrase

> "Let me be precise about what this means.
>
> **JSON-RPC** is the protocol — a lightweight standard for calling a function by name over JSON. You pass the function name and arguments; it returns a result or an error.
>
> **Typed contract** means each function (tool) is defined with a formal schema before any agent is allowed to call it. The schema says: here is the name, here is the description, here are the valid arguments and their types, here is what is required.
>
> **Schema-validated arguments** means the system validates the arguments against that schema *before* executing the function. Not after. At the boundary.
>
> Why does this matter in an enterprise context?
>
> First: AI models can generate invalid inputs. Gemini might try to call `get_supplier_directory` with `category: 12` — an integer — when the spec says category is a string. Schema validation catches and rejects that before it reaches your database.
>
> Second: auditability. Every call is logged with the exact validated inputs. When your compliance or legal team asks 'what did the AI use to make that recommendation?' you have a precise answer, not a reconstruction.
>
> Third: decoupling. Your data team owns the tools and schemas. Your AI team builds agents. They never need to coordinate on implementation details — they coordinate on the contract. That's a clean engineering boundary.
>
> The analogy: Swagger/OpenAPI for your AI agents. You already enforce this discipline on REST APIs for human clients. MCP brings the same discipline to AI clients."

---

## Closing the Demo

### Say
> "Let me leave you with what you just saw.
>
> One question. Five specialist agents. Real data. Parallel execution. Full observability. Actionable output with owners and ETAs.
>
> No dashboard hopping. No manual aggregation. No war-room coordination for every weather event.
>
> This is what production multi-agent AI looks like in a retail operations context — not a pilot, not a concept — a running system that your team could adapt to your environment.
>
> The architecture is open. The components are standard. The data layer is swappable.
>
> What questions do you have?"

---

## Handling Tough Questions During the Demo

**"The AI took 50 seconds. That's too slow for operations."**
> "You are right that the raw latency is visible. The bottleneck is the LLM reasoning time — specifically Gemini 2.5 Pro with extended thinking, which is a high-quality but deliberate model.
>
> Two ways to compress this in production: (1) use a faster model for less complex queries — Gemini Flash, for example, is 10x faster for structured analysis; (2) pre-run the morning briefing at 7 AM so it is ready when the manager arrives at 8. The architecture supports scheduled runs out of the box.
>
> More importantly: even at 50 seconds, this replaces 30-45 minutes of manual aggregation. That is still a 35x improvement in the manager's time."

**"What if the LLM gets a number wrong?"**
> "Grounding. Every specialist agent sees only the data returned by its MCP tool — it does not draw on the model's training knowledge for store-specific facts.
>
> The Synthesizer is explicitly prompted: 'do not invent numbers — use only the specialist data.'
>
> And the LangSmith trace shows you exactly what data each agent received. If a number looks wrong, you can trace it back to the tool call and verify the source in under 30 seconds."

**"Can we see the LangSmith trace?"**
> *(Switch to the LangSmith browser tab)*
> "Yes. Here is the run we just executed. You can see the full graph — Orchestrator call, each specialist node, each MCP tool call within the specialist, the Synthesizer call. Click into any node to see the exact prompt, the exact tool output, and the exact LLM response. This is your full audit trail."

**"Is this connected to your actual retail data?"**
> "No — this is synthetic data with realistic structure: 25 tables, 540 rows, seeded to look like a real store's operational data. The schema matches the output shape of standard POS, WMS, and HRIS systems.
>
> Connecting to production data is a data engineering task — the agent and tool layers do not change. You point the MCP tools at your actual data sources."

**"How many agents is too many?"**
> "The LangGraph topology handles any number of parallel agents cleanly. The practical limit is the LLM cost and latency budget per run. For most store-level queries, 2-3 specialists are sufficient — the Orchestrator's routing ensures you don't pay for what you don't need.
>
> The Disruption War Room uses 6 agents because a supply chain event genuinely touches six distinct analytical domains simultaneously."
