import json
import os
import subprocess
from pathlib import Path
from gateway import UnifiedGateway

class BatonOrchestrator:
    """
    Implements the 'Baton Passing' pattern.
    Splits a complex goal into sub-batons and dispatches workers.
    """
    
    def __init__(self, provider, key, model):
        self.gateway = UnifiedGateway(provider, key)
        self.model = model
        self.baton_dir = Path("temp_batons")
        self.baton_dir.mkdir(exist_ok=True)

    async def plan_and_execute(self, objective: str):
        print(f"Orchestrating Objective: {objective}")
        
        # 1. Break down the task
        if self.gateway.api_key == "dummy":
            print("  [DUMMY MODE] Using hardcoded plan.")
            plan = [
                {"id": 1, "task": "Review security docs", "file_context": "docs/SAFE_SHELL.md"},
                {"id": 2, "task": "Propose TUI enhancement", "file_context": "scripts/tui_shell.py"}
            ]
        else:
            planning_prompt = (
                f"Break down this objective into 2-3 independent sub-tasks: '{objective}'. "
                "Return ONLY a JSON list of objects with 'id', 'task', and 'file_context'."
            )
            plan_str = self.gateway.chat(self.model, planning_prompt)
            
            try:
                plan_str = plan_str.strip().replace("```json", "").replace("```", "")
                plan = json.loads(plan_str)
            except:
                print("Planning failed. AI did not return valid JSON.")
                return

        # 2. Dispatch subagents with Batons
        results = []
        for task in plan:
            baton_path = self.baton_dir / f"baton_{task['id']}.json"
            baton_data = {
                "id": task['id'],
                "task": task['task'],
                "context": task.get('file_context', ""),
                "status": "pending",
                "output": ""
            }
            baton_path.write_text(json.dumps(baton_data, indent=2))
            
            print(f"  - Dispatching Worker for Task {task['id']}: {task['task']}")
            result = await self.execute_task_with_worker(baton_path)
            results.append(result)
            
        # 3. Final Synthesis
        if self.gateway.api_key == "dummy":
            final_report = "Final Synthesis [DUMMY]: Tasks completed. Suggested improvement: Add a 'Session History' panel to the TUI."
        else:
            synthesis_prompt = (
                f"Objective: {objective}\n"
                f"Sub-task results: {json.dumps(results, indent=2)}\n"
                "Synthesize these results into a final report."
            )
            final_report = self.gateway.chat(self.model, synthesis_prompt)
        
        print("\nFinal Synthesis Complete:")
        print(final_report)

    async def execute_task_with_worker(self, baton_path: Path):
        """
        Launches a real independent process for the worker.
        """
        print(f"  - Launching process: python scripts/agent_worker.py {baton_path}")
        
        # We use subprocess.run for simplicity in this demo, but could use asyncio.create_subprocess_exec
        process = subprocess.run(
            ["python", "scripts/agent_worker.py", str(baton_path)],
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            print(f"    ERROR: Process Error: {process.stderr}")
            return {"status": "failed", "error": process.stderr}
            
        # Re-read the updated baton
        return json.loads(baton_path.read_text())

if __name__ == "__main__":
    import asyncio
    # For demo: python scripts/baton_orchestrator.py "Refactor the TUI and update the docs"
    import sys
    obj = sys.argv[1] if len(sys.argv) > 1 else "Refactor the TUI shell and update the README"
    
    # Using environment variables for keys if available
    provider = os.getenv("AI_PROVIDER", "nvidia")
    key = os.getenv("AI_KEY", "dummy")
    model = os.getenv("AI_MODEL", "llama-3")
    
    orch = BatonOrchestrator(provider, key, model)
    asyncio.run(orch.plan_and_execute(obj))
