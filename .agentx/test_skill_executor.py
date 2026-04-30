"""
Smoke test — Phase 8B: skill_executor.py integration
Run from project root:
  python -c "import sys; sys.path.insert(0,'.'); exec(open('.agentx/test_skill_executor.py').read())"
"""
import os, sys, json, sqlite3, uuid

TEST_DB = os.path.join(".agentx", "test_executor_smoke.sqlite3")
os.environ["AGENTX_DB_PATH"] = TEST_DB
for f in [TEST_DB]:
    if os.path.exists(f): os.remove(f)

from agentx.skills.skill_store    import create_skill_from_task, recommend_skill, get_skill
from agentx.skills.skill_executor import execute_skill, _risk_gate, _update_skill_metrics
from agentx.persistence.tasks     import init_db, create_task, update_task_status

init_db()
PASS, FAIL = [], []

def check(label, cond, detail=""):
    if cond:
        PASS.append(label); print(f"  [PASS] {label}")
    else:
        FAIL.append(label); print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))

# ── Helper: create skill with injected tool_executions ────────────────────────
def seed_skill(objective, tools, status="COMPLETED"):
    tid = create_task({"input": objective})
    update_task_status(tid, "RUNNING")
    update_task_status(tid, status)
    run_id = str(uuid.uuid4())
    conn = sqlite3.connect(TEST_DB); conn.row_factory = sqlite3.Row
    conn.execute("UPDATE tasks SET run_id=? WHERE id=?", (run_id, tid))
    conn.execute("""CREATE TABLE IF NOT EXISTS tool_executions (
        idempotency_key TEXT PRIMARY KEY, tool_name TEXT, args_hash TEXT,
        status TEXT, result TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)""")
    for i, t in enumerate(tools):
        conn.execute(
            "INSERT OR IGNORE INTO tool_executions "
            "(idempotency_key,tool_name,args_hash,status,created_at,updated_at) "
            "VALUES(?,?,?,?,datetime('now'),datetime('now'))",
            (f"{run_id}:{t}:{i}", t, "aaa", "COMPLETED"))
    conn.commit(); conn.close()
    return create_skill_from_task(tid)

print("\n=== Phase 8B Skill Executor Smoke Test ===\n")

# ── Step 2: Risk gate ─────────────────────────────────────────────────────────
print("Step 2 — Risk gate")

low_skill    = {"id": "x1", "name": "Read Config", "risk_level": "LOW",  "pitfalls": ""}
medium_skill = {"id": "x2", "name": "Send Email",  "risk_level": "MEDIUM","pitfalls": "dup sends"}
high_skill   = {"id": "x3", "name": "Delete Records","risk_level": "HIGH","pitfalls": "destructive"}

check("LOW risk gate passes",    _risk_gate(low_skill))
check("MEDIUM risk gate passes", _risk_gate(medium_skill))

# HIGH-risk with deny confirm_fn → must return False
check("HIGH risk gate DENIED when confirm_fn returns False",
      not _risk_gate(high_skill, confirm_fn=lambda _: False))

# HIGH-risk with approve confirm_fn → must return True
check("HIGH risk gate APPROVED when confirm_fn returns True",
      _risk_gate(high_skill, confirm_fn=lambda _: True))

# ── Step 5: Metrics update ────────────────────────────────────────────────────
print("\nStep 5 — Metrics update")
sid_low = seed_skill("load configuration from file", ["read_file", "parse_yaml"])
check("Seed skill created", sid_low is not None)
if sid_low:
    sk_before = get_skill(sid_low)
    _update_skill_metrics(sid_low, success=True)
    sk_after = get_skill(sid_low)
    check("S5 success_count incremented", sk_after["success_count"] == sk_before["success_count"] + 1)
    check("S5 confidence_score recalculated",
          0.0 <= sk_after["confidence_score"] <= 1.0)

    _update_skill_metrics(sid_low, success=False)
    sk_fail = get_skill(sid_low)
    check("S5 failure_count incremented",
          sk_fail["failure_count"] == sk_before["failure_count"] + 1)

