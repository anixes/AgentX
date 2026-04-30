import sqlite3
import json
from datetime import datetime, timezone
import os

DB_PATH = os.path.join(".agentx", "aja_secretary.sqlite3")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

def log_event(event_type: str, payload: dict):
    init_db()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO execution_tracking (event_type, payload, timestamp) VALUES (?, ?, ?)",
                (event_type, json.dumps(payload), datetime.now(timezone.utc).isoformat())
            )
    except Exception as e:
        print(f"[Tracker] Failed to log event: {e}")
