import asyncio
import json
import logging
import traceback
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import data_store, db, seed
from .config import FRONTEND_DIR, ROOT_DIR, settings
from .agents import store_manager_graph, disruption_graph
from .mcp_tools import get_server as get_mcp_server

logger = logging.getLogger(__name__)


app = FastAPI(title="RCG Multi-Agent Command Center")


@app.on_event("startup")
async def _bootstrap_db():
    if not db.DB_PATH.exists():
        seed.seed_all(rebuild=False)
    else:
        # Ensure schema is up to date for existing DBs
        db.init_schema()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
async def status():
    stats = db.db_stats()
    return {
        "demo_mode": settings.is_demo_mode,
        "model": settings.gemini_model,
        "langsmith_enabled": getattr(settings, "langsmith_active", False),
        "langsmith_project": settings.langsmith_project,
        "input_cost_per_1m": settings.input_cost_per_1m,
        "output_cost_per_1m": settings.output_cost_per_1m,
        "db": {"tables": stats["tables"], "rows": stats["rows"]},
    }


@app.get("/api/db-info")
async def db_info():
    return db.db_stats()


@app.post("/api/db-reseed")
async def db_reseed():
    return seed.seed_all(rebuild=True)


@app.get("/api/mcp/tools")
async def mcp_tools():
    server = get_mcp_server()
    return {
        "name": server.name,
        "version": server.version,
        "tool_count": server.tool_count,
        "tools": server.list_tools(),
    }


@app.get("/api/mcp/history")
async def mcp_history(limit: int = 50):
    server = get_mcp_server()
    return {
        "history": [c.to_event() for c in server.history[-limit:]],
    }


@app.get("/api/dashboard")
async def dashboard():
    return data_store.dashboard_snapshot()


@app.get("/api/scenarios")
async def scenarios():
    return data_store.disruption_scenarios()


@app.get("/api/stores")
async def stores():
    return data_store.stores()


@app.get("/api/analytics")
async def analytics():
    h = data_store.historical()
    return {
        "daily_revenue_90d": h["daily_revenue_90d"],
        "daily_revenue_dates": h["daily_revenue_dates"],
        "categories_30d": h["categories_30d"],
        "category_dates": h["category_dates"],
        "agent_runs_30d": h["agent_runs_30d"],
        "agent_breakdown": h["agent_breakdown"],
        "disruptions_handled_90d": h["disruptions_handled_90d"],
        "db": db.db_stats(),
    }


@app.websocket("/ws/store-manager")
async def ws_store_manager(ws: WebSocket):
    await ws.accept()
    question = "(unknown)"
    try:
        msg = await ws.receive_json()
        question = msg.get("question", "").strip() or "Give me my morning briefing."
        logger.info("[SM] run started | question=%r", question)
        async for event in store_manager_graph.run_streamed(question):
            await ws.send_json(event)
        logger.info("[SM] run complete | question=%r", question)
    except WebSocketDisconnect:
        logger.info("[SM] client disconnected | question=%r", question)
    except Exception as e:
        logger.error("[SM] UNHANDLED EXCEPTION | question=%r\n%s", question, traceback.format_exc())
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@app.websocket("/ws/disruption")
async def ws_disruption(ws: WebSocket):
    await ws.accept()
    scenario_id = "(unknown)"
    try:
        msg = await ws.receive_json()
        scenario_id = msg.get("scenario_id", "SCN-HURRICANE")
        logger.info("[WR] run started | scenario=%r", scenario_id)
        async for event in disruption_graph.run_streamed(scenario_id):
            await ws.send_json(event)
        logger.info("[WR] run complete | scenario=%r", scenario_id)
    except WebSocketDisconnect:
        logger.info("[WR] client disconnected | scenario=%r", scenario_id)
    except Exception as e:
        logger.error("[WR] UNHANDLED EXCEPTION | scenario=%r\n%s", scenario_id, traceback.format_exc())
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


# Markmap walkthrough served from project root
@app.get("/markmap")
async def serve_markmap():
    for name in ("pulse_markmap.html", "PULSE.html"):
        candidate = ROOT_DIR / name
        if candidate.exists():
            return FileResponse(str(candidate))
    return JSONResponse({"error": "markmap file not found at project root"}, status_code=404)


# Static frontend mount (last, so /api/* and /ws/* take precedence)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        target = FRONTEND_DIR / path
        if target.exists() and target.is_file():
            return FileResponse(str(target))
        return FileResponse(str(FRONTEND_DIR / "index.html"))


def run():
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    run()
