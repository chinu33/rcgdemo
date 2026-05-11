"""In-process MCP-style tool server.

Mirrors the Model Context Protocol surface (`list_tools`, `call_tool` with
JSON Schema arguments) without the stdio/SSE transport layer — agents in
this app run in-process so we keep things lightweight while preserving MCP
semantics: tools are discoverable, every call is structured, and every
invocation produces an observable record.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional


@dataclass
class ToolDef:
    name: str
    description: str
    input_schema: dict
    handler: Callable[..., Any]
    category: str = "data"


@dataclass
class ToolCall:
    tool: str
    arguments: dict
    started_at: float
    ended_at: Optional[float] = None
    result: Any = None
    result_preview: str = ""
    error: Optional[str] = None
    caller: str = ""

    @property
    def latency_ms(self) -> int:
        end = self.ended_at if self.ended_at else time.time()
        return int((end - self.started_at) * 1000)

    def to_event(self) -> dict:
        return {
            "type": "mcp_tool_call",
            "tool": self.tool,
            "caller": self.caller,
            "arguments": self.arguments,
            "result_preview": self.result_preview,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "ok": self.error is None,
        }


def _preview(obj: Any, max_chars: int = 220) -> str:
    if obj is None:
        return ""
    try:
        text = json.dumps(obj, default=str)
    except Exception:
        text = str(obj)
    text = text.replace("\n", " ")
    if len(text) > max_chars:
        return text[: max_chars - 1] + "…"
    return text


class MCPServer:
    """Lightweight MCP-compatible tool registry."""

    def __init__(self, name: str = "rcg-mcp-server", version: str = "0.1.0"):
        self.name = name
        self.version = version
        self._tools: dict[str, ToolDef] = {}
        self._history: list[ToolCall] = []

    def register(self, tool: ToolDef) -> None:
        self._tools[tool.name] = tool

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "category": t.category,
            }
            for t in self._tools.values()
        ]

    def get_tool_def(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def as_lc_tools(self, names: list[str]) -> list:
        """Return LangChain StructuredTool objects for use with llm.bind_tools().

        The returned tools have no-op handlers — execution routes through
        call_tool() so every invocation is logged by the MCP server.
        """
        from langchain_core.tools import StructuredTool
        from pydantic import create_model
        from typing import Optional as Opt

        lc_tools = []
        for name in names:
            td = self._tools.get(name)
            if td is None:
                continue

            # Build a Pydantic args model from the JSON Schema properties
            fields: dict = {}
            for fname, fschema in td.input_schema.get("properties", {}).items():
                py_type = {
                    "string": str, "integer": int,
                    "number": float, "boolean": bool,
                }.get(fschema.get("type", "string"), str)
                fields[fname] = (Opt[py_type], None)

            ArgsModel = create_model(f"_{name}_Args", **fields)

            # No-op: execution goes through call_tool(), not through LangChain
            def _noop(**kwargs): return {}

            lc_tools.append(StructuredTool.from_function(
                func=_noop,
                name=td.name,
                description=td.description,
                args_schema=ArgsModel,
            ))
        return lc_tools

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    @property
    def history(self) -> list[ToolCall]:
        return list(self._history)

    async def call_tool(
        self,
        name: str,
        arguments: Optional[dict] = None,
        caller: str = "",
        observer: Optional[Callable[[ToolCall], Awaitable[None]]] = None,
    ) -> ToolCall:
        args = arguments or {}
        call = ToolCall(tool=name, arguments=args, started_at=time.time(), caller=caller)
        tool = self._tools.get(name)
        if tool is None:
            call.ended_at = time.time()
            call.error = f"Unknown tool: {name}"
            self._history.append(call)
            if observer:
                await observer(call)
            return call

        # Strip args the handler doesn't declare — enforces the schema contract
        # and prevents LLM-hallucinated extra params from causing TypeErrors.
        valid_keys = set(tool.input_schema.get("properties", {}).keys())
        args = {k: v for k, v in args.items() if k in valid_keys}

        try:
            handler = tool.handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**args)
            else:
                # Run sync handlers in a thread pool to keep the loop free
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: handler(**args)
                )
            call.result = result
            call.result_preview = _preview(result)
        except Exception as e:
            call.error = f"{type(e).__name__}: {e}"
        finally:
            call.ended_at = time.time()
            self._history.append(call)
            if len(self._history) > 500:
                self._history = self._history[-500:]
            if observer:
                await observer(call)
        return call


_default_server: Optional[MCPServer] = None


def get_server() -> MCPServer:
    """Return the singleton MCP server, building it on first access."""
    global _default_server
    if _default_server is None:
        from .tools import build_default_server
        _default_server = build_default_server()
    return _default_server
