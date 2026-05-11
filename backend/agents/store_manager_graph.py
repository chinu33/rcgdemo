"""Store Manager Command Center — multi-agent LangGraph workflow.

Architecture:
    Orchestrator (intent routing)
         ↓
    Sales | Inventory | Labor | Promo | Reviews   ← each fetches data
         ↓                                          via MCP tool calls
    Chief Synthesizer
"""
import asyncio
import json
import logging
import traceback
import re
from typing import AsyncIterator, Optional, TypedDict

from langgraph.graph import StateGraph, END

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def deco(fn): return fn
        return deco if args and callable(args[0]) is False else (args[0] if args else deco)

from ..config import settings
from ..llm import ainvoke, ainvoke_stream, get_llm
from ..mcp_tools import get_server
from ..telemetry import AgentTrace, RunMetrics, estimate_tokens
from . import demo_responses, prompts

logger = logging.getLogger(__name__)


class SMState(TypedDict, total=False):
    question: str
    selected_agents: list
    sales_brief: str
    inventory_brief: str
    labor_brief: str
    promo_brief: str
    reviews_brief: str
    final_answer: str


AGENT_LABELS = {
    "orchestrator": "Orchestrator",
    "sales": "Sales Performance Agent",
    "inventory": "Inventory & Stockout Agent",
    "labor": "Labor & Scheduling Agent",
    "promo": "Promotion & Competitive Intel Agent",
    "reviews": "Customer Voice Agent",
    "synthesizer": "Chief Synthesizer",
}

# Demo-mode: one representative tool per specialist for MCP monitor telemetry only.
_DEMO_TOOL = {
    "sales":     "get_sales_snapshot",
    "inventory": "get_inventory_health",
    "labor":     "get_labor_status",
    "promo":     "get_promotions_and_competitive",
    "reviews":   "get_customer_voice",
}



def _system_for(agent: str) -> str:
    return {
        "sales":     prompts.SALES_SYSTEM,
        "inventory": prompts.INVENTORY_SYSTEM,
        "labor":     prompts.LABOR_SYSTEM,
        "promo":     prompts.PROMO_SYSTEM,
        "reviews":   prompts.REVIEWS_SYSTEM,
    }[agent]


_VALID_AGENTS = {"sales", "inventory", "labor", "promo", "reviews"}

# Selective demo-mode routing — mirrors what the LLM would decide
_DEMO_ROUTES = [
    (["morning briefing", "full brief"],                          ["sales", "inventory", "labor", "promo", "reviews"]),
    (["dairy", "produce", "bakery", "stockout", "out of stock", "categor", "at risk"],  ["sales", "inventory"]),
    (["promo", "competit", "discount", "markdown"],               ["promo", "sales"]),
    (["staff", "labor", "scheduling", "callout", "coverage", "covered", "shift", "headcount"],  ["labor"]),
    (["review", "customer", "complaint", "sentiment", "nps"],     ["reviews", "sales"]),
    (["inventory", "stock", "replenish", "supply"],               ["inventory"]),
    (["sales", "revenue", "category", "trend"],                   ["sales"]),
]


def _demo_route(question: str) -> list:
    q = question.lower()
    for keywords, agents in _DEMO_ROUTES:
        if any(k in q for k in keywords):
            return agents
    return ["sales", "inventory", "labor", "promo", "reviews"]


def _extract_agents(text: str) -> list:
    """Extract the first JSON array from LLM output, however it is formatted."""
    import re
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if not match:
        return []
    try:
        candidates = json.loads(match.group())
        if isinstance(candidates, list):
            return [a for a in candidates if a in _VALID_AGENTS]
    except Exception:
        pass
    return []


