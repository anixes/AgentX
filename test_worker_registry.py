"""Quick smoke test for Phase 6.1 Worker Registry."""
import sys
sys.path.insert(0, ".")
from scripts.secretary_memory import SecretaryMemory

m = SecretaryMemory()

# Seed defaults
workers = m.seed_default_workers()
print(f"Seeded {len(workers)} new workers")

# List all
all_w = m.list_workers()
print(f"Total workers: {len(all_w)}")
for w in all_w:
    wid = w["worker_id"]
    name = w["worker_name"]
    status = w["availability_status"]
    speed = w["execution_speed"]
    rel = w["reliability_score"]
    print(f"  {wid}: {name} | {status} | speed={speed} | reliability={rel}")

# Get one
copilot = m.get_worker("github-copilot-cli")
if copilot:
    print(f"\nGot worker: {copilot['worker_name']}")
    print(f"  Strengths: {copilot['primary_strengths']}")
    print(f"  Supports tests: {copilot['supports_tests']}")
    print(f"  Supports git: {copilot['supports_git_operations']}")

# Log execution
log = m.log_worker_execution({
    "worker_id": "github-copilot-cli",
    "task_type": "code",
    "task_description": "Test task",
    "outcome": "success",
    "duration_seconds": 120,
})
print(f"\nLogged execution: {log}")

# Check updated stats
updated = m.get_worker("github-copilot-cli")
if updated:
    print(f"  Total executed: {updated['total_tasks_executed']}")
    print(f"  Success rate: {updated['historical_success_rate']}%")

print("\n[OK] Worker Registry smoke test passed.")