# ── Step 3 + 4: Full execute_skill() flow ─────────────────────────────────────
print("\nStep 3+4 — execute_skill() with LOW-risk skill")
run_id = str(uuid.uuid4())
# Build a minimal skill dict with a two-step tool_sequence
skill_dict = {
    "id":          sid_low or "test-skill-id",
    "name":        "Load Config",
    "risk_level":  "LOW",
    "pitfalls":    "",
    "confidence_score": 1.0,
    "tool_sequence": json.dumps([
        {"tool_name": "read_file",  "args_schema": {"path": "config.yaml"}},
        {"tool_name": "parse_yaml", "args_schema": {"content": ""}},
    ]),
}

events_logged = []
class FakeTracker:
    @staticmethod
    def log_event(event, payload=None):
        events_logged.append(event)
        print(f"    [evt] {event}")

result = execute_skill(
    skill      = skill_dict,
    task_id    = 1,
    run_id     = run_id,
    objective  = "load configuration from file",
    tracker    = FakeTracker,
    confirm_fn = None,
)
check("S3 execute_skill returns True for LOW-risk", result is True, f"got {result}")
check("S6 SKILL_SELECTED logged",           "SKILL_SELECTED"            in events_logged)
check("S6 SKILL_EXECUTION_STARTED logged",  "SKILL_EXECUTION_STARTED"   in events_logged)
check("S6 SKILL_EXECUTION_COMPLETED logged","SKILL_EXECUTION_COMPLETED"  in events_logged)
check("S6 SKILL_FALLBACK NOT logged on success", "SKILL_FALLBACK" not in events_logged)

# Idempotency: second call with same run_id should coalesce (not re-execute)
events_logged.clear()
result2 = execute_skill(
    skill=skill_dict, task_id=1, run_id=run_id,
    objective="load configuration from file", tracker=FakeTracker,
)
check("S3 second call with same run_id succeeds (coalesced)", result2 is True)

# ── Step 4: Fallback on empty tool_sequence ────────────────────────────────────
print("\nStep 4 — Fallback on empty tool_sequence")
empty_skill = {
    "id": "empty-skill", "name": "Empty Skill", "risk_level": "LOW",
    "confidence_score": 1.0, "tool_sequence": json.dumps([]),
}
events_logged2 = []
class FakeTracker2:
    @staticmethod
    def log_event(event, payload=None):
        events_logged2.append(event)

result_empty = execute_skill(
    skill=empty_skill, task_id=2, run_id=str(uuid.uuid4()),
    objective="empty test", tracker=FakeTracker2,
)
check("S4 empty tool_sequence returns False", result_empty is False)
check("S6 SKILL_EXECUTION_FAILED logged on empty", "SKILL_EXECUTION_FAILED" in events_logged2)
check("S6 SKILL_FALLBACK logged on empty",         "SKILL_FALLBACK"         in events_logged2)

# ── Step 2: HIGH-risk denied → fallback ───────────────────────────────────────
print("\nStep 2 — HIGH-risk denied → returns False immediately")
high_seq_skill = {
    "id": "high-risk-skill", "name": "Delete All Records", "risk_level": "HIGH",
    "confidence_score": 1.0, "pitfalls": "destructive",
    "tool_sequence": json.dumps([{"tool_name": "delete_records", "args_schema": {}}]),
}
denied_result = execute_skill(
    skill=high_seq_skill, task_id=3, run_id=str(uuid.uuid4()),
    objective="delete all records", tracker=None,
    confirm_fn=lambda _: False,  # deny
)
check("S2 HIGH-risk denied returns False", denied_result is False)

approved_result = execute_skill(
    skill=high_seq_skill, task_id=3, run_id=str(uuid.uuid4()),
    objective="delete all records", tracker=None,
    confirm_fn=lambda _: True,   # approve
)
check("S2 HIGH-risk approved returns True", approved_result is True)

# ── Summary ───────────────────────────────────────────────────────────────────
import gc; gc.collect()
try: os.remove(TEST_DB)
except OSError: pass

print(f"\n{'='*44}")
print(f"PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
if FAIL:
    print("Failed:", FAIL); sys.exit(1)
else:
    print("ALL CASES PASSED ✓")
