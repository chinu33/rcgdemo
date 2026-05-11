"""Disruption War Room — multi-agent LangGraph workflow with MCP-backed context."""
import asyncio
import json
import re
from typing import AsyncIterator, TypedDict

from langgraph.graph import StateGraph, END

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def deco(fn): return fn
        return deco if args and callable(args[0]) is False else (args[0] if args else deco)

from .. import data_store
from ..config import settings
from ..llm import ainvoke, ainvoke_stream, get_llm
from ..mcp_tools import get_server
from ..telemetry import AgentTrace, RunMetrics, estimate_tokens
from . import demo_responses, prompts


class WRState(TypedDict, total=False):
    scenario_id: str
    raw_event: str
    detection: str
    supplier_brief: str
    rebalance_brief: str
    impact_brief: str
    comms_brief: str
    final_brief: str


AGENT_LABELS = {
    "detector": "Disruption Detector",
    "supplier": "Supplier Researcher",
    "rebalancer": "Store Inventory Analyst",
    "impact": "Store Impact Analyst",
    "comms": "Comms Specialist",
    "synthesizer": "Response Commander",
}

# Agents that discover and call MCP tools autonomously.
# comms and synthesizer work purely from prior agent outputs — no data tools needed.
_TOOL_USING_AGENTS = {"detector", "supplier", "rebalancer", "impact"}

# Demo-mode: one representative tool per tool-using agent for MCP monitor telemetry.
_DEMO_TOOL = {
    "detector":   "get_disruption_scenarios",
    "supplier":   "get_supplier_directory",
    "rebalancer": "get_inventory_health",
    "impact":     "get_store_directory",
}


SYSTEM_MAP = {
    "detector":    prompts.DISRUPTION_DETECTOR_SYSTEM,
    "supplier":    prompts.SUPPLIER_RESEARCHER_SYSTEM,
    "rebalancer":  prompts.REBALANCER_SYSTEM,
    "impact":      prompts.IMPACT_MODELER_SYSTEM,
    "comms":       prompts.COMMS_DRAFTER_SYSTEM,
    "synthesizer": prompts.DISRUPTION_SYNTHESIZER_SYSTEM,
}


def _scenario(scenario_id: str) -> dict:
    scenarios = data_store.disruption_scenarios()["scenarios"]
    return next((s for s in scenarios if s["id"] == scenario_id), scenarios[0])


async def _run_synthesizer_stream(scenario: dict, prior: dict):
    """Streams the final commander brief."""
    if settings.is_demo_mode:
        text = demo_responses.DISRUPTION["synthesis"]
        for tok in re.findall(r"\S+\s*", text):
            yield {"type": "chunk", "text": tok}
            await asyncio.sleep(0.022)
        yield {
            "type": "usage",
            "input": estimate_tokens(json.dumps(scenario)),
            "output": estimate_tokens(text),
            "full": text,
        }
        return

    payload = {"scenario": scenario, "prior_outputs": prior}
    async for ev in ainvoke_stream(json.dumps(payload, indent=2), system=prompts.DISRUPTION_SYNTHESIZER_SYSTEM):
        yield ev


