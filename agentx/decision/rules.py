import sqlite3
import json
import logging
from datetime import datetime, timezone
import os
from typing import Dict, Any, Optional

logger = logging.getLogger("agentx.decision.rules")
DB_PATH = os.environ.get("AGENTX_DB_PATH", os.path.join(".agentx", "aja_secretary.sqlite3"))

def init_rules_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decision_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                condition TEXT,
                action TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)

def create_rule(pattern: str, condition: Dict[str, Any], action: str):
    init_rules_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Check if identical rule exists
            existing = conn.execute(
                "SELECT id FROM decision_rules WHERE pattern = ? AND action = ?", 
                (pattern, action)
            ).fetchone()
            if existing:
                return
            
            conn.execute(
                "INSERT INTO decision_rules (pattern, condition, action, created_at) VALUES (?, ?, ?, ?)",
                (pattern, json.dumps(condition), action, now)
            )
            print(f"[Rules] RULE_CREATED: Pattern='{pattern}' -> Action='{action}'")
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")

def check_rules(objective: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Deterministic rule engine that overrides decisions based on exact matches or keywords.
    No LLM is used here.
    """
    init_rules_db()
    obj_lower = objective.lower()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rules = conn.execute("SELECT * FROM decision_rules ORDER BY id DESC").fetchall()
            
            for rule in rules:
                pattern = rule["pattern"].lower()
                
                # Simple deterministic check: if pattern is a substring of the objective
                if pattern in obj_lower:
                    # Optional condition check
                    condition = {}
                    if rule["condition"]:
                        condition = json.loads(rule["condition"])
                    
                    # If condition demands certain context, verify it
                    condition_met = True
                    for k, v in condition.items():
                        if context.get(k) != v:
                            condition_met = False
                            break
                            
                    if condition_met:
                        action = rule["action"]
                        print(f"[Rules] RULE_APPLIED: Matched pattern '{pattern}'")
                        print(f"[Rules] RULE_OVERRIDE: Forcing decision to {action}")
                        return {
                            "type": action,
                            "confidence": 1.0,
                            "reason": f"Deterministic rule override matched pattern: '{pattern}'"
                        }
    except Exception as e:
        logger.error(f"Failed to check rules: {e}")
        
    return None

def extract_rule_from_failures(objective: str, context: Dict[str, Any]):
    """
    Automatically called when repeated failures occur.
    Generates a deterministic rule to prevent future failures.
    """
    from agentx.decision.feedback import extract_tags
    
    tags = extract_tags(objective)
    if not tags:
        return
        
    # We use the primary tag or phrase as the pattern
    pattern = tags[0] if tags else objective
    
    # If the system failed repeatedly on this, default action is to ASK for human help
    # to avoid further automatic failures.
    action = "ASK"
    condition = {}  # Could capture specific context states like 'load_level' in the future
    
    create_rule(pattern, condition, action)
