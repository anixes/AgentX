import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.core.gateway import UnifiedGateway


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def append_baton_history(baton, stage, message):
    baton.setdefault("history", []).append(
        {
            "stage": stage,
            "message": message,
            "timestamp": now_iso(),
        }
    )
    baton["updated_at"] = now_iso()


def save_baton(path: Path, baton):
    path.write_text(json.dumps(baton, indent=2))


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

    provider = os.getenv("AI_PROVIDER", "nvidia")
    key = os.getenv("AI_KEY", "dummy")
    model = os.getenv("AI_MODEL", "llama-3")
    gateway = UnifiedGateway(provider, key)

    prompt = (
        f"Context: {baton['context']}\n"
        f"Task: {baton['task']}\n"
        "Execute this task and provide a detailed report of the work completed."
    )

    try:
        baton["status"] = "executing"
        baton["stage"] = "working"
        append_baton_history(baton, "working", "Worker started execution.")
        save_baton(path, baton)

        if gateway.api_key != "dummy":
            output = gateway.chat(model, prompt)
        else:
            output = f"Simulated success for task: {baton['task']}"

        baton["stage"] = "verifying"
        append_baton_history(baton, "verifying", "Worker completed execution and is finalizing the baton.")
        save_baton(path, baton)

        baton["status"] = "completed"
        baton["stage"] = "worker_complete"
        baton["output"] = output
        append_baton_history(baton, "worker_complete", "Worker wrote the final task output.")
        save_baton(path, baton)
        print(f"DONE: Worker {baton['id']} finished.")

    except Exception as e:
        baton["status"] = "failed"
        baton["stage"] = "worker_failed"
        baton["error"] = str(e)
        append_baton_history(baton, "worker_failed", f"Worker raised an exception: {e}")
        save_baton(path, baton)
        print(f"ERROR: Worker {baton['id']} failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_worker.py <baton_path>")
        sys.exit(1)

    asyncio.run(work(sys.argv[1]))
