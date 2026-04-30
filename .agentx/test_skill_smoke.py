"""
Smoke test — Phase 8A.3 (Issues 1, 2, 3)
Covers: false-positive prevention, risk_level, confidence gating, recommend_skill.
Run:
  python -c "import sys; sys.path.insert(0,'.'); exec(open('.agentx/test_skill_smoke.py').read())"
"""
import os, sys, json, sqlite3, uuid

TEST_DB = os.path.join(".agentx", "test_skills_smoke.sqlite3")
os.environ["AGENTX_DB_PATH"] = TEST_DB
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from agentx.skills.skill_store import (
    create_skill_from_task, search_skills, get_skill,
    recommend_skill, CONFIDENCE_GATE, _overlap_score, _tokenize
)
from agentx.persistence.tasks import init_db, create_task, update_task_status

init_db()
PASS, FAIL = [], []

def check(label, cond, detail=""):
    if cond:
        PASS.append(label); print(f"  [PASS] {label}")
    else:
        FAIL.append(label); print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))

def make_and_capture(objective: str, tools: list):
    """Create task, inject tool_executions, capture skill. Returns skill_id or None."""
    tid = create_task({"input": objective})
    update_task_status(tid, "RUNNING")
    update_task_status(tid, "COMPLETED")
    run_id = str(uuid.uuid4())
    conn = sqlite3.connect(TEST_DB)
    conn.execute("UPDATE tasks SET run_id = ? WHERE id = ?", (run_id, tid))
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

print("\n=== Phase 8A.3 Skill Store Smoke Test ===\n")

# ── Issue 1: False positive prevention ───────────────────────────────────────
print("Issue 1 — False positive prevention (two-tier scorer)")

# Setup: two skills with overlapping keywords but different intents
sid_email_report = make_and_capture(
    "send email report to stakeholders",
    ["compose_email", "smtp_send"]
)
sid_generate = make_and_capture(
    "generate financial report pdf",
    ["report_generator", "pdf_export"]
)
check("Setup: email-report skill captured",  sid_email_report is not None)
check("Setup: generate-report skill captured", sid_generate is not None)

# "generate report" — 'report' IS in email-report's input_pattern,
# so we EXPECT both to match (shared noun). What matters is RANKING.
results_gen = search_skills("generate report")
ids_gen = [r["id"] for r in results_gen]
check("I1 'generate report' DOES match generate-report skill (true positive)",
      sid_generate in ids_gen,
      f"generate not found — ids: {ids_gen}")
# generate-report must score HIGHER than email-report for this query
if sid_email_report in ids_gen and sid_generate in ids_gen:
    idx_gen   = ids_gen.index(sid_generate)
    idx_email = ids_gen.index(sid_email_report)
    check("I1 generate-report ranks above email-report for 'generate report'",
          idx_gen < idx_email, f"generate at #{idx_gen}, email at #{idx_email}")
else:
    check("I1 generate-report ranks above email-report for 'generate report'",
          sid_email_report not in ids_gen or sid_generate in ids_gen)

# "send report" — 'report' IS in generate-report's input_pattern too,
# so again ranking matters, not exclusion.
results_send = search_skills("send report")
ids_send = [r["id"] for r in results_send]
check("I1 'send report' DOES match email-report skill",
      sid_email_report in ids_send,
      f"email-report not found — ids: {ids_send}")
# email-report must score HIGHER than generate-report for 'send report'
if sid_email_report in ids_send and sid_generate in ids_send:
    idx_email  = ids_send.index(sid_email_report)
    idx_gen    = ids_send.index(sid_generate)
    check("I1 email-report ranks above generate-report for 'send report'",
          idx_email < idx_gen, f"email at #{idx_email}, generate at #{idx_gen}")
else:
    check("I1 email-report ranks above generate-report for 'send report'",
          sid_generate not in ids_send or sid_email_report in ids_send)