@traceable(run_type="chain", name="Orchestrator")
async def _route(question: str) -> list:
    """LLM decides the minimum set of specialists needed to answer the question."""
    logger.info("[Orchestrator] routing | question=%r", question)
    if settings.is_demo_mode:
        await asyncio.sleep(0.4)
        result = _demo_route(question)
        logger.info("[Orchestrator] demo route → %s", result)
        return result

    try:
        text, _, _ = await ainvoke(
            f"Manager question: {question}\n\nReturn the JSON array.",
            system=prompts.ORCHESTRATOR_SYSTEM,
        )
        logger.debug("[Orchestrator] raw LLM response: %r", text[:300])
        agents = _extract_agents(text)
        if agents:
            logger.info("[Orchestrator] selected agents=%s", agents)
            return agents
        logger.warning("[Orchestrator] JSON parse failed, raw=%r — falling back to keyword route", text[:200])
    except Exception:
        logger.exception("[Orchestrator] LLM call failed — falling back to keyword route")

    fallback = _demo_route(question)
    logger.info("[Orchestrator] fallback route → %s", fallback)
    return fallback


@traceable(run_type="chain", name="Specialist Agent")
async def _run_specialist(agent: str, question: str, on_tool_call=None) -> tuple[str, int, int]:
    """True agentic specialist.

    Discovers ALL tools registered on the MCP server at runtime via list_tools(),
    binds them to the LLM, and lets the model decide autonomously which to call
    based on its role and the manager's question.

    Two LLM calls:
      1. bind_tools  — model reads every tool schema, selects and calls what it needs
      2. briefing    — model reasons over results and produces its domain output
    """
    server = get_server()

    async def _observer(call):
        if on_tool_call:
            await on_tool_call(call)

    logger.info("[%s] specialist started | question=%r", agent, question[:80])

    # ── Demo mode: one representative MCP call for monitor telemetry ─────────────
    if settings.is_demo_mode:
        demo_call = await server.call_tool(_DEMO_TOOL[agent], {}, caller=agent, observer=_observer)
        payload = demo_call.result if not demo_call.error else {"error": demo_call.error}
        await asyncio.sleep(0.6 + (hash(agent) % 5) * 0.08)
        text = demo_responses.STORE_MANAGER[agent]
        logger.info("[%s] demo mode complete", agent)
        return text, estimate_tokens(json.dumps(payload)), estimate_tokens(text)

    # ── Step 1: Discover ALL MCP tools; LLM decides which to call ────────────────
    from langchain_core.messages import HumanMessage, SystemMessage

    all_tool_names = [t["name"] for t in server.list_tools()]
    logger.info("[%s] discovered %d MCP tools: %s", agent, len(all_tool_names), all_tool_names)
    lc_tools       = server.as_lc_tools(all_tool_names)
    llm_with_tools = get_llm().bind_tools(lc_tools)

    logger.info("[%s] calling LLM for tool selection (bind_tools)", agent)
    try:
        selection = await llm_with_tools.ainvoke([
            SystemMessage(content=_system_for(agent)),
            HumanMessage(content=(
                f"Manager's question: {question}\n\n"
                f"You have {len(lc_tools)} MCP tools available — call only the ones "
                f"your role requires. Other specialists are handling their own domains."
            )),
        ])
    except Exception:
        logger.exception("[%s] bind_tools LLM call FAILED", agent)
        raise

    sel_meta = getattr(selection, "usage_metadata", None) or {}
    in_tok  = int(sel_meta.get("input_tokens",  0) or 0)
    out_tok = int(sel_meta.get("output_tokens", 0) or 0)

    # ── Step 2: Execute chosen tools through the MCP server ──────────────────────
    tool_calls   = getattr(selection, "tool_calls", []) or []
    logger.info("[%s] LLM chose %d tool call(s): %s", agent, len(tool_calls),
                [tc["name"] for tc in tool_calls])
    tool_results = []

    if tool_calls:
        for tc in tool_calls:
            logger.info("[%s] calling MCP tool %r with args %s", agent, tc["name"], tc.get("args", {}))
            try:
                mcp_call = await server.call_tool(
                    tc["name"], tc.get("args", {}), caller=agent, observer=_observer
                )
            except Exception:
                logger.exception("[%s] MCP tool call %r FAILED", agent, tc["name"])
                raise
            if mcp_call.error:
                logger.warning("[%s] MCP tool %r returned error: %s", agent, tc["name"], mcp_call.error)
            else:
                logger.info("[%s] MCP tool %r OK (%dms)", agent, tc["name"], mcp_call.latency_ms)
            tool_results.append({
                "tool":   tc["name"],
                "result": mcp_call.result if not mcp_call.error else {"error": mcp_call.error},
                "ok":     mcp_call.error is None,
            })
    else:
        fallback = _DEMO_TOOL[agent]
        logger.warning("[%s] LLM chose no tools — falling back to %r", agent, fallback)
        mcp_call = await server.call_tool(fallback, {}, caller=agent, observer=_observer)
        tool_results.append({
            "tool":   fallback,
            "result": mcp_call.result if not mcp_call.error else {"error": mcp_call.error},
            "ok":     mcp_call.error is None,
        })

    # ── Step 3: LLM produces its briefing from the tool results ──────────────────
    tools_called = ", ".join(r["tool"] for r in tool_results)
    logger.info("[%s] calling LLM for briefing | tools_used=%s", agent, tools_called)
    brief_prompt = (
        f"Manager's question: {question}\n\n"
        f"Tools called: {tools_called}\n\n"
        f"Results:\n{json.dumps(tool_results, indent=2)}\n\n"
        f"Produce your specialist briefing."
    )
    try:
        text, in_tok_2, out_tok_2 = await ainvoke(brief_prompt, system=_system_for(agent))
    except Exception:
        logger.exception("[%s] briefing LLM call FAILED", agent)
        raise
    logger.info("[%s] briefing complete | in_tok=%d out_tok=%d", agent, in_tok + in_tok_2, out_tok + out_tok_2)
    return text, in_tok + in_tok_2, out_tok + out_tok_2


