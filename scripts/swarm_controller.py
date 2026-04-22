import os
import subprocess
import time
from pathlib import Path

# Config
PYTHON = r"D:\ANACONDA py\python.exe"

class SwarmController:
    """
    The Hive Mind of AgentX. Dispatches healing workers across the project.
    """
    def __init__(self):
        self.territories = [
            "src/prod",
            "src/vault",
            "src/tools"
        ]
        self.workers = {}

    def deploy_swarm(self):
        print("--- AGENTX SWARM DEPLOYMENT INITIATED ---")
        # Prepare the environment with PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()

        for territory in self.territories:
            if os.path.exists(territory):
                print(f"[-] Dispatching Healing Worker to territory: {territory}")
                # We launch a dedicated worker for each territory
                process = subprocess.Popen(
                    [PYTHON, "scripts/self_healer.py", territory],
                    env=env
                )
                self.workers[territory] = process
        
        print(f"\n[+] Swarm Active: {len(self.workers)} agents monitoring the system.")
        print("Press Ctrl+C to recall the swarm.")

    def monitor_swarm(self):
        try:
            while True:
                # In a real swarm, we would check if workers died and respawn them
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n[!] Recalling the swarm. Terminating all agents...")
            for territory, process in self.workers.items():
                process.terminate()
            print("[+] Swarm offline.")

if __name__ == "__main__":
    swarm = SwarmController()
    swarm.deploy_swarm()
    swarm.monitor_swarm()