@traceable(run_type="chain", name="Disruption Agent")
async def _run_node(agent_key: str, scenario: dict, prior: dict, on_tool_call=None) -> tuple[str, int, int]:
    """True agentic disruption node.

    Tool-using agents (detector, supplier, rebalancer, impact) discover ALL MCP tools
    at runtime and let the LLM decide which to call based on the disruption context.
    Non-tool agents (comms, synthesizer) work purely from prior outputs.
    """
    server = get_server()

    async def _observer(call):
        if on_tool_call:
            await on_tool_call(call)

    # ── Demo mode ────────────────────────────────────────────────────────────────
    if settings.is_demo_mode:
        if agent_key in _TOOL_USING_AGENTS:
            await server.call_tool(_DEMO_TOOL[agent_key], {}, caller=agent_key, observer=_observer)
        await asyncio.sleep(0.9 + 0.4 * (list(AGENT_LABELS).index(agent_key) % 3))
        text = demo_responses.DISRUPTION[agent_key]
        return text, estimate_tokens(json.dumps(scenario)), estimate_tokens(text)

    system = SYSTEM_MAP[agent_key]

    # ── Non-tool agents: single LLM call over prior outputs ──────────────────────
    if agent_key not in _TOOL_USING_AGENTS:
        payload = {"scenario": scenario, "prior_outputs": prior}
        return await ainvoke(json.dumps(payload, indent=2), system=system)

    # ── Step 1: Discover ALL MCP tools and let the LLM decide which to call ──────
    from langchain_core.messages import HumanMessage, SystemMessage

    all_tool_names = [t["name"] for t in server.list_tools()]
    lc_tools       = server.as_lc_tools(all_tool_names)
    llm_with_tools = get_llm().bind_tools(lc_tools)

    context_hint = json.dumps({"scenario": scenario, "prior_outputs": prior}, indent=2)
    selection = await llm_with_tools.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=(
            f"Disruption context:\n{context_hint}\n\n"
            f"You have access to {len(lc_tools)} MCP tools. "
            f"Call whichever you need to complete your analysis."
        )),
    ])

    sel_meta = getattr(selection, "usage_metadata", None) or {}
    in_tok  = int(sel_meta.get("input_tokens",  0) or 0)
    out_tok = int(sel_meta.get("output_tokens", 0) or 0)

    # ── Step 2: Execute chosen tools through MCP server ──────────────────────────
    tool_calls   = getattr(selection, "tool_calls", []) or []
    tool_results = []

    if tool_calls:
        for tc in tool_calls:
            mcp_call = await server.call_tool(
                tc["name"], tc.get("args", {}), caller=agent_key, observer=_observer
            )
            tool_results.append({
                "tool":   tc["name"],
                "result": mcp_call.result if not mcp_call.error else {"error": mcp_call.error},
                "ok":     mcp_call.error is None,
            })
    else:
        fallback = _DEMO_TOOL[agent_key]
        mcp_call = await server.call_tool(fallback, {}, caller=agent_key, observer=_observer)
        tool_results.append({
            "tool":   fallback,
            "result": mcp_call.result if not mcp_call.error else {"error": mcp_call.error},
            "ok":     mcp_call.error is None,
        })

    # ── Step 3: LLM produces output from scenario + prior + tool results ─────────
    tools_called = ", ".join(r["tool"] for r in tool_results)
    brief_prompt = json.dumps({
        "scenario":      scenario,
        "prior_outputs": prior,
        "tools_called":  tools_called,
        "tool_results":  tool_results,
    }, indent=2)
    text, in_tok_2, out_tok_2 = await ainvoke(brief_prompt, system=system)
    return text, in_tok + in_tok_2, out_tok + out_tok_2


def build_graph():
    g = StateGraph(WRState)

    def make_node(name: str, prior_keys: list = None):
        async def node(state):
            sc = _scenario(state["scenario_id"])
            prior = {k: state.get(k, "") for k in (prior_keys or [])}
            text, _, _ = await _run_node(name, sc, prior)
            return {f"{'detection' if name == 'detector' else name + '_brief' if name != 'synthesizer' else 'final_brief'}": text}
        return node

    async def detector_node(state):
        sc = _scenario(state["scenario_id"])
        text, _, _ = await _run_node("detector", sc, {})
        return {"detection": text}

    async def supplier_node(state):
        sc = _scenario(state["scenario_id"])
        text, _, _ = await _run_node("supplier", sc, {"detection": state.get("detection", "")})
        return {"supplier_brief": text}

    async def rebalancer_node(state):
        sc = _scenario(state["scenario_id"])
        text, _, _ = await _run_node("rebalancer", sc, {"detection": state.get("detection", "")})
        return {"rebalance_brief": text}

    async def impact_node(state):
        sc = _scenario(state["scenario_id"])
        text, _, _ = await _run_node("impact", sc, {"detection": state.get("detection", "")})
        return {"impact_brief": text}

    async def comms_node(state):
        sc = _scenario(state["scenario_id"])
        text, _, _ = await _run_node("comms", sc, state)
        return {"comms_brief": text}

    async def synth_node(state):
        sc = _scenario(state["scenario_id"])
        text, _, _ = await _run_node("synthesizer", sc, state)
        return {"final_brief": text}

    for name, fn in [
        ("detector", detector_node),
        ("supplier", supplier_node),
        ("rebalancer", rebalancer_node),
        ("impact", impact_node),
        ("comms", comms_node),
        ("synthesizer", synth_node),
    ]:
        g.add_node(name, fn)

    g.set_entry_point("detector")
    g.add_edge("detector", "supplier")
    g.add_edge("detector", "rebalancer")
    g.add_edge("detector", "impact")
    g.add_edge("supplier", "comms")
    g.add_edge("rebalancer", "comms")
    g.add_edge("impact", "comms")
    g.add_edge("comms", "synthesizer")
    g.add_edge("synthesizer", END)

    return g.compile()