async def _synthesize_stream(question: str, briefs: dict):
    """Async generator: yields {type:'chunk',text} chunks then {type:'usage',input,output,full}."""
    logger.info("[Synthesizer] starting | briefs_received=%s", list(briefs.keys()))
    if settings.is_demo_mode:
        text = demo_responses.STORE_MANAGER["synthesis"]
        for tok in re.findall(r"\S+\s*", text):
            yield {"type": "chunk", "text": tok}
            await asyncio.sleep(0.022)
        yield {
            "type": "usage",
            "input": estimate_tokens(json.dumps(briefs)),
            "output": estimate_tokens(text),
            "full": text,
        }
        logger.info("[Synthesizer] demo mode complete")
        return

    prompt = (
        f"Manager's question: {question}\n\n"
        f"Specialist briefings:\n{json.dumps(briefs, indent=2)}\n\n"
        f"Produce the final briefing."
    )
    logger.info("[Synthesizer] calling LLM (streaming) | prompt_len=%d chars", len(prompt))
    chunk_count = 0
    try:
        async for ev in ainvoke_stream(prompt, system=prompts.SYNTHESIZER_SYSTEM):
            if ev["type"] == "chunk":
                chunk_count += 1
            elif ev["type"] == "usage":
                logger.info("[Synthesizer] stream complete | chunks=%d in_tok=%d out_tok=%d",
                            chunk_count, ev.get("input", 0), ev.get("output", 0))
            yield ev
    except Exception:
        logger.exception("[Synthesizer] streaming LLM call FAILED after %d chunks", chunk_count)
        raise


def build_graph():
    g = StateGraph(SMState)

    async def orchestrator_node(state: SMState) -> SMState:
        agents = await _route(state["question"])
        return {"selected_agents": agents}

    def make_specialist_node(name: str):
        async def node(state: SMState) -> SMState:
            if name not in state.get("selected_agents", []):
                return {}
            text, _, _ = await _run_specialist(name, state["question"])
            return {f"{name}_brief": text}
        return node

    async def synth_node(state: SMState) -> SMState:
        briefs = {k: state.get(f"{k}_brief", "") for k in _VALID_AGENTS}
        briefs = {k: v for k, v in briefs.items() if v}
        full = ""
        async for ev in _synthesize_stream(state["question"], briefs):
            if ev["type"] == "chunk":
                full += ev["text"]
            elif ev["type"] == "usage":
                full = ev.get("full", full) or full
        return {"final_answer": full}

    g.add_node("orchestrator", orchestrator_node)
    for name in _VALID_AGENTS:
        g.add_node(name, make_specialist_node(name))
    g.add_node("synthesizer", synth_node)

    g.set_entry_point("orchestrator")
    for name in _VALID_AGENTS:
        g.add_edge("orchestrator", name)
        g.add_edge(name, "synthesizer")
    g.add_edge("synthesizer", END)

    return g.compile()


