"""Seed the SQLite database from JSON snapshots + procedurally-generated timeseries."""
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

from .config import SEED_DIR, DB_PATH
from . import db as dbm


RNG = random.Random(2026_05_06)


def _load_seed(name: str) -> dict:
    with open(SEED_DIR / name) as f:
        return json.load(f)


def _gen_daily_revenue(days: int, store_id: str) -> list[tuple[str, str, float]]:
    """Realistic 90-day revenue: weekly seasonality, slight growth, recent dip story."""
    today = datetime(2026, 5, 6)
    rows = []
    base_weekday = 400_000
    base_weekend = 510_000
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        weekday = d.weekday()  # 0=Mon, 6=Sun
        is_weekend = weekday >= 5
        base = base_weekend if is_weekend else base_weekday
        growth = 1.0 + (i / days) * 0.06  # +6% over 90 days
        noise = 1.0 + RNG.uniform(-0.04, 0.04)
        revenue = base * growth * noise
        # Last 2 days dip (the disruption story)
        if i == days - 2:
            revenue = 412_800
        elif i == days - 1:
            revenue = 184_320  # today partial
        rows.append((store_id, d.strftime("%Y-%m-%d"), round(revenue, 2)))
    return rows


def _gen_category_history(days: int, store_id: str) -> list[tuple[str, str, str, float]]:
    """30 days of category daily revenue with realistic patterns."""
    today = datetime(2026, 5, 6)
    profiles = {
        "Dairy":         {"base": 43_000, "trend": 0.001, "noise": 0.04, "shock_last": 0.30},   # crash
        "Produce":       {"base": 63_000, "trend": 0.001, "noise": 0.05, "shock_last": 0.65},
        "Beverages":     {"base": 79_000, "trend": 0.004, "noise": 0.05, "shock_last": 0.40},
        "Snacks":        {"base": 22_000, "trend": 0.003, "noise": 0.05, "shock_last": 0.85},
        "Frozen":        {"base": 28_000, "trend": 0.001, "noise": 0.04, "shock_last": 0.55},
        "Bakery":        {"base": 18_500, "trend": 0.0,    "noise": 0.04, "shock_last": 0.55},
        "Household":     {"base": 32_000, "trend": 0.0005, "noise": 0.04, "shock_last": 0.60},
        "Personal Care": {"base": 14_500, "trend": 0.0,    "noise": 0.04, "shock_last": 0.70},
        "Apparel":       {"base": 54_000, "trend": -0.001, "noise": 0.06, "shock_last": 0.20},  # clearance flop
        "Electronics":   {"base": 99_000, "trend": -0.0005, "noise": 0.07, "shock_last": 0.40},
    }
    rows = []
    for cat, p in profiles.items():
        for i in range(days):
            d = today - timedelta(days=days - 1 - i)
            weekday = d.weekday()
            seasonal = 1.18 if weekday >= 5 else 1.0
            growth = 1.0 + p["trend"] * i
            noise = 1.0 + RNG.uniform(-p["noise"], p["noise"])
            r = p["base"] * seasonal * growth * noise
            # Recent shocks
            if i == days - 1:
                r = p["base"] * p["shock_last"]  # today partial
            elif i == days - 2 and cat == "Dairy":
                r = p["base"] * 0.45  # yesterday already declining
            rows.append((store_id, d.strftime("%Y-%m-%d"), cat, round(r, 2)))
    return rows


def _gen_agent_runs(days: int) -> list[tuple[int, str, int, int, float]]:
    """Adoption curve: gradual ramp from 142 to 472 daily runs."""
    today = datetime(2026, 5, 6)
    rows = []
    for i in range(days):
        offset = -(days - 1 - i)
        d = today + timedelta(days=offset)
        runs = int(140 + (i / days) * 340 + RNG.randint(-12, 12))
        if i == days - 1:
            runs = 184  # partial day
        latency = int(1820 - (i / days) * 580 + RNG.randint(-30, 30))
        cost = round(runs * 0.022 + RNG.uniform(-0.4, 0.4), 2)
        rows.append((offset, d.strftime("%Y-%m-%d"), runs, latency, cost))
    return rows


def _gen_hourly(store_id: str) -> list[tuple[str, str, float, float, int]]:
    """Forecast: gentle bell curve. Actual: matches forecast through 11am, then zero."""
    base_rows = _load_seed("sales.json")["hourly"]
    return [(store_id, h["hour"], h["revenue"], h["forecast"], h["transactions"]) for h in base_rows]


