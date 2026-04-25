"""
AgentX — Unified CLI Entry Point
=================================
Usage:
  agentx              → Start the interactive SafeShell TUI (default)
  agentx dash         → Launch API bridge + open dashboard
  agentx run [--bg]   → Run a SwarmEngine mission (optionally in background)
  agentx status       → Show swarm health, active batons, territories
  agentx doctor       → Run system health checks and diagnostics
  agentx memory       → Manage agent persistent memory
  agentx help         → Show this help message
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve python executable portably
# ---------------------------------------------------------------------------
PYTHON = sys.executable
PROJECT_ROOT = Path(__file__).resolve().parent
BATON_DIR = PROJECT_ROOT / "temp_batons"
RUNTIME_STATE = PROJECT_ROOT / ".agentx" / "runtime-state.json"
MEMORY_FILE = PROJECT_ROOT / ".agentx" / "memory.json"


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
    """Manage persistent memory for the swarm."""
    if not MEMORY_FILE.exists():
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text("{}", encoding="utf-8")
        
    try:
        mem_data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        mem_data = {}
        
    if not args or args[0] == "list":
        print("\n--- AgentX Persistent Memory ---")
        if not mem_data:
            print("  (empty)")
        else:
            for k, v in mem_data.items():
                print(f"  {k}: {v}")
        print("--------------------------------\n")
        print("Usage: agentx memory add <key> <value>")
        print("       agentx memory remove <key>")
        print("       agentx memory clear")
        
    elif args[0] == "add" and len(args) >= 3:
        key = args[1]
        val = " ".join(args[2:])
        mem_data[key] = val
        MEMORY_FILE.write_text(json.dumps(mem_data, indent=2), encoding="utf-8")
        print(f"[OK] Added to memory: '{key}' = '{val}'")
        
    elif args[0] == "remove" and len(args) == 2:
        key = args[1]
        if key in mem_data:
            del mem_data[key]
            MEMORY_FILE.write_text(json.dumps(mem_data, indent=2), encoding="utf-8")
            print(f"[OK] Removed from memory: '{key}'")
        else:
            print(f"[X] Key not found: '{key}'")
            
    elif args[0] == "clear":
        MEMORY_FILE.write_text("{}", encoding="utf-8")
        print("[OK] Memory cleared.")
    else:
        print("[X] Invalid memory command.")


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
|  agentx memory       Manage agent persistent memory       |
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
    elif command == "ui":
        cmd_ui()
    else:
        print(f"[X] Unknown command: '{command}'")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
