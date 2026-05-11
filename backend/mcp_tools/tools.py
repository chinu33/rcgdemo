"""Tool implementations exposed by the MCP server.

Each tool is a thin, JSON-schema-described wrapper over the SQLite-backed
data layer. Agents call these instead of touching `data_store` directly,
giving us a real MCP-style tool boundary the UI can observe.
"""
from __future__ import annotations

from typing import Optional

from .. import data_store
from .server import MCPServer, ToolDef


# --- Tool handlers -----------------------------------------------------------

def _get_sales_snapshot(store_id: Optional[str] = None, category: Optional[str] = None) -> dict:
    payload = data_store.sales()
    if category:
        cat = category.lower()
        payload = dict(payload)
        payload["by_category"] = [
            c for c in payload.get("by_category", [])
            if c.get("category", "").lower() == cat
        ]
        payload["top_movers_up"] = [
            m for m in payload.get("top_movers_up", [])
            if m.get("category", "").lower() == cat
        ]
        payload["top_movers_down"] = [
            m for m in payload.get("top_movers_down", [])
            if m.get("category", "").lower() == cat
        ]
    return payload


def _get_inventory_health(store_id: Optional[str] = None, category: Optional[str] = None) -> dict:
    payload = data_store.inventory()
    if category:
        cat = category.lower()
        payload = dict(payload)
        payload["categories"] = [
            c for c in payload.get("categories", [])
            if c.get("category", "").lower() == cat
        ]
        payload["critical_skus"] = [
            s for s in payload.get("critical_skus", [])
            if s.get("category", "").lower() == cat
        ]
    return payload


def _get_labor_status(store_id: Optional[str] = None) -> dict:
    return data_store.labor()


def _get_promotions_and_competitive(store_id: Optional[str] = None) -> dict:
    return data_store.promotions()


def _get_customer_voice(store_id: Optional[str] = None, category: Optional[str] = None) -> dict:
    payload = data_store.reviews()
    if category:
        cat = category.lower()
        payload = dict(payload)
        payload["themes"] = [
            t for t in payload.get("themes", [])
            if cat in t.get("theme", "").lower() or cat in t.get("category", "").lower()
        ]
        payload["recent"] = [
            r for r in payload.get("recent", [])
            if cat in r.get("category", "").lower() or cat in r.get("text", "").lower()
        ]
    return payload


def _get_store_directory() -> dict:
    return data_store.stores()


def _get_disruption_scenarios() -> dict:
    return data_store.disruption_scenarios()


def _get_supplier_directory(category: Optional[str] = None) -> dict:
    payload = data_store.suppliers()
    if category:
        cat = category.lower()
        payload = {
            "suppliers": [
                s for s in payload["suppliers"]
                if any(c.lower() == cat for c in s.get("categories", []))
            ]
        }
    return payload


def _get_historical_analytics() -> dict:
    return data_store.historical()


def _get_dashboard_snapshot() -> dict:
    return data_store.dashboard_snapshot()


# --- Schemas -----------------------------------------------------------------

_STORE_ID_SCHEMA = {
    "type": "object",
    "properties": {
        "store_id": {
            "type": "string",
            "description": "Store identifier, e.g. ST-014. Defaults to the active store.",
        }
    },
    "required": [],
}

_STORE_CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {
        "store_id": {
            "type": "string",
            "description": "Store identifier, e.g. ST-014. Defaults to the active store.",
        },
        "category": {
            "type": "string",
            "description": "Filter results to a specific category, e.g. 'Dairy', 'Produce', 'Beverages'.",
        },
    },
    "required": [],
}


def build_default_server() -> MCPServer:
    s = MCPServer(name="rcg-retail-mcp", version="0.1.0")

    s.register(ToolDef(
        name="get_sales_snapshot",
        description="Today's sales: revenue vs forecast, transactions, traffic, hourly breakdown, category performance, top movers. Optional category filter narrows results to one category, e.g. 'Dairy'.",
        input_schema=_STORE_CATEGORY_SCHEMA,
        handler=_get_sales_snapshot,
        category="sales",
    ))
    s.register(ToolDef(
        name="get_inventory_health",
        description="Inventory by category: on-hand units, days of supply, stockout SKUs, critical replenishment items. Optional category filter, e.g. 'Dairy'.",
        input_schema=_STORE_CATEGORY_SCHEMA,
        handler=_get_inventory_health,
        category="inventory",
    ))
    s.register(ToolDef(
        name="get_labor_status",
        description="Today's labor: scheduled hours, callouts, department-level coverage gaps, labor cost vs target.",
        input_schema=_STORE_ID_SCHEMA,
        handler=_get_labor_status,
        category="labor",
    ))
    s.register(ToolDef(
        name="get_promotions_and_competitive",
        description="Active promotions with redemptions and lift, plus nearby competitor promo intel.",
        input_schema=_STORE_ID_SCHEMA,
        handler=_get_promotions_and_competitive,
        category="merchandising",
    ))
    s.register(ToolDef(
        name="get_customer_voice",
        description="Customer review summary, complaint themes, and recent verbatim feedback. Optional category filter to focus on a specific department, e.g. 'Dairy'.",
        input_schema=_STORE_CATEGORY_SCHEMA,
        handler=_get_customer_voice,
        category="cx",
    ))
    s.register(ToolDef(
        name="get_store_directory",
        description="List of all stores with location, format, square footage, and manager.",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=_get_store_directory,
        category="reference",
    ))
    s.register(ToolDef(
        name="get_supplier_directory",
        description="Supplier catalogue with lead times, reliability, alternates, and risk flags. Optional category filter.",
        input_schema={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category, e.g. 'Dairy'"}
            },
            "required": [],
        },
        handler=_get_supplier_directory,
        category="supply_chain",
    ))
    s.register(ToolDef(
        name="get_disruption_scenarios",
        description="Library of pre-modeled disruption scenarios (weather, logistics, supplier, cyber).",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=_get_disruption_scenarios,
        category="risk",
    ))
    s.register(ToolDef(
        name="get_historical_analytics",
        description="90-day daily revenue, 30-day category trajectories, agent activity, and disruption response history.",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=_get_historical_analytics,
        category="analytics",
    ))
    s.register(ToolDef(
        name="get_dashboard_snapshot",
        description="Composite snapshot combining KPIs, alerts, top movers, and review highlights for the active store.",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=_get_dashboard_snapshot,
        category="overview",
    ))

    return s
