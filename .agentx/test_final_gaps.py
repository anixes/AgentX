"""
Phase 8B.1 — Final gaps smoke test (Issues 1, 2, 3, 4)
Run from project root:
  python -c "import sys; sys.path.insert(0,'.'); exec(open('.agentx/test_final_gaps.py').read())"
"""
import os, sys, json, sqlite3, uuid

TEST_DB = os.path.join(".agentx", "test_final_gaps.sqlite3")
os.environ["AGENTX_DB_PATH"] = TEST_DB
for f in [TEST_DB]:
    if os.path.exists(f): os.remove(f)

from agentx.skills.skill_store import (
    create_skill_from_task, recommend_skill, search_skills,
    get_skill, _expand_tokens, _tokenize, CONFIDENCE_GATE,
)
from agentx.skills.skill_executor import (
    execute_skill, check_environment, mark_stale_skills,
    _load_completed_steps, _checkpoint_step, _clear_checkpoints,
    _bootstrap_executor_tables, _refresh_last_used,
)
from agentx.persistence.tasks import init_db, create_task, update_task_status

init_db()
PASS, FAIL = [], []

def check(label, cond, detail=""):
    if cond:
        PASS.append(label); print(f"  [PASS] {label}")
    else:
        FAIL.append(label); print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))

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

