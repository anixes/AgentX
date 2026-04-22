import sys
import json
import asyncio
import os
from pathlib import Path
from gateway import UnifiedGateway

async def work(baton_path: str):
    """
    The worker entry point.
    Reads a baton file, executes the assigned task, and updates the baton.
    """
    path = Path(baton_path)
    if not path.exists():
        print(f"Error: Baton file {baton_path} not found.")
        return

    baton = json.loads(path.read_text())
    print(f"Worker {baton['id']} started. Task: {baton['task']}")

    # Setup Gateway
    provider = os.getenv("AI_PROVIDER", "nvidia")
    key = os.getenv("AI_KEY", "dummy")
    model = os.getenv("AI_MODEL", "llama-3")
    gateway = UnifiedGateway(provider, key)

    # 1. Execute Task
    prompt = (
        f"Context: {baton['context']}\n"
        f"Task: {baton['task']}\n"
        "Execute this task and provide a detailed report of the work completed."
    )
    
    try:
        if gateway.key != "dummy":
            output = gateway.chat(model, prompt)
        else:
            output = f"Simulated success for task: {baton['task']}"
        
        # 2. Update Baton
        baton["status"] = "completed"
        baton["output"] = output
        path.write_text(json.dumps(baton, indent=2))
        print(f"DONE: Worker {baton['id']} finished.")
        
    except Exception as e:
        baton["status"] = "failed"
        baton["error"] = str(e)
        path.write_text(json.dumps(baton, indent=2))
        print(f"ERROR: Worker {baton['id']} failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_worker.py <baton_path>")
        sys.exit(1)
    
    asyncio.run(work(sys.argv[1]))
