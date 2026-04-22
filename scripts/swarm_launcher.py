import concurrent.futures
import subprocess
import os
import json
import argparse

class SwarmLauncher:
    """
    Orchestrates multiple AI agents in parallel using the Unified Gateway.
    Mimics Claude's 'Teammate' swarm architecture.
    """

    def __init__(self, providers: list):
        self.providers = providers # List of providers to load-balance across

    def run_agent(self, agent_id: int, task: str, provider: str):
        """Launches a single agent process."""
        print(f"🐝 [Agent {agent_id}] Starting task on {provider.upper()}...")
        
        # We call our existing gateway.py as a separate process
        cmd = [
            "python", "scripts/gateway.py", 
            "--provider", provider,
            task
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {
                "agent_id": agent_id,
                "provider": provider,
                "status": "success",
                "output": result.stdout.strip()
            }
        except subprocess.CalledProcessError as e:
            return {
                "agent_id": agent_id,
                "provider": provider,
                "status": "failed",
                "error": e.stderr
            }

    def launch_swarm(self, overall_task: str, sub_tasks: list):
        """Launches agents in parallel to handle sub-tasks."""
        print(f"🚀 Launching Swarm with {len(sub_tasks)} agents...")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sub_tasks)) as executor:
            # Map sub-tasks to providers (round-robin)
            future_to_agent = {
                executor.submit(
                    self.run_agent, 
                    i, 
                    sub_tasks[i], 
                    self.providers[i % len(self.providers)]
                ): i for i in range(len(sub_tasks))
            }
            
            for future in concurrent.futures.as_completed(future_to_agent):
                results.append(future.result())
        
        return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch a swarm of agents.")
    parser.add_argument("--task", type=str, required=True, help="The main task description")
    parser.add_argument("--items", type=str, required=True, help="Comma-separated items (e.g. files) to process")
    parser.add_argument("--providers", type=str, default="nvidia,groq", help="Comma-separated providers")
    
    args = parser.parse_args()
    
    items = args.items.split(",")
    providers = args.providers.split(",")
    
    # Split the main task into one sub-task per item
    sub_tasks = [f"{args.task} for item: {item}" for item in items]
    
    launcher = SwarmLauncher(providers)
    swarm_results = launcher.launch_swarm(args.task, sub_tasks)
    
    # Final Aggregation
    print("\n--- 🏁 Swarm Task Completed ---")
    final_report = ""
    for r in sorted(swarm_results, key=lambda x: x['agent_id']):
        if r['status'] == "success":
            print(f"✅ Agent {r['agent_id']} ({r['provider']}) finished.")
            final_report += f"\n### Agent {r['agent_id']} Result:\n{r['output']}\n"
        else:
            print(f"❌ Agent {r['agent_id']} ({r['provider']}) failed.")
            
    with open("swarm_report.md", "w") as f:
        f.write(f"# Swarm Final Report\n\nTask: {args.task}\n\n{final_report}")
    
    print("\n📄 Detailed report saved to 'swarm_report.md'")