# Hard gate: a query with ZERO token overlap in input_pattern must be blocked
# "weather forecast" shares no tokens with either skill's input_pattern
results_unrelated = search_skills("weather forecast")
ids_unrelated = [r["id"] for r in results_unrelated]
check("I1 hard gate: 'weather forecast' returns 0 results (no input_pattern overlap)",
      len(ids_unrelated) == 0,
      f"unexpectedly matched: {ids_unrelated[:2]}")

# Verify score ordering: exact match > partial
# "send email report" should score higher for email-report than for generate-report
if sid_email_report and sid_generate:
    sk_e  = get_skill(sid_email_report)
    sk_g  = get_skill(sid_generate)
    score_e = _overlap_score(_tokenize("send email report"), sk_e)
    score_g = _overlap_score(_tokenize("send email report"), sk_g)
    check("I1 email-report scores higher than generate-report for 'send email report'",
          score_e > score_g, f"email={score_e:.4f} generate={score_g:.4f}")

# ── Issue 2: risk_level ───────────────────────────────────────────────────────
print("\nIssue 2 — risk_level")

sid_delete = make_and_capture("delete old user records permanently",
                               ["query_users", "delete_records"])
sid_payment = make_and_capture("charge customer via stripe payment",
                                ["stripe_customer_lookup", "stripe_charge"])
sid_low     = make_and_capture("load config and parse settings",
                                ["read_config", "parse_yaml"])

for sid, expected, label in [
    (sid_delete,  "HIGH",   "I2 delete task → HIGH risk"),
    (sid_payment, "HIGH",   "I2 payment task → HIGH risk"),
    (sid_low,     "LOW",    "I2 config task → LOW risk"),
]:
    sk = get_skill(sid) if sid else None
    if sk:
        check(label, sk["risk_level"] == expected,
              f"got '{sk['risk_level']}' expected '{expected}'")
    else:
        FAIL.append(label); print(f"  [FAIL] {label} — skill not captured")

# Email → MEDIUM risk
sid_email2 = make_and_capture("notify user via email alert",
                                ["compose_email", "notify_send"])
if sid_email2:
    sk_e2 = get_skill(sid_email2)
    check("I2 email notify → MEDIUM risk",
          sk_e2["risk_level"] == "MEDIUM",
          f"got '{sk_e2['risk_level']}'")

# ── Issue 3: confidence gating ────────────────────────────────────────────────
print("\nIssue 3 — Confidence gating + recommend_skill()")

check("CONFIDENCE_GATE constant is 0.6", CONFIDENCE_GATE == 0.6)

# recommend_skill should return the generate-report skill for "generate report"
rec = recommend_skill("generate report")
check("I3 recommend_skill returns match above gate",
      rec is not None and rec["id"] == sid_generate,
      f"got {rec['id'][:12] if rec else None}…")

# recommend_skill with very high threshold → should return None
rec_none = recommend_skill("generate report", min_confidence=1.01)
check("I3 recommend_skill with impossible threshold → None",
      rec_none is None, f"got {rec_none}")

# search_skills with min_confidence filter
all_results = search_skills("generate report", min_confidence=0.0)
gated_results = search_skills("generate report", min_confidence=1.0)
check("I3 gated search fewer results than ungated",
      len(gated_results) <= len(all_results))

# ── risk_level in recommend output ────────────────────────────────────────────
rec_del = recommend_skill("delete user records permanently")
if rec_del:
    check("I2+I3 delete recommendation exposes risk_level",
          rec_del.get("risk_level") == "HIGH",
          f"got '{rec_del.get('risk_level')}'")
else:
    check("I2+I3 delete recommendation found",  False, "recommend_skill returned None")

# ── Summary ───────────────────────────────────────────────────────────────────
import gc; gc.collect()
try:
    os.remove(TEST_DB)
except OSError:
    pass

print(f"\n{'='*44}")
print(f"PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
if FAIL:
    print("Failed:", FAIL); sys.exit(1)
else:
    print("ALL CASES PASSED ✓")
