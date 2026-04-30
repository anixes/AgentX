"""
Phase 9 Final Gaps smoke test
Run: python .agentx/test_phase9.py
"""
import os, sys, json, sqlite3, uuid

TEST_DB = os.path.join(".agentx", "test_phase9.sqlite3")
os.environ["AGENTX_DB_PATH"] = TEST_DB
for f in [TEST_DB]:
    if os.path.exists(f): os.remove(f)

from agentx.persistence.tasks import init_db, create_task, update_task_status
from agentx.skills.skill_store import create_skill_from_task, recommend_skill
from agentx.skills.skill_executor import _bootstrap_executor_tables
from agentx.skills.skill_postconditions import (
    validate_postconditions, add_postcondition, parse_postconditions, _ensure_postconditions_column
)
from agentx.skills.skill_composer import build_chain, compose_skills, _inject_context
from agentx.skills.skill_introspect import explain_skill, format_ambiguity_prompt

init_db()
PASS, FAIL = [], []

def check(label, cond, detail=""):
    if cond:
        PASS.append(label); print(f"  [PASS] {label}")
    else:
        FAIL.append(label); print(f"  [FAIL] {label} " + str(detail))

def seed_skill(objective, tools):
    tid = create_task({"input": objective})
    update_task_status(tid, "RUNNING")
    update_task_status(tid, "COMPLETED")
    run_id = str(uuid.uuid4())
    conn = sqlite3.connect(TEST_DB); conn.row_factory = sqlite3.Row
    conn.execute("UPDATE tasks SET run_id=? WHERE id=?", (run_id, tid))
    conn.execute("""CREATE TABLE IF NOT EXISTS tool_executions (
        idempotency_key TEXT PRIMARY KEY, tool_name TEXT, args_hash TEXT,
        status TEXT, result TEXT, error_type TEXT, last_error TEXT,
        created_at TIMESTAMP, finished_at TIMESTAMP)""")
    for i, t in enumerate(tools):
        conn.execute(
            "INSERT OR IGNORE INTO tool_executions "
            "(idempotency_key,tool_name,args_hash,status,created_at,finished_at) "
            "VALUES(?,?,?,?,datetime('now'),datetime('now'))",
            (f"{run_id}:{t}:{i}", t, "aaa", "COMPLETED"))
    conn.commit(); conn.close()
    return create_skill_from_task(tid)

# Ensure schema
conn = sqlite3.connect(TEST_DB); _bootstrap_executor_tables(conn); conn.commit(); conn.close()

print("\n=== Phase 9 Gaps Smoke Test ===\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Gap 1: Postconditions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Gap 1 — Postconditions")
s1 = seed_skill("test postconditions", ["tool1", "tool2"])
_ensure_postconditions_column()

add_postcondition(s1, {"type": "key_present", "target": "user_id", "expected": True})
add_postcondition(s1, {"type": "value_equals", "target": "status", "expected": "active", "required": False})

conn = sqlite3.connect(TEST_DB); conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM skills WHERE id=?", (s1,)).fetchone()
conn.close()
skill1 = dict(row)

# Valid results
results_ok = [{"step": 0, "tool": "tool1", "ok": True, "result": '{"user_id": 123, "status": "active"}'}]
ok, fails = validate_postconditions(skill1, results_ok)
check("G1 valid results pass", ok is True, fails)

# Invalid results (missing user_id)
results_bad = [{"step": 0, "tool": "tool1", "ok": True, "result": '{"status": "pending"}'}]
ok, fails = validate_postconditions(skill1, results_bad)
check("G1 missing required key fails", ok is False)
check("G1 failure details returned", len(fails) == 1, fails)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Gap 2: Multi-skill composer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nGap 2 — Multi-skill composer")

s_fetch = seed_skill("fetch data", ["fetch_tool", "parse_tool"])
s_process = seed_skill("process and store results", ["process_tool", "store_tool"])

# Context injection
step = {"tool_name": "t1", "args_schema": {"val": "{{my_var}}", "other": "static"}}
ctx = {"my_var": "resolved_value"}
inj = _inject_context(step, ctx)
check("G2 context injection works", inj["args_schema"]["val"] == "resolved_value", inj)

# Chain building
chain = build_chain("fetch data then process and store results")
check("G2 build_chain heuristic split works", len(chain) == 2, f"chain length={len(chain)}")
check("G2 chain sub-objectives correct", chain[0][1] == "fetch data" and chain[1][1] == "process and store results", chain)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Gap 3: Ambiguity Resolution
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nGap 3 — Ambiguity Resolution")

s_ambig1 = seed_skill("fetch document from server", ["t1", "t2"])
s_ambig2 = seed_skill("fetch document from remote", ["t3", "t4"])

def mock_resolver(query, skills):
    return [s for s in skills if "remote" in s["input_pattern"]][0]

rec = recommend_skill("fetch document from server remote", resolve_ambiguity_fn=mock_resolver)
check("G3 ambiguity resolver picked target", rec is not None and "remote" in rec["input_pattern"], rec)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Gap 4: Introspection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nGap 4 — Introspection")

exp = explain_skill(s1)
check("G4 explain_skill returns markdown", "## Tool Sequence" in exp and "test postconditions" in exp)

conn = sqlite3.connect(TEST_DB); conn.row_factory = sqlite3.Row
r1 = dict(conn.execute("SELECT * FROM skills WHERE id=?", (s_ambig1,)).fetchone())
r2 = dict(conn.execute("SELECT * FROM skills WHERE id=?", (s_ambig2,)).fetchone())
conn.close()

prompt = format_ambiguity_prompt("fetch doc", [r1, r2])
check("G4 format_ambiguity_prompt works", "fetch document" in prompt and "[?] Ambiguity" in prompt)


print(f"\n{'='*44}\nPASSED: {len(PASS)}  FAILED: {len(FAIL)}")
if FAIL: sys.exit(1)