def seed_all(rebuild: bool = False) -> dict:
    """Wipe (if rebuild) and populate the DB from JSON + generators."""
    if rebuild and DB_PATH.exists():
        DB_PATH.unlink()
    dbm.init_schema()

    stores = _load_seed("stores.json")
    inv = _load_seed("inventory.json")
    sal = _load_seed("sales.json")
    lab = _load_seed("labor.json")
    pro = _load_seed("promotions.json")
    rev = _load_seed("reviews.json")
    sup = _load_seed("suppliers.json")
    scn = _load_seed("disruption_scenarios.json")

    current_store_id = stores["current_store_id"]

    with dbm.get_conn() as conn:
        cur = conn.cursor()
        # Clear tables for idempotent seed
        for t in [
            "config", "stores", "suppliers", "disruption_scenarios",
            "category_health", "critical_skus",
            "sales_today", "sales_yesterday", "sales_hourly", "sales_category_today",
            "top_movers", "sales_daily_history", "sales_category_history",
            "labor_today", "departments", "callouts",
            "promotions", "competitor_intel",
            "reviews_summary", "review_themes", "recent_reviews",
            "agent_runs_daily", "agent_breakdown", "disruptions_handled",
        ]:
            cur.execute(f"DELETE FROM {t}")

        # Config
        cur.execute("INSERT INTO config(key, value) VALUES (?, ?)", ("current_store_id", current_store_id))

        # Stores
        for s in stores["stores"]:
            cur.execute(
                "INSERT INTO stores VALUES (?,?,?,?,?,?,?,?)",
                (s["id"], s["name"], s["city"], s["lat"], s["lon"], s["format"], s["sqft"], s["manager"]),
            )

        # Suppliers
        for s in sup["suppliers"]:
            cur.execute(
                "INSERT INTO suppliers VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    s["id"], s["name"],
                    json.dumps(s["categories"]), json.dumps(s["regions"]),
                    s["lead_time_days"], s["reliability_pct"],
                    json.dumps(s["alt_suppliers"]), s["risk"],
                    s.get("current_alert"),
                ),
            )

        # Scenarios
        for sc in scn["scenarios"]:
            cur.execute(
                "INSERT INTO disruption_scenarios VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    sc["id"], sc["title"], sc["type"], sc["severity"],
                    json.dumps(sc["affected_regions"]), json.dumps(sc["affected_stores"]),
                    sc["details"],
                    json.dumps(sc.get("expected_skus_at_risk", [])),
                    json.dumps(sc.get("demand_surge_categories", [])),
                ),
            )

        # Inventory snapshot
        for c in inv["categories"]:
            cur.execute(
                "INSERT INTO category_health VALUES (?,?,?,?,?,?,?,?)",
                (current_store_id, c["category"], c["on_hand_units"], c["days_of_supply"],
                 c["stockout_skus"], c["trend"], c["alert"], inv["as_of"]),
            )
        for s in inv["critical_skus"]:
            cur.execute(
                "INSERT INTO critical_skus VALUES (?,?,?,?,?,?,?,?,?)",
                (s["sku"], current_store_id, s["name"], s["category"],
                 s["on_hand"], s["weekly_velocity"], s["last_delivery"],
                 s["next_delivery"], s["lost_sales_est"]),
            )

        # Sales — today + yesterday
        t = sal["today"]
        cur.execute(
            "INSERT INTO sales_today VALUES (?,?,?,?,?,?,?,?,?)",
            (current_store_id, t["revenue_to_date"], t["forecast_to_date"], t["variance_pct"],
             t["transactions"], t["avg_basket"], t["traffic"], t["conversion_pct"], sal["as_of"]),
        )
        y = sal["yesterday"]
        cur.execute(
            "INSERT INTO sales_yesterday VALUES (?,?,?,?,?)",
            (current_store_id, y["revenue"], y["forecast"], y["transactions"], y["avg_basket"]),
        )
        for h in _gen_hourly(current_store_id):
            cur.execute("INSERT INTO sales_hourly VALUES (?,?,?,?,?)", h)
        for c in sal["by_category"]:
            cur.execute(
                "INSERT INTO sales_category_today VALUES (?,?,?,?,?,?)",
                (current_store_id, c["category"], c["revenue"], c["forecast"], c["variance_pct"], c["trend"]),
            )
        for m in sal["top_movers_up"]:
            cur.execute("INSERT INTO top_movers VALUES (?,?,?,?,?)",
                        (current_store_id, m["sku"], m["name"], m["delta_pct"], "up"))
        for m in sal["top_movers_down"]:
            cur.execute("INSERT INTO top_movers VALUES (?,?,?,?,?)",
                        (current_store_id, m["sku"], m["name"], m["delta_pct"], "down"))

        # Historical timeseries
        for row in _gen_daily_revenue(90, current_store_id):
            cur.execute("INSERT INTO sales_daily_history VALUES (?,?,?)", row)
        for row in _gen_category_history(30, current_store_id):
            cur.execute("INSERT INTO sales_category_history VALUES (?,?,?,?)", row)

        # Labor
        l = lab["today"]
        cur.execute(
            "INSERT INTO labor_today VALUES (?,?,?,?,?,?,?,?,?)",
            (current_store_id, l["scheduled_hours"], l["actual_hours_to_date"],
             l["callouts"], l["open_shifts"], l["overtime_hours"],
             l["labor_cost_pct_of_sales"], l["target_pct"], lab["as_of"]),
        )
        for d in lab["departments"]:
            cur.execute(
                "INSERT INTO departments VALUES (?,?,?,?,?,?)",
                (current_store_id, d["dept"], d["scheduled"], d["filled"], d["gap"], d["status"]),
            )
        for c in lab["callout_details"]:
            cur.execute(
                "INSERT INTO callouts(store_id, associate, dept, shift, reason) VALUES (?,?,?,?,?)",
                (current_store_id, c["associate"], c["dept"], c["shift"], c["reason"]),
            )

        # Promotions
        for p in pro["active"]:
            cur.execute(
                "INSERT INTO promotions VALUES (?,?,?,?,?,?,?,?,?)",
                (p["id"], current_store_id, p["name"], p["category"],
                 p["start"], p["end"], p["lift_pct"], p["redemptions"], p["status"]),
            )
        for c in pro["competitor_intel"]:
            cur.execute(
                "INSERT INTO competitor_intel(store_id, competitor, distance_mi, promo, started, estimated_traffic_pull) VALUES (?,?,?,?,?,?)",
                (current_store_id, c["competitor"], c["distance_mi"], c["promo"], c["started"], c["estimated_traffic_pull"]),
            )

        # Reviews
        rs = rev["summary"]
        cur.execute(
            "INSERT INTO reviews_summary VALUES (?,?,?,?,?,?,?)",
            (current_store_id, rs["rating_today"], rs["rating_30d"],
             rs["review_count_today"], rs["review_count_30d"],
             rs["sentiment_score"], rs["trend"]),
        )
        for t in rev["themes"]:
            cur.execute(
                "INSERT INTO review_themes VALUES (?,?,?,?,?)",
                (current_store_id, t["theme"], t["mentions"], t["sentiment"], t["delta_vs_30d"]),
            )
        for r in rev["recent"]:
            cur.execute(
                "INSERT INTO recent_reviews(store_id, author, rating, time, text) VALUES (?,?,?,?,?)",
                (current_store_id, r["author"], r["rating"], r["time"], r["text"]),
            )

        # Analytics — agent activity
        for row in _gen_agent_runs(30):
            cur.execute("INSERT INTO agent_runs_daily VALUES (?,?,?,?,?)", row)

        agent_categories = {
            "Sales": "store_manager", "Inventory": "store_manager", "Labor": "store_manager",
            "Promo": "store_manager", "Reviews": "store_manager",
            "Disruption Detector": "disruption", "Supplier Researcher": "disruption",
            "Inventory Rebalancer": "disruption", "Impact Modeler": "disruption",
            "Comms Drafter": "disruption",
        }
        hist = _load_seed("historical.json")
        for b in hist["agent_breakdown"]:
            cur.execute(
                "INSERT INTO agent_breakdown VALUES (?,?,?,?,?)",
                (b["agent"], b["calls"], b["avg_ms"], b["cost_usd"],
                 agent_categories.get(b["agent"], "other")),
            )
        for d in hist["disruptions_handled_90d"]:
            cur.execute(
                "INSERT INTO disruptions_handled(date, type, title, stores_affected, minutes_to_response) VALUES (?,?,?,?,?)",
                (d["date"], d["type"], d["title"], d["stores_affected"], d["minutes_to_response"]),
            )

        conn.commit()

    return dbm.db_stats()


if __name__ == "__main__":
    import sys
    rebuild = "--rebuild" in sys.argv
    stats = seed_all(rebuild=rebuild)
    print(f"Seeded: {stats['tables']} tables, {stats['rows']} rows at {stats['path']}")
