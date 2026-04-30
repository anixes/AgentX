"""
agentx/decision/feedback.py
==========================
Phase 10 — Decision Feedback Loop.

Tracks the outcomes of LLM-assisted decisions to enable self-improvement,
biasing, and better contextual prompting.
"""

import sqlite3
import hashlib
import os
from datetime import datetime, timezone

SECRETARY_DB = os.environ.get("AGENTX_DB_PATH", ".agentx/aja_secretary.sqlite3")

def init_feedback_db():
    """Ensure the decision_logs table exists."""
    os.makedirs(os.path.dirname(SECRETARY_DB) or ".", exist_ok=True)
    with sqlite3.connect(SECRETARY_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decision_logs (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                objective_hash TEXT NOT NULL,
                decision_type  TEXT NOT NULL,
                confidence     REAL,
                outcome        TEXT NOT NULL, -- SUCCESS | FAILURE | FALLBACK
                task_id        INTEGER,
                created_at     TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_obj_hash ON decision_logs(objective_hash)")

def get_objective_hash(objective: str) -> str:
    """Normalize and hash the objective string."""
    return hashlib.sha256(objective.strip().lower().encode('utf-8')).hexdigest()

def log_decision_outcome(objective: str, decision_type: str, confidence: float, outcome: str, task_id: int = None):
    """Record the outcome of a decision."""
    try:
        init_feedback_db()
        obj_hash = get_objective_hash(objective)
        with sqlite3.connect(SECRETARY_DB) as conn:
            conn.execute("""
                INSERT INTO decision_logs (objective_hash, decision_type, confidence, outcome, task_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (obj_hash, decision_type, confidence, outcome, task_id, datetime.now(timezone.utc).isoformat()))
    except Exception as e:
        print(f"[Feedback] Failed to log outcome: {e}")

def get_recent_decisions(objective: str, limit: int = 10):
    """Retrieve recent decision outcomes for a specific objective hash."""
    try:
        init_feedback_db()
        obj_hash = get_objective_hash(objective)
        with sqlite3.connect(SECRETARY_DB) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT decision_type, outcome, created_at 
                FROM decision_logs 
                WHERE objective_hash = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (obj_hash, limit)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Feedback] Failed to retrieve history: {e}")
        return []

def get_feedback_stats(objective: str):
    """Calculate success/failure stats for an objective."""
    history = get_recent_decisions(objective)
    stats = {}
    for entry in history:
        dtype = entry["decision_type"]
        if dtype not in stats:
            stats[dtype] = {"SUCCESS": 0, "FAILURE": 0, "FALLBACK": 0}
        stats[dtype][entry["outcome"]] += 1
    return stats
