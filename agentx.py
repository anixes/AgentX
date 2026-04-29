"""
AgentX — Unified CLI Entry Point
=================================
Usage:
  agentx              → Start the interactive SafeShell TUI (default)
  agentx dash         → Launch API bridge + open dashboard
  agentx run [--bg]   → Run a SwarmEngine mission (optionally in background)
  agentx status       → Show swarm health, active batons, territories
  agentx doctor       → Run system health checks and diagnostics
  agentx memory       → Manage AJA secretary memory
  agentx message      → Manage AJA outbound drafts
  agentx review       → Run executive reviews
  agentx worker       → Manage worker registry & get recommendations
  agentx help         → Show this help message
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path
from scripts.secretary_memory import (
    SecretaryMemory,
    format_communication_for_mobile,
    format_tasks_for_mobile,
    parse_communication_intent,
    parse_task_intent,
)

# ---------------------------------------------------------------------------
# Resolve python executable portably
# ---------------------------------------------------------------------------
PYTHON = sys.executable
PROJECT_ROOT = Path(__file__).resolve().parent
BATON_DIR = PROJECT_ROOT / "temp_batons"
RUNTIME_STATE = PROJECT_ROOT / ".agentx" / "runtime-state.json"
SECRETARY_DB = PROJECT_ROOT / ".agentx" / "aja_secretary.sqlite3"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_ui():
    """Start the interactive SafeShell TUI."""
    print("[*] Starting SafeShell TUI...")
    subprocess.run([PYTHON, str(PROJECT_ROOT / "scripts" / "tui_shell.py")])


def cmd_dash():
    """Launch API Bridge (background) + Dashboard dev server."""
    print("[*] Starting API Bridge on :8000 ...")
    bridge = subprocess.Popen(
        [PYTHON, str(PROJECT_ROOT / "scripts" / "api_bridge.py")],
        cwd=str(PROJECT_ROOT),
    )

    print("[*] Starting Dashboard on :5173 ...")
    try:
        subprocess.run(
            ["npm", "run", "dev"],
            cwd=str(PROJECT_ROOT / "dashboard"),
            shell=True,
        )
    except KeyboardInterrupt:
        pass
    finally:
        bridge.terminate()
        print("\n[OK] Shutdown complete.")


def cmd_run(objective: str, background: bool = False):
    """Delegate an objective to the SwarmEngine (auto-picks mode)."""
    print(f'[>] Delegating mission to SwarmEngine: "{objective}"')
    
    cmd = [
        PYTHON,
        str(PROJECT_ROOT / "scripts" / "swarm_engine.py"),
        "--mode", "baton",
        "--objective", objective,
    ]
    
    if background:
        print("[*] Running in background mode...")
        log_file = PROJECT_ROOT / ".agentx" / "bg_run.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\\n--- New Run: {time.ctime()} ---\\n")
            subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        print(f"[OK] Background task started. Logs: {log_file.relative_to(PROJECT_ROOT) if PROJECT_ROOT in log_file.parents else log_file}")
    else:
        subprocess.run(cmd)


def cmd_status():
    """Print a concise dashboard of swarm health."""
    # 1. Territories
    territories = ["src/prod", "src/vault", "src/tools"]
    print("\n+--------------------+----------+----------+")
    print("|          AgentX Swarm Status             |")
    print("+--------------------+----------+----------+")
    print("| Territory          | Status   | Load     |")
    print("+--------------------+----------+----------+")
    for t in territories:
        p = PROJECT_ROOT / t
        baton = p / ".baton"
        status = "healing" if baton.exists() else "stable"
        count = len(list(p.glob("*"))) if p.exists() else 0
        load = f"{(count * 15) % 100}%"
        print(f"| {t:<18} | {status:<8} | {load:<8} |")
    print("+--------------------+----------+----------+")

    # 2. Active Batons
    if BATON_DIR.exists():
        baton_files = sorted(BATON_DIR.glob("*.json"))
        if baton_files:
            print(f"[BATON] Active Batons ({len(baton_files)}):")
            for bf in baton_files:
                try:
                    b = json.loads(bf.read_text(encoding="utf-8"))
                    stage = b.get("stage", "unknown")
                    task = b.get("task", bf.stem)
                    progress = b.get("progress", 0)
                    print(f"   - {task} [{stage}] {progress}%")
                except Exception:
                    print(f"   - {bf.stem} [invalid]")
        else:
            print("\n[BATON] No active batons.")
    else:
        print("\n🎯 No active batons.")

    # 3. Pending Approval
    if RUNTIME_STATE.exists():
        try:
            state = json.loads(RUNTIME_STATE.read_text(encoding="utf-8"))
            pending = state.get("pendingApproval")
            if pending:
                tool = pending.get("tool", "unknown")
                print(f"\n[!] Pending Approval: {tool}")
                print(f"   Run 'agentx approve' or 'agentx deny' to respond.")
            else:
                print("\n[OK] No pending approvals.")
        except Exception:
            print("\n✅ No pending approvals.")
    else:
        print("\n✅ No pending approvals.")


def cmd_doctor():
    """Run system health checks and diagnostics."""
    print("\n+--------------------------------------------------+")
    print("|               AgentX System Doctor                 |")
    print("+--------------------------------------------------+\n")
    
    issues = 0
    
    # 1. Check Python version
    import platform
    py_version = platform.python_version()
    print(f"[*] Python Version: {py_version} ", end="")
    if sys.version_info >= (3, 9):
        print("[OK]")
    else:
        print("[WARN] (Recommended 3.9+)")
        issues += 1
        
    # 2. Check Node & NPM (for dashboard)
    import shutil
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    print(f"[*] Node.js installed: ", end="")
    if node_path:
        print("[OK]")
    else:
        print("[WARN] Node.js is required for the dashboard.")
        issues += 1
        
    print(f"[*] npm installed: ", end="")
    if npm_path:
        print("[OK]")
    else:
        print("[WARN] npm is required for the dashboard.")
        issues += 1
        
    # 3. Check Configuration
    cfg = load_config()
    print(f"[*] Configuration (.agentx/config.json): ", end="")
    if cfg.get("api_key") and cfg.get("provider"):
        print(f"[OK] (Provider: {cfg['provider']})")
    else:
        print("[WARN] Missing API key or provider. Run 'agentx setup'.")
        issues += 1
        
    # 4. Check Territories
    print(f"[*] Project Directories: ", end="")
    missing_dirs = []
    for d in ["temp_batons", "src/prod", "src/vault", "src/tools"]:
        if not (PROJECT_ROOT / d).exists():
            missing_dirs.append(d)
    
    if not missing_dirs:
        print("[OK]")
    else:
        print(f"[WARN] Missing directories: {', '.join(missing_dirs)}")
        issues += 1

    # 5. Check Ollama
    print(f"[*] Ollama Service: ", end="")
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json().get('models', [])]
            print(f"[OK] ({len(models)} models found)")
        else:
            print("[WARN] Ollama API returned error. Is it running?")
            issues += 1
    except Exception:
        print("[WARN] Could not connect to Ollama. Is it running on :11434?")
        issues += 1

    print("\n+--------------------------------------------------+")
    if issues == 0:
        print("[OK] System is healthy and ready to run.")
    else:
        print(f"[WARN] Found {issues} warning(s). AgentX may have limited functionality.")
    print("+--------------------------------------------------+\n")


def cmd_memory(*args):
    """Manage AJA's structured secretary memory."""
    memory = SecretaryMemory(SECRETARY_DB)

    if not args or args[0] in {"list", "tasks"}:
        tasks = memory.list_tasks(statuses=["pending", "active", "blocked"], limit=50)
        print("\n--- AJA Secretary Memory ---")
        print(format_tasks_for_mobile(tasks, memory.review(escalate=False)))
        print("----------------------------\n")
        print("Usage:")
        print("  agentx memory add \"follow up with recruiter next Tuesday\"")
        print("  agentx memory list")
        print("  agentx memory review")
        print("  agentx memory complete <task_id>")
        print("  agentx memory archive <task_id>")
        return

    command = args[0].lower()
    if command == "add" and len(args) >= 2:
        text = " ".join(args[1:])
        task_data = parse_task_intent(text, source="CLI", owner="AJA") or {
            "title": text,
            "context": text,
            "source": "CLI",
            "owner": "AJA",
            "priority": "medium",
            "status": "pending",
            "communication_history": [{"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "type": "source", "message": text}],
        }
        task = memory.create_task(task_data)
        print(f"[OK] Saved secretary task: {task['title']}")
        print(f"     ID      : {task['task_id']}")
        print(f"     Due     : {task.get('due_date') or '(none)'}")
        print(f"     Priority: {task['priority']}")
    elif command == "review":
        review = memory.review(escalate=True)
        tasks = memory.list_tasks(statuses=["pending", "active", "blocked"], limit=50)
        print(format_tasks_for_mobile(tasks, review))
    elif command == "complete" and len(args) == 2:
        try:
            task = memory.complete_task(args[1])
            print(f"[OK] Completed: {task['title']} ({task['status']})")
        except KeyError:
            print(f"[X] Task not found: {args[1]}")
    elif command == "archive" and len(args) == 2:
        try:
            task = memory.archive_task(args[1])
            print(f"[OK] Archived: {task['title']}")
        except KeyError:
            print(f"[X] Task not found: {args[1]}")
    else:
        print("[X] Invalid memory command.")
        print("Usage: agentx memory add|list|review|complete|archive")


def cmd_message(*args):
    """Manage AJA outbound communication drafts."""
    memory = SecretaryMemory(SECRETARY_DB)

    if not args or args[0] in {"list", "drafts"}:
        print(memory.communication_summary())
        print("\nUsage:")
        print("  agentx message draft \"draft recruiter follow-up\"")
        print("  agentx message approve <message_id>")
        print("  agentx message reject <message_id>")
        return

    command = args[0].lower()
    if command == "draft" and len(args) >= 2:
        text = " ".join(args[1:])
        message_data = parse_communication_intent(text, source="CLI") or {
            "recipient": "recipient",
            "channel": "draft",
            "subject": "Draft",
            "draft_content": text,
            "tone_profile": "professional",
            "approval_required": True,
            "approval_status": "pending",
            "communication_history": [{"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "type": "source", "message": text}],
        }
        message = memory.create_communication(message_data)
        print(format_communication_for_mobile(message))
    elif command == "approve" and len(args) == 2:
        try:
            message = memory.approve_communication(args[1])
            print(f"[OK] Approved message {message['message_id']}. It is ready, not auto-sent.")
        except KeyError:
            print(f"[X] Message not found: {args[1]}")
    elif command == "reject" and len(args) >= 2:
        reason = " ".join(args[2:]) if len(args) > 2 else ""
        try:
            message = memory.reject_communication(args[1], reason)
            print(f"[OK] Rejected message {message['message_id']}.")
        except KeyError:
            print(f"[X] Message not found: {args[1]}")
    else:
        print("[X] Invalid message command.")
        print("Usage: agentx message draft|list|approve|reject")


def cmd_review(*args):
    """Run AJA executive reviews."""
    memory = SecretaryMemory(SECRETARY_DB)
    kind = args[0].lower() if args else "morning"
    if kind not in {"morning", "night", "weekly"}:
        print("[X] Review must be morning, night, or weekly.")
        return
    print(memory.generate_executive_review(kind, escalate=True)["summary"])


def cmd_worker(*args):
    """Manage the Worker Capability Registry."""
    memory = SecretaryMemory(SECRETARY_DB)

    if not args or args[0] in {"list", "ls"}:
        workers = memory.list_workers()
        if not workers:
            print("\n[!] No workers registered. Run 'agentx worker seed' to populate defaults.")
            _show_worker_help()
            return
        print("\n+" + "-" * 70 + "+")
        print("|" + "  Worker Capability Registry".ljust(70) + "|")
        print("+" + "-" * 70 + "+")
        print(f"| {'ID':<22} | {'Name':<20} | {'Status':<12} | {'Speed':<7} | {'Rel':>4} |")
        print("+" + "-" * 70 + "+")
        for w in workers:
            sid = w['worker_id'][:20]
            name = w['worker_name'][:18]
            status = w['availability_status'][:10]
            speed = w['execution_speed'][:6]
            rel = f"{int(w['reliability_score'] * 100)}%"
            print(f"| {sid:<22} | {name:<20} | {status:<12} | {speed:<7} | {rel:>4} |")
        print("+" + "-" * 70 + "+")
        print(f"  {len(workers)} worker(s) total")
        _show_worker_help()
        return

    command = args[0].lower()

    if command == "get" and len(args) >= 2:
        worker = memory.get_worker(args[1])
        if not worker:
            print(f"[X] Worker not found: {args[1]}")
            return
        print(f"\n--- Worker: {worker['worker_name']} ---")
        print(f"  ID            : {worker['worker_id']}")
        print(f"  Type          : {worker['worker_type']}")
        print(f"  Status        : {worker['availability_status']}")
        print(f"  Speed         : {worker['execution_speed']}")
        print(f"  Reliability   : {int(worker['reliability_score'] * 100)}%")
        print(f"  Cost          : {worker['cost_profile']}")
        print(f"  Strengths     : {', '.join(worker['primary_strengths'])}")
        if worker['weak_areas']:
            print(f"  Weak areas    : {', '.join(worker['weak_areas'])}")
        print(f"  Task types    : {', '.join(worker['preferred_task_types'])}")
        if worker['blocked_task_types']:
            print(f"  Blocked       : {', '.join(worker['blocked_task_types'])}")
        caps = []
        if worker['supports_tests']: caps.append('tests')
        if worker['supports_git_operations']: caps.append('git')
        if worker['supports_deployment']: caps.append('deploy')
        if worker['supports_plan_mode']: caps.append('plan_mode')
        print(f"  Capabilities  : {', '.join(caps) or '(none)'}")
        if worker['total_tasks_executed'] > 0:
            print(f"  Executed      : {worker['total_tasks_executed']} tasks ({worker['historical_success_rate']}% success)")
        if worker['recommended_use_cases']:
            print(f"  Use cases     :")
            for uc in worker['recommended_use_cases']:
                print(f"                  - {uc}")

    elif command == "seed":
        seeded = memory.seed_default_workers()
        print(f"[OK] Seeded {len(seeded)} new worker(s).")
        if seeded:
            for w in seeded:
                print(f"  + {w['worker_name']} ({w['worker_id']})")
        else:
            print("  (All defaults already exist.)")

    elif command in {"recommend", "rec"} and len(args) >= 2:
        objective = " ".join(args[1:])
        from scripts.api_bridge import recommend_workers_for_task
        result = recommend_workers_for_task(memory, objective)
        recs = result.get("recommended", [])
        analysis = result.get("analysis", {})
        cautions = result.get("cautions", [])

        print(f"\n--- Worker Recommendation ---")
        print(f"  Objective    : {analysis.get('objective', objective)}")
        print(f"  Inferred     : {', '.join(analysis.get('inferred_types', []))}")
        print(f"  Risk Level   : {analysis.get('risk_level', '?')}")
        print(f"  Speed Need   : {analysis.get('speed_need', '?')}")

        if cautions:
            print(f"\n  Cautions:")
            for c in cautions:
                print(f"    [!] {c}")

        if not recs:
            print("\n  No workers available for this task. Run 'agentx worker seed' first.")
            return

        print(f"\n  Ranked Recommendations ({len(recs)}):")
        print(f"  {'#':>3}  {'Score':>5}  {'Worker':<22}  {'Speed':<8}  {'Cost':<14}  Reasons")
        print(f"  {'---':>3}  {'-----':>5}  {'------':<22}  {'-----':<8}  {'----':<14}  -------")
        for i, rec in enumerate(recs, 1):
            marker = " *" if i == 1 else "  "
            reasons_str = "; ".join(rec.get('reasons', [])[:2])
            print(f"{marker}{i:>2}  {rec['recommendation_score']:>5.0f}  {rec['worker_name']:<22}  {rec['execution_speed']:<8}  {rec['cost_profile']:<14}  {reasons_str}")
            if rec.get('cautions'):
                for c in rec['cautions']:
                    print(f"        {'':>5}  {'':>22}  [!] {c}")

    elif command == "log" and len(args) >= 3:
        worker_id = args[1]
        outcome = args[2] if args[2] in {"success", "failure"} else "success"
        task_type = args[3] if len(args) > 3 else "general"
        desc = " ".join(args[4:]) if len(args) > 4 else ""
        result = memory.log_worker_execution({
            "worker_id": worker_id,
            "outcome": outcome,
            "task_type": task_type,
            "task_description": desc,
        })
        print(f"[OK] Logged {outcome} for {worker_id} ({result['log_id']})")

    elif command in {"remove", "delete", "rm"} and len(args) >= 2:
        worker_id = args[1]
        existing = memory.get_worker(worker_id)
        if not existing:
            print(f"[X] Worker not found: {worker_id}")
            return
        memory.delete_worker(worker_id)
        print(f"[OK] Removed worker: {existing['worker_name']} ({worker_id})")

    elif command == "history" and len(args) >= 2:
        worker_id = args[1]
        hist = memory.get_worker_execution_history(worker_id, limit=20)
        if not hist:
            print(f"  No execution history for {worker_id}.")
            return
        print(f"\n--- Execution History: {worker_id} ---")
        for h in hist:
            outcome_mark = "[OK]" if h.get('outcome') == 'success' else "[FAIL]"
            print(f"  {outcome_mark} {h.get('task_type', '?')}: {h.get('task_description', '(no desc)')[:50]}  ({h.get('created_at', '')})")

    else:
        print("[X] Invalid worker command.")
        _show_worker_help()


def _show_worker_help():
    print("\nUsage:")
    print("  agentx worker list                            -- List all workers")
    print("  agentx worker get <worker_id>                 -- Show worker details")
    print("  agentx worker seed                            -- Seed default profiles")
    print('  agentx worker recommend "fix login bug"        -- Get AJA recommendations')
    print("  agentx worker log <id> success|failure <type> -- Log execution outcome")
    print("  agentx worker history <id>                    -- Show execution history")
    print("  agentx worker remove <id>                     -- Remove a worker")


CONFIG_PATH = PROJECT_ROOT / ".agentx" / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"provider": "openrouter", "api_key": "", "model": ""}


def save_config(data: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def cmd_setup():
    """Interactive wizard to configure AI provider, key, and model."""
    providers_file = PROJECT_ROOT / "providers.json"
    try:
        providers = json.loads(providers_file.read_text(encoding="utf-8"))
    except Exception:
        providers = {"openrouter": "https://openrouter.ai/api/v1"}

    provider_names = list(providers.keys())
    cfg = load_config()

    print("\n--- AgentX Setup ---\n")
    print("Available providers:")
    for i, name in enumerate(provider_names, 1):
        marker = " (current)" if name == cfg.get("provider") else ""
        print(f"  {i}. {name}{marker}")

    choice = input(f"\nSelect provider [1-{len(provider_names)}] (Enter to keep current): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(provider_names):
        cfg["provider"] = provider_names[int(choice) - 1]

    print(f"\nProvider: {cfg['provider']}")

    current_key = cfg.get("api_key", "")
    key_hint = f" (current: ...{current_key[-4:]})" if len(current_key) > 4 else ""
    new_key = input(f"API Key{key_hint} (Enter to keep current): ").strip()
    if new_key:
        cfg["api_key"] = new_key

    # Suggest popular models per provider
    model_suggestions = {
        "openrouter": "anthropic/claude-sonnet-4, google/gemini-2.5-flash, meta-llama/llama-4-maverick",
        "groq": "llama-3.3-70b-versatile, mixtral-8x7b-32768",
        "nvidia": "nvidia/llama-3.1-nemotron-70b-instruct",
        "together": "meta-llama/Llama-3-70b-chat-hf",
        "openai": "gpt-4o-mini, gpt-4o",
        "ollama": "phi4-mini, qwen2.5:3b, llama3.2:3b, gemma2:2b",
    }
    suggestions = model_suggestions.get(cfg["provider"], "")
    current_model = cfg.get("model", "")
    model_hint = f" (current: {current_model})" if current_model else ""

    if suggestions:
        print(f"\nPopular models for {cfg['provider']}:")
        print(f"  {suggestions}")

    new_model = input(f"Model{model_hint} (Enter to keep current): ").strip()
    if new_model:
        cfg["model"] = new_model

    save_config(cfg)
    print(f"\n[OK] Configuration saved to .agentx/config.json")
    print(f"     Provider : {cfg['provider']}")
    print(f"     Model    : {cfg.get('model', '(not set)')}")
    print(f"     API Key  : {'set' if cfg.get('api_key') else 'NOT SET'}")


def show_help():
    print("""
+-----------------------------------------------------------+
|                  AgentX -- Unified CLI                     |
+-----------------------------------------------------------+
|                                                           |
|  agentx              Start the interactive SafeShell TUI  |
|  agentx dash         Launch Dashboard + API Bridge        |
|  agentx run [--bg]   Run a SwarmEngine mission            |
|  agentx status       Show swarm health & active batons    |
|  agentx setup        Configure AI provider & API key      |
|  agentx doctor       Run system health diagnostics        |
|  agentx memory       Manage AJA secretary memory          |
|  agentx message      Manage outbound communication drafts |
|  agentx review       Run morning/night/weekly reviews     |
|  agentx worker       Worker registry & recommendations    |
|  agentx help         Show this help message               |
|                                                           |
+-----------------------------------------------------------+
    """)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args:
        cmd_ui()
        return

    command = args[0].lower()

    if command == "help":
        show_help()
    elif command == "dash":
        cmd_dash()
    elif command == "run":
        bg = False
        if "--bg" in args:
            bg = True
            args.remove("--bg")
            
        if len(args) < 2:
            print(f"[X] Usage: agentx run [--bg] \"your objective here\"")
            sys.exit(1)
        cmd_run(" ".join(args[1:]), background=bg)
    elif command == "status":
        cmd_status()
    elif command == "setup":
        cmd_setup()
    elif command == "doctor":
        cmd_doctor()
    elif command == "memory":
        cmd_memory(*args[1:])
    elif command == "message":
        cmd_message(*args[1:])
    elif command == "review":
        cmd_review(*args[1:])
    elif command == "worker":
        cmd_worker(*args[1:])
    elif command == "ui":
        cmd_ui()
    else:
        print(f"[X] Unknown command: '{command}'")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
