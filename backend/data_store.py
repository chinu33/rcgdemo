"""Data access layer — reads from the SQLite DB."""
from __future__ import annotations
from . import db as dbm


def _current_store_id() -> str:
    row = dbm.fetch_one("SELECT value FROM config WHERE key = 'current_store_id'")
    return row["value"] if row else "ST-014"


def stores() -> dict:
    rows = dbm.fetch_all("SELECT * FROM stores ORDER BY id")
    return {"stores": rows, "current_store_id": _current_store_id()}


def current_store() -> dict:
    sid = _current_store_id()
    return dbm.fetch_one("SELECT * FROM stores WHERE id = ?", (sid,))


def inventory() -> dict:
    sid = _current_store_id()
    cats = dbm.fetch_all(
        "SELECT category, on_hand_units, days_of_supply, stockout_skus, trend, alert "
        "FROM category_health WHERE store_id = ? ORDER BY category", (sid,)
    )
    skus = dbm.fetch_all(
        "SELECT sku, name, category, on_hand, weekly_velocity, last_delivery, next_delivery, lost_sales_est "
        "FROM critical_skus WHERE store_id = ?", (sid,)
    )
    as_of = dbm.fetch_one("SELECT as_of FROM category_health WHERE store_id = ? LIMIT 1", (sid,))
    return {
        "as_of": as_of["as_of"] if as_of else None,
        "store_id": sid,
        "categories": cats,
        "critical_skus": skus,
    }


def sales() -> dict:
    sid = _current_store_id()
    today = dbm.fetch_one("SELECT * FROM sales_today WHERE store_id = ?", (sid,)) or {}
    yest = dbm.fetch_one("SELECT * FROM sales_yesterday WHERE store_id = ?", (sid,)) or {}
    hourly = dbm.fetch_all(
        "SELECT hour, revenue, forecast, transactions FROM sales_hourly WHERE store_id = ? ORDER BY hour", (sid,)
    )
    by_cat = dbm.fetch_all(
        "SELECT category, revenue, forecast, variance_pct, trend FROM sales_category_today "
        "WHERE store_id = ? ORDER BY revenue DESC", (sid,)
    )
    up = dbm.fetch_all(
        "SELECT sku, name, delta_pct FROM top_movers WHERE store_id = ? AND direction = 'up' "
        "ORDER BY delta_pct DESC", (sid,)
    )
    down = dbm.fetch_all(
        "SELECT sku, name, delta_pct FROM top_movers WHERE store_id = ? AND direction = 'down' "
        "ORDER BY delta_pct ASC", (sid,)
    )
    return {
        "store_id": sid,
        "as_of": today.get("as_of"),
        "today": {
            "revenue_to_date": today.get("revenue_to_date", 0),
            "forecast_to_date": today.get("forecast_to_date", 0),
            "variance_pct": today.get("variance_pct", 0),
            "transactions": today.get("transactions", 0),
            "avg_basket": today.get("avg_basket", 0),
            "traffic": today.get("traffic", 0),
            "conversion_pct": today.get("conversion_pct", 0),
        },
        "yesterday": {
            "revenue": yest.get("revenue", 0),
            "forecast": yest.get("forecast", 0),
            "transactions": yest.get("transactions", 0),
            "avg_basket": yest.get("avg_basket", 0),
        },
        "hourly": hourly,
        "by_category": by_cat,
        "top_movers_up": up,
        "top_movers_down": down,
    }


def labor() -> dict:
    sid = _current_store_id()
    today = dbm.fetch_one("SELECT * FROM labor_today WHERE store_id = ?", (sid,)) or {}
    depts = dbm.fetch_all(
        "SELECT dept, scheduled, filled, gap, status FROM departments WHERE store_id = ?", (sid,)
    )
    callouts = dbm.fetch_all(
        "SELECT associate, dept, shift, reason FROM callouts WHERE store_id = ?", (sid,)
    )
    return {
        "store_id": sid,
        "as_of": today.get("as_of"),
        "today": {
            "scheduled_hours": today.get("scheduled_hours", 0),
            "actual_hours_to_date": today.get("actual_hours_to_date", 0),
            "callouts": today.get("callouts", 0),
            "open_shifts": today.get("open_shifts", 0),
            "overtime_hours": today.get("overtime_hours", 0),
            "labor_cost_pct_of_sales": today.get("labor_cost_pct_of_sales", 0),
            "target_pct": today.get("target_pct", 0),
        },
        "departments": depts,
        "callout_details": callouts,
    }


def promotions() -> dict:
    sid = _current_store_id()
    active = dbm.fetch_all(
        "SELECT id, name, category, start_date AS start, end_date AS end, lift_pct, redemptions, status "
        "FROM promotions WHERE store_id = ?", (sid,)
    )
    comp = dbm.fetch_all(
        "SELECT competitor, distance_mi, promo, started, estimated_traffic_pull FROM competitor_intel WHERE store_id = ?",
        (sid,),
    )
    return {"store_id": sid, "active": active, "competitor_intel": comp}