GRAPH = None


def graph():
    global GRAPH
    if GRAPH is None:
        GRAPH = build_graph()
    return GRAPH


async def run_streamed(scenario_id: str) -> AsyncIterator[dict]:
    metrics = RunMetrics()
    sc = _scenario(scenario_id)
    yield {"type": "run_start", "workflow": "disruption", "scenario": sc}

    tool_event_queue: asyncio.Queue = asyncio.Queue()

    async def emit_tool_call(call):
        await tool_event_queue.put(call.to_event())

    async def drain_tool_events():
        items = []
        while not tool_event_queue.empty():
            items.append(tool_event_queue.get_nowait())
        return items

    # Step 1: Detector
    t = AgentTrace(agent="detector")
    yield {"type": "agent_start", **t.to_event(), "label": AGENT_LABELS["detector"]}
    detection, in_tok, out_tok = await _run_node("detector", sc, {}, on_tool_call=emit_tool_call)
    for ev in await drain_tool_events():
        yield ev
    t.finish(in_tok, out_tok)
    metrics.add(t)
    yield {"type": "agent_complete", **t.to_event(), "label": AGENT_LABELS["detector"], "output": {"brief": detection}}

    # Step 2: Parallel — supplier, rebalancer, impact (each fires its own MCP calls)
    parallel = ["supplier", "rebalancer", "impact"]
    yield {"type": "fanout_start", "agents": parallel}
    starts = []
    for a in parallel:
        st = AgentTrace(agent=a)
        starts.append(st)
        yield {"type": "agent_start", **st.to_event(), "label": AGENT_LABELS[a]}

    prior = {"detection": detection}
    tasks = [
        asyncio.create_task(_run_node(a, sc, prior, on_tool_call=emit_tool_call))
        for a in parallel
    ]
    pending = set(tasks)
    finish_index = {id(task): (a, st) for task, a, st in zip(tasks, parallel, starts)}
    outputs: dict = {}

    while pending or not tool_event_queue.empty():
        for ev in await drain_tool_events():
            yield ev
        if not pending:
            break
        done, pending = await asyncio.wait(
            pending, timeout=0.05, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            a, st = finish_index[id(task)]
            try:
                text, in_tok, out_tok = task.result()
                st.finish(in_tok, out_tok)
                metrics.add(st)
                outputs[a] = text
                yield {"type": "agent_complete", **st.to_event(), "label": AGENT_LABELS[a], "output": {"brief": text}}
            except Exception as exc:
                st.finish(0, 0)
                metrics.add(st)
                yield {"type": "agent_error", "agent": a, "label": AGENT_LABELS[a], "error": str(exc)}

    for ev in await drain_tool_events():
        yield ev

    # Step 3: Comms
    c = AgentTrace(agent="comms")
    yield {"type": "agent_start", **c.to_event(), "label": AGENT_LABELS["comms"]}
    comms, in_tok, out_tok = await _run_node("comms", sc, {"detection": detection, **outputs}, on_tool_call=emit_tool_call)
    for ev in await drain_tool_events():
        yield ev
    c.finish(in_tok, out_tok)
    metrics.add(c)
    yield {"type": "agent_complete", **c.to_event(), "label": AGENT_LABELS["comms"], "output": {"brief": comms}}

    # Step 4: Synthesizer (streaming)
    s = AgentTrace(agent="synthesizer")
    yield {"type": "agent_start", **s.to_event(), "label": AGENT_LABELS["synthesizer"]}
    final = ""
    in_tok = out_tok = 0
    async for ev in _run_synthesizer_stream(sc, {"detection": detection, **outputs, "comms": comms}):
        if ev["type"] == "chunk":
            final += ev["text"]
            yield {"type": "token", "agent": "synthesizer", "text": ev["text"]}
        elif ev["type"] == "usage":
            in_tok = ev["input"]
            out_tok = ev["output"]
            final = ev.get("full", final) or final
    s.finish(in_tok, out_tok)
    metrics.add(s)
    yield {"type": "agent_complete", **s.to_event(), "label": AGENT_LABELS["synthesizer"], "output": {"brief": final}}

    yield {
        "type": "run_complete",
        "scenario": sc,
        "detection": detection,
        "supplier": outputs.get("supplier", ""),
        "rebalance": outputs.get("rebalancer", ""),
        "impact": outputs.get("impact", ""),
        "comms": comms,
        "final": final,
        "metrics": metrics.to_dict(),
    }
