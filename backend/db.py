"""SQLite database — schema, connection, and helpers."""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from typing import Optional
from .config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS stores (
  id TEXT PRIMARY KEY,
  name TEXT, city TEXT, lat REAL, lon REAL,
  format TEXT, sqft INTEGER, manager TEXT
);

CREATE TABLE IF NOT EXISTS suppliers (
  id TEXT PRIMARY KEY,
  name TEXT, categories_json TEXT, regions_json TEXT,
  lead_time_days INTEGER, reliability_pct REAL,
  alt_suppliers_json TEXT, risk TEXT, current_alert TEXT
);

CREATE TABLE IF NOT EXISTS disruption_scenarios (
  id TEXT PRIMARY KEY,
  title TEXT, type TEXT, severity TEXT,
  affected_regions_json TEXT, affected_stores_json TEXT,
  details TEXT, expected_skus_at_risk_json TEXT,
  demand_surge_categories_json TEXT
);

CREATE TABLE IF NOT EXISTS category_health (
  store_id TEXT, category TEXT,
  on_hand_units INTEGER, days_of_supply REAL,
  stockout_skus INTEGER, trend TEXT, alert TEXT,
  as_of TEXT,
  PRIMARY KEY (store_id, category)
);

CREATE TABLE IF NOT EXISTS critical_skus (
  sku TEXT PRIMARY KEY,
  store_id TEXT, name TEXT, category TEXT,
  on_hand INTEGER, weekly_velocity INTEGER,
  last_delivery TEXT, next_delivery TEXT, lost_sales_est REAL
);

CREATE TABLE IF NOT EXISTS sales_today (
  store_id TEXT PRIMARY KEY,
  revenue_to_date REAL, forecast_to_date REAL, variance_pct REAL,
  transactions INTEGER, avg_basket REAL, traffic INTEGER, conversion_pct REAL,
  as_of TEXT
);

CREATE TABLE IF NOT EXISTS sales_yesterday (
  store_id TEXT PRIMARY KEY,
  revenue REAL, forecast REAL, transactions INTEGER, avg_basket REAL
);

CREATE TABLE IF NOT EXISTS sales_hourly (
  store_id TEXT, hour TEXT,
  revenue REAL, forecast REAL, transactions INTEGER,
  PRIMARY KEY (store_id, hour)
);

CREATE TABLE IF NOT EXISTS sales_category_today (
  store_id TEXT, category TEXT,
  revenue REAL, forecast REAL, variance_pct REAL, trend TEXT,
  PRIMARY KEY (store_id, category)
);

CREATE TABLE IF NOT EXISTS top_movers (
  store_id TEXT, sku TEXT, name TEXT,
  delta_pct REAL, direction TEXT,
  PRIMARY KEY (store_id, sku, direction)
);

CREATE TABLE IF NOT EXISTS sales_daily_history (
  store_id TEXT, date TEXT, revenue REAL,
  PRIMARY KEY (store_id, date)
);

CREATE TABLE IF NOT EXISTS sales_category_history (
  store_id TEXT, date TEXT, category TEXT, revenue REAL,
  PRIMARY KEY (store_id, date, category)
);

CREATE TABLE IF NOT EXISTS labor_today (
  store_id TEXT PRIMARY KEY,
  scheduled_hours INTEGER, actual_hours_to_date INTEGER,
  callouts INTEGER, open_shifts INTEGER, overtime_hours INTEGER,
  labor_cost_pct_of_sales REAL, target_pct REAL, as_of TEXT
);

CREATE TABLE IF NOT EXISTS departments (
  store_id TEXT, dept TEXT,
  scheduled INTEGER, filled INTEGER, gap INTEGER, status TEXT,
  PRIMARY KEY (store_id, dept)
);

CREATE TABLE IF NOT EXISTS callouts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  store_id TEXT, associate TEXT, dept TEXT, shift TEXT, reason TEXT
);

CREATE TABLE IF NOT EXISTS promotions (
  id TEXT PRIMARY KEY, store_id TEXT,
  name TEXT, category TEXT, start_date TEXT, end_date TEXT,
  lift_pct REAL, redemptions INTEGER, status TEXT
);

CREATE TABLE IF NOT EXISTS competitor_intel (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  store_id TEXT, competitor TEXT, distance_mi REAL,
  promo TEXT, started TEXT, estimated_traffic_pull TEXT
);

CREATE TABLE IF NOT EXISTS reviews_summary (
  store_id TEXT PRIMARY KEY,
  rating_today REAL, rating_30d REAL,
  count_today INTEGER, count_30d INTEGER,
  sentiment_score REAL, trend TEXT
);

CREATE TABLE IF NOT EXISTS review_themes (
  store_id TEXT, theme TEXT,
  mentions INTEGER, sentiment TEXT, delta_vs_30d TEXT,
  PRIMARY KEY (store_id, theme)
);

CREATE TABLE IF NOT EXISTS recent_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  store_id TEXT, author TEXT, rating INTEGER, time TEXT, text TEXT
);

CREATE TABLE IF NOT EXISTS agent_runs_daily (
  day_offset INTEGER PRIMARY KEY,
  date TEXT, runs INTEGER, avg_latency_ms INTEGER, cost_usd REAL
);

CREATE TABLE IF NOT EXISTS agent_breakdown (
  agent TEXT PRIMARY KEY,
  calls INTEGER, avg_ms INTEGER, cost_usd REAL,
  category TEXT
);

CREATE TABLE IF NOT EXISTS disruptions_handled (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT, type TEXT, title TEXT,
  stores_affected INTEGER, minutes_to_response INTEGER
);
"""


def _row_to_dict(cursor, row):
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


@contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = lambda c, r: _row_to_dict(c, r)
    try:
        yield conn
    finally:
        conn.close()


def init_schema():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def fetch_all(query: str, params: tuple = ()) -> list:
    with get_conn() as conn:
        return list(conn.execute(query, params))


def fetch_one(query: str, params: tuple = ()) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(query, params).fetchone()
        return row


def db_stats() -> dict:
    with get_conn() as conn:
        tables = [r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )]
        counts = {}
        total = 0
        for t in tables:
            n = conn.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
            counts[t] = n
            total += n
        return {
            "path": str(DB_PATH),
            "tables": len(tables),
            "rows": total,
            "by_table": counts,
        }


def parse_json(s):
    return json.loads(s) if s else None