GRAPH = None


def graph():
    global GRAPH
    if GRAPH is None:
        GRAPH = build_graph()
    return GRAPH


async def run_streamed(question: str) -> AsyncIterator[dict]:
    """Run the workflow, yielding telemetry events (agents + MCP tool calls) for the UI."""
    metrics = RunMetrics()
    yield {"type": "run_start", "workflow": "store_manager", "question": question}

    # Step 1: Orchestrator
    t = AgentTrace(agent="orchestrator")
    yield {"type": "agent_start", **t.to_event(), "label": AGENT_LABELS["orchestrator"]}
    selected = await _route(question)
    t.finish(estimate_tokens(question), estimate_tokens(json.dumps(selected)),
             note=f"Selected: {', '.join(selected)}")
    metrics.add(t)
    yield {"type": "agent_complete", **t.to_event(), "label": AGENT_LABELS["orchestrator"], "output": {"selected": selected}}

    # Step 2: Specialists in parallel — each fires a real MCP tool call we forward to the UI
    yield {"type": "fanout_start", "agents": selected}

    tool_event_queue: asyncio.Queue = asyncio.Queue()

    async def emit_tool_call(call):
        await tool_event_queue.put(call.to_event())

    started = []
    for a in selected:
        st = AgentTrace(agent=a)
        started.append(st)
        yield {"type": "agent_start", **st.to_event(), "label": AGENT_LABELS[a]}

    tasks = [
        asyncio.create_task(_run_specialist(a, question, on_tool_call=emit_tool_call))
        for a in selected
    ]
    pending_tasks = set(tasks)
    briefs = {}
    finish_index = {id(t): (a, st) for t, a, st in zip(tasks, selected, started)}

    while pending_tasks or not tool_event_queue.empty():
        # Drain any tool events that arrived
        while not tool_event_queue.empty():
            yield tool_event_queue.get_nowait()

        if not pending_tasks:
            break

        done, pending_tasks = await asyncio.wait(
            pending_tasks, timeout=0.05, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            a, st = finish_index[id(task)]
            try:
                text, in_tok, out_tok = task.result()
                st.finish(in_tok, out_tok)
                metrics.add(st)
                briefs[a] = text
                yield {
                    "type": "agent_complete",
                    **st.to_event(),
                    "label": AGENT_LABELS[a],
                    "output": {"brief": text},
                }
            except Exception as exc:
                logger.error("[%s] specialist task FAILED\n%s", a, traceback.format_exc())
                st.finish(0, 0)
                metrics.add(st)
                yield {
                    "type": "agent_error",
                    "agent": a,
                    "label": AGENT_LABELS[a],
                    "error": str(exc),
                }

    logger.info("[run_streamed] all specialists done | briefs_collected=%s", list(briefs.keys()))

    # Final drain in case tool events landed after the last task finished
    while not tool_event_queue.empty():
        yield tool_event_queue.get_nowait()

    # Step 3: Synthesize (streaming)
    logger.info("[run_streamed] starting synthesizer")
    s = AgentTrace(agent="synthesizer")
    yield {"type": "agent_start", **s.to_event(), "label": AGENT_LABELS["synthesizer"]}
    final = ""
    in_tok = out_tok = 0
    async for ev in _synthesize_stream(question, briefs):
        if ev["type"] == "chunk":
            final += ev["text"]
            yield {"type": "token", "agent": "synthesizer", "text": ev["text"]}
        elif ev["type"] == "usage":
            in_tok = ev["input"]
            out_tok = ev["output"]
            final = ev.get("full", final) or final
    s.finish(in_tok, out_tok)
    metrics.add(s)
    yield {"type": "agent_complete", **s.to_event(), "label": AGENT_LABELS["synthesizer"], "output": {"answer": final}}

    yield {
        "type": "run_complete",
        "answer": final,
        "briefs": briefs,
        "selected_agents": selected,
        "metrics": metrics.to_dict(),
    }
