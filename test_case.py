import sqlite3
import hashlib
from datetime import datetime, timezone
import sys
import os

DB_PATH = ".agentx/aja_secretary.sqlite3"
os.makedirs(".agentx", exist_ok=True)

def simulate():
    objective = "test duplicate"
    execution_hash = hashlib.sha256(f"{objective}:cmd_run".encode()).hexdigest()
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, input TEXT, status TEXT, created_at TIMESTAMP, updated_at TIMESTAMP, retry_count INTEGER DEFAULT 0, last_error TEXT, execution_hash TEXT, execution_started_at TIMESTAMP, execution_finished_at TIMESTAMP)")
        
        # Insert a COMPLETED task with the hash
        conn.execute("INSERT INTO tasks (input, status, created_at, updated_at, execution_hash) VALUES (?, ?, ?, ?, ?)",
                     ('{"input": "test duplicate"}', 'COMPLETED', datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(), execution_hash))
        conn.commit()
        
    print("Inserted dummy completed task. Run agentx run 'test duplicate'")

if __name__ == "__main__":
    simulate()