print("\n=== Phase 8B.1 Final Gaps Smoke Test ===\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GAP 1 — Step-level recovery
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Gap 1 — Step-level recovery (resume from checkpoint)")

sid = seed_skill("fetch data process and store results",
                 ["fetch_data", "process_data", "store_results"])
check("G1 skill created", sid is not None)

# Get db bootstrapped for executor tables
conn = sqlite3.connect(TEST_DB); conn.row_factory = sqlite3.Row
_bootstrap_executor_tables(conn); conn.commit(); conn.close()

skill_dict = get_skill(sid) if sid else {}
if skill_dict:
    skill_dict["tool_sequence"] = json.dumps([
        {"tool_name": "fetch_data",    "args_schema": {}},
        {"tool_name": "process_data",  "args_schema": {}},
        {"tool_name": "store_results", "args_schema": {}},
    ])

run_id = str(uuid.uuid4())

# Simulate a crash after step 0 by manually checkpointing it
_checkpoint_step(sid, run_id, 0, "fetch_data", "row_data")
prior_done = _load_completed_steps(sid, run_id)
check("G1 checkpoint persisted", 0 in prior_done, f"got keys: {list(prior_done.keys())}")

# Execute: should skip step 0, run steps 1 and 2
events = []
class FT:
    @staticmethod
    def log_event(e, p=None): events.append(e)

if sid and skill_dict:
    result = execute_skill(skill=skill_dict, task_id=1, run_id=run_id,
                            objective="fetch data process and store results",
                            tracker=FT, confirm_fn=None)
    check("G1 execute_skill returns True (resumed)", result is True)
    check("G1 SKILL_RESUMING event logged",  "SKILL_RESUMING" in events)
    check("G1 checkpoints cleared on success",
          len(_load_completed_steps(sid, run_id)) == 0)

# Verify: no double-execution on re-run with NEW run_id (fresh start)
run_id2  = str(uuid.uuid4())
events2  = []
class FT2:
    @staticmethod
    def log_event(e, p=None): events2.append(e)

if sid and skill_dict:
    r2 = execute_skill(skill=skill_dict, task_id=1, run_id=run_id2,
                        objective="fetch data process and store results",
                        tracker=FT2, confirm_fn=None)
    check("G1 fresh run_id executes all steps (no phantom checkpoint)",
          r2 is True and "SKILL_RESUMING" not in events2)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GAP 2 — Environment validation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nGap 2 — Environment validation")

# Skill with no prerequisites → always OK
no_prereq_skill = {"id": "np1", "name": "NoPrereq", "risk_level": "LOW",
                   "prerequisites": "[]", "confidence_score": 1.0,
                   "tool_sequence": json.dumps([{"tool_name": "dummy", "args_schema": {}}])}
ok, failures = check_environment(no_prereq_skill)
check("G2 no prerequisites → env OK", ok is True, failures)

# Skill requiring 'database connection available' — DB file exists (we created it)
db_prereq_skill = {"id": "dp1", "name": "DBSkill", "risk_level": "LOW",
                   "prerequisites": '["database connection available"]',
                   "confidence_score": 1.0,
                   "tool_sequence": json.dumps([{"tool_name": "query_db", "args_schema": {}}])}
ok_db, failures_db = check_environment(db_prereq_skill)
check("G2 db prereq satisfied (file exists)", ok_db is True, failures_db)

# Skill requiring missing env var → should FAIL
os.environ.pop("SMTP_HOST", None); os.environ.pop("SMTP_USER", None)
email_prereq_skill = {"id": "ep1", "name": "EmailSkill", "risk_level": "MEDIUM",
                      "prerequisites": '["email credentials configured"]',
                      "confidence_score": 1.0,
                      "tool_sequence": json.dumps([{"tool_name": "send_email", "args_schema": {}}])}
ok_email, failures_email = check_environment(email_prereq_skill)
check("G2 email prereq FAILS (SMTP_HOST missing)", ok_email is False,
      f"unexpectedly passed; failures={failures_email}")
check("G2 failure message mentions prerequisite",
      any("email" in f.lower() for f in failures_email),
      f"failures: {failures_email}")

# Unknown prerequisite → warns but does NOT block
unknown_prereq = {"id": "up1", "name": "Unknown", "risk_level": "LOW",
                  "prerequisites": '["some future custom thing"]',
                  "confidence_score": 1.0,
                  "tool_sequence": json.dumps([{"tool_name": "tool_x", "args_schema": {}}])}
ok_unk, failures_unk = check_environment(unknown_prereq)
check("G2 unknown prerequisite warns but does not block", ok_unk is True, failures_unk)

# execute_skill aborts when env validation fails
evts_env = []
class FTEnv:
    @staticmethod
    def log_event(e, p=None): evts_env.append(e)

env_fail_result = execute_skill(
    skill=email_prereq_skill, task_id=2, run_id=str(uuid.uuid4()),
    objective="send email", tracker=FTEnv, confirm_fn=None,
)
check("G2 execute_skill returns False when env fails", env_fail_result is False)
check("G2 SKILL_EXECUTION_FAILED logged on env fail", "SKILL_EXECUTION_FAILED" in evts_env)
check("G2 SKILL_FALLBACK logged on env fail",         "SKILL_FALLBACK"         in evts_env)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GAP 3 — Validity decay
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nGap 3 — Validity decay")

sid_stale = seed_skill("transform legacy data format conversion",
                        ["read_legacy", "transform_data"])
check("G3 stale-target skill created", sid_stale is not None)

if sid_stale:
    # Force created_at + last_used_at far in the past
    conn = sqlite3.connect(TEST_DB)
    conn.execute("UPDATE skills SET created_at='2020-01-01', last_used_at='2020-01-01' WHERE id=?",
                 (sid_stale,))
    conn.commit(); conn.close()

    marked = mark_stale_skills(stale_after_days=30)
    check("G3 mark_stale_skills marks the old skill", marked >= 1, f"marked={marked}")

    # Stale skill should NOT appear in recommend_skill (default include_stale=False)
    rec_stale = recommend_skill("transform legacy data format", include_stale=False)
    check("G3 stale skill excluded from recommend_skill (default)",
          rec_stale is None or rec_stale["id"] != sid_stale,
          f"got stale skill: {rec_stale}")

    # With include_stale=True → should appear
    rec_incl = recommend_skill("transform legacy data format", include_stale=True)
    check("G3 stale skill visible with include_stale=True",
          rec_incl is not None and rec_incl["id"] == sid_stale,
          f"got {rec_incl}")

    # Executing the stale skill resets stale flag
    stale_skill_dict = get_skill(sid_stale)
    if stale_skill_dict:
        stale_skill_dict["tool_sequence"] = json.dumps([
            {"tool_name": "read_legacy",    "args_schema": {}},
            {"tool_name": "transform_data", "args_schema": {}},
        ])
        _refresh_last_used(sid_stale)
        sk_after = get_skill(sid_stale)
        check("G3 last_used_at updated after use", sk_after["last_used_at"] is not None)
        check("G3 is_stale reset to 0 after use", sk_after["is_stale"] == 0)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GAP 4 — Recall improvement (synonym expansion + bidirectional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nGap 4 — Recall (synonym expansion + bidirectional matching)")

# Confirm _expand_tokens works
fetch_expanded = _expand_tokens(_tokenize("fetch document"))
check("G4 'fetch' expands to include 'download'", "download" in fetch_expanded)
check("G4 'fetch' expands to include 'retrieve'", "retrieve" in fetch_expanded)
check("G4 'document' expands to include 'file'",  "file"     in fetch_expanded)

# Seed a skill with 'download file' as objective
sid_dl = seed_skill("download file from remote server",
                     ["http_request", "file_write"])
check("G4 'download file' skill created", sid_dl is not None)

# Query: "fetch document" — zero direct token overlap with "download file"
# BUT via synonym expansion: fetch→download, document→file → should match
results_syn = search_skills("fetch document", include_stale=False)
ids_syn = [r["id"] for r in results_syn]
check("G4 'fetch document' matches 'download file' skill via synonyms",
      sid_dl in ids_syn,
      f"ids: {[i[:10] for i in ids_syn]}")

# Bidirectional: query 'config' vs skill "load configuration from file parse settings"
sid_cfg = seed_skill("load configuration from file parse settings",
                      ["read_file", "parse_yaml"])
results_bd = search_skills("config", include_stale=False)
ids_bd = [r["id"] for r in results_bd]
check("G4 short query 'config' matches verbose skill via synonym bidirectional",
      sid_cfg in ids_bd, f"ids: {[i[:10] for i in ids_bd]}")

# Ranking: direct-term match should still rank above synonym match
sid_direct = seed_skill("fetch recent reports from api endpoint",
                         ["api_request", "report_parser"])
results_rank = search_skills("fetch report", include_stale=False)
ids_rank = [r["id"] for r in results_rank]
check("G4 direct-term skill in results", sid_direct in ids_rank,
      f"ids: {[i[:10] for i in ids_rank]}")

# Fully unrelated query still blocked
results_unrelated = search_skills("quantum entanglement physics", include_stale=False)
check("G4 unrelated query returns 0 results",
      len(results_unrelated) == 0, f"matched: {[r['name'] for r in results_unrelated[:2]]}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import gc; gc.collect()
try: os.remove(TEST_DB)
except OSError: pass

print(f"\n{'='*44}")
print(f"PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
if FAIL:
    print("Failed:", FAIL); sys.exit(1)
else:
    print("ALL CASES PASSED ✓")
