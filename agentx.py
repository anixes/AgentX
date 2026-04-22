import sys
import subprocess
import os

# Configuration
PYTHON = r"D:\ANACONDA py\python.exe"

def run_ui():
    print("🚀 Launching AgentX SafeShell TUI...")
    subprocess.run([PYTHON, "scripts/tui_shell.py"])

def run_watcher():
    print("👁️ Starting Zero-Token Graph Watcher...")
    subprocess.run([PYTHON, "scripts/graph_watcher.py"])

def run_plan(objective):
    print(f"🏗️ Dispatching Baton Orchestrator for: {objective}")
    subprocess.run([PYTHON, "scripts/baton_orchestrator.py", objective])

def show_help():
    print("""
    AgentX - Security-Hardened Agentic Toolkit
    
    Usage:
      python agentx.py ui          - Start the interactive SafeShell TUI
      python agentx.py watch       - Start the live knowledge graph watcher
      python agentx.py plan \"...\"  - Run a multi-process autonomous task
      python agentx.py audit       - Run a security audit of the codebase
    """)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()
    
    if cmd == "ui":
        run_ui()
    elif cmd == "watch":
        run_watcher()
    elif cmd == "plan":
        if len(sys.argv) < 3:
            print("Error: Please provide an objective. Example: python agentx.py plan \"refactor code\"")
        else:
            run_plan(sys.argv[2])
    else:
        show_help()