def reviews() -> dict:
    sid = _current_store_id()
    summary = dbm.fetch_one("SELECT * FROM reviews_summary WHERE store_id = ?", (sid,)) or {}
    themes = dbm.fetch_all(
        "SELECT theme, mentions, sentiment, delta_vs_30d FROM review_themes WHERE store_id = ? ORDER BY mentions DESC",
        (sid,),
    )
    recent = dbm.fetch_all(
        "SELECT author, rating, time, text FROM recent_reviews WHERE store_id = ? ORDER BY time DESC LIMIT 8",
        (sid,),
    )
    return {
        "store_id": sid,
        "summary": {
            "rating_today": summary.get("rating_today", 0),
            "rating_30d": summary.get("rating_30d", 0),
            "review_count_today": summary.get("count_today", 0),
            "review_count_30d": summary.get("count_30d", 0),
            "sentiment_score": summary.get("sentiment_score", 0),
            "trend": summary.get("trend", "stable"),
        },
        "themes": themes,
        "recent": recent,
    }


def suppliers() -> dict:
    rows = dbm.fetch_all("SELECT * FROM suppliers ORDER BY id")
    out = []
    for r in rows:
        out.append({
            "id": r["id"], "name": r["name"],
            "categories": dbm.parse_json(r["categories_json"]) or [],
            "regions": dbm.parse_json(r["regions_json"]) or [],
            "lead_time_days": r["lead_time_days"],
            "reliability_pct": r["reliability_pct"],
            "alt_suppliers": dbm.parse_json(r["alt_suppliers_json"]) or [],
            "risk": r["risk"],
            "current_alert": r["current_alert"],
        })
    return {"suppliers": out}


def disruption_scenarios() -> dict:
    rows = dbm.fetch_all("SELECT * FROM disruption_scenarios ORDER BY severity DESC, id")
    out = []
    for r in rows:
        out.append({
            "id": r["id"], "title": r["title"], "type": r["type"], "severity": r["severity"],
            "affected_regions": dbm.parse_json(r["affected_regions_json"]) or [],
            "affected_stores": dbm.parse_json(r["affected_stores_json"]) or [],
            "details": r["details"],
            "expected_skus_at_risk": dbm.parse_json(r["expected_skus_at_risk_json"]) or [],
            "demand_surge_categories": dbm.parse_json(r["demand_surge_categories_json"]) or [],
        })
    return {"scenarios": out}


def historical() -> dict:
    sid = _current_store_id()
    daily = dbm.fetch_all(
        "SELECT date, revenue FROM sales_daily_history WHERE store_id = ? ORDER BY date", (sid,)
    )
    cat_hist = dbm.fetch_all(
        "SELECT date, category, revenue FROM sales_category_history WHERE store_id = ? ORDER BY date", (sid,)
    )
    cats: dict[str, list] = {}
    dates_per_cat: dict[str, list] = {}
    for r in cat_hist:
        cats.setdefault(r["category"], []).append(r["revenue"])
        dates_per_cat.setdefault(r["category"], []).append(r["date"])
    runs = dbm.fetch_all(
        "SELECT day_offset AS day, date, runs, avg_latency_ms, cost_usd FROM agent_runs_daily ORDER BY day_offset"
    )
    breakdown = dbm.fetch_all(
        "SELECT agent, calls, avg_ms, cost_usd, category FROM agent_breakdown ORDER BY cost_usd DESC"
    )
    handled = dbm.fetch_all(
        "SELECT date, type, title, stores_affected, minutes_to_response FROM disruptions_handled ORDER BY date DESC"
    )
    return {
        "store_id": sid,
        "daily_revenue_90d": [r["revenue"] for r in daily],
        "daily_revenue_dates": [r["date"] for r in daily],
        "categories_30d": cats,
        "category_dates": dates_per_cat.get(next(iter(cats), ""), []),
        "agent_runs_30d": runs,
        "agent_breakdown": breakdown,
        "disruptions_handled_90d": handled,
    }


def dashboard_snapshot() -> dict:
    inv = inventory()
    sal = sales()
    lab = labor()
    rev = reviews()
    pro = promotions()
    store = current_store()

    critical_alerts = []
    for c in inv["categories"]:
        if c["alert"] == "critical":
            critical_alerts.append({
                "level": "critical",
                "title": f"{c['category']} stockout risk",
                "detail": f"{c['stockout_skus']} SKUs out, {c['days_of_supply']:.1f} days of supply",
            })
    for d in lab["departments"]:
        if d["status"] == "critical":
            critical_alerts.append({
                "level": "critical",
                "title": f"{d['dept']} understaffed",
                "detail": f"{d['gap']} hours uncovered today",
            })
    if rev["summary"]["sentiment_score"] < -0.1:
        critical_alerts.append({
            "level": "warning",
            "title": "Customer sentiment declining",
            "detail": f"Today rating {rev['summary']['rating_today']:.1f} vs 30d {rev['summary']['rating_30d']:.1f}",
        })
    for c in pro["competitor_intel"]:
        if c["estimated_traffic_pull"] == "high":
            critical_alerts.append({
                "level": "warning",
                "title": f"Competitor pressure: {c['competitor']}",
                "detail": f"{c['promo']} ({c['distance_mi']} mi)",
            })

    return {
        "store": store,
        "today": sal["today"],
        "yesterday": sal["yesterday"],
        "hourly": sal["hourly"],
        "categories": sal["by_category"],
        "top_up": sal["top_movers_up"],
        "top_down": sal["top_movers_down"],
        "inventory_categories": inv["categories"],
        "critical_skus": inv["critical_skus"],
        "labor": lab["today"],
        "departments": lab["departments"],
        "promos": pro["active"],
        "competitor_intel": pro["competitor_intel"],
        "reviews_summary": rev["summary"],
        "review_themes": rev["themes"],
        "recent_reviews": rev["recent"],
        "alerts": critical_alerts,
    }
