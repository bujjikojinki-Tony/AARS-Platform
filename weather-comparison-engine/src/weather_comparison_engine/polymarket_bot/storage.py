from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS market_snapshots (
      market_id TEXT PRIMARY KEY,
      question TEXT NOT NULL,
      slug TEXT,
      category TEXT,
      yes_price REAL NOT NULL,
      no_price REAL NOT NULL,
      liquidity REAL NOT NULL,
      spread REAL NOT NULL,
      fetched_at TEXT NOT NULL,
      source TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS strategy_signals (
      signal_id TEXT PRIMARY KEY,
      market_id TEXT NOT NULL,
      strategy_id TEXT NOT NULL,
      side TEXT NOT NULL,
      model_probability REAL NOT NULL,
      market_probability REAL NOT NULL,
      edge_percent REAL NOT NULL,
      z_score REAL,
      confidence TEXT NOT NULL,
      reason TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS opportunity_candidates (
      candidate_id TEXT PRIMARY KEY,
      signal_id TEXT NOT NULL,
      market_id TEXT NOT NULL,
      question TEXT NOT NULL,
      side TEXT NOT NULL,
      market_probability REAL NOT NULL,
      model_probability REAL NOT NULL,
      edge_percent REAL NOT NULL,
      z_score REAL,
      liquidity REAL NOT NULL,
      spread REAL NOT NULL,
      confidence_tier TEXT NOT NULL,
      risk_status TEXT NOT NULL,
      action_status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      expires_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS execution_decisions (
      decision_id TEXT PRIMARY KEY,
      candidate_id TEXT NOT NULL,
      mode TEXT NOT NULL,
      action TEXT NOT NULL,
      requested_by TEXT,
      approved_by TEXT,
      approval_required INTEGER NOT NULL,
      approval_status TEXT NOT NULL,
      position_size REAL NOT NULL,
      expected_cost REAL NOT NULL,
      risk_status TEXT NOT NULL,
      execution_status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      executed_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS simulation_results (
      simulation_id TEXT PRIMARY KEY,
      decision_id TEXT NOT NULL,
      candidate_id TEXT NOT NULL,
      side TEXT NOT NULL,
      entry_price REAL NOT NULL,
      position_size REAL NOT NULL,
      simulated_cost REAL NOT NULL,
      expected_probability REAL NOT NULL,
      expected_value REAL NOT NULL,
      max_loss REAL NOT NULL,
      max_gain REAL NOT NULL,
      result_status TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
      event_id TEXT PRIMARY KEY,
      event_type TEXT NOT NULL,
      object_type TEXT NOT NULL,
      object_id TEXT NOT NULL,
      payload_json TEXT,
      created_at TEXT NOT NULL
    )
    """,
)


def init_db(db_path: str | Path) -> sqlite3.Connection:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    conn.commit()
    return conn
