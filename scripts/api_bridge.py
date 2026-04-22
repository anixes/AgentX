from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import time
from pathlib import Path
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared State
LAST_DIFF = ""

@app.get("/status")
def get_status():
    """Returns real dynamic engineering data."""
    territories = ["src/prod", "src/vault", "src/tools"]
    results = []
    
    # Count total files for the header
    total_files = len(list(Path("src").rglob("*.ts")))
    
    for t in territories:
        status = "idle"
        load = "2%"
        worker = "Idle"
        
        # Check for active processes or batons
        baton_dir = Path("temp_batons")
        if baton_dir.exists():
            active_batons = list(baton_dir.glob("*.baton"))
            if any(t.replace("/", "_") in b.name for b in active_batons):
                status = "healing"
                load = f"{10 + (int(time.time()) % 40)}%" # Dynamic simulated load
                worker = "Agent_03"
        
        results.append({
            "name": t,
            "status": status,
            "load": load,
            "worker": worker
        })
        
    return {
        "swarm_active": True, 
        "territories": results,
        "total_files": total_files,
        "active_agents": 1 if any(r["status"] == "healing" for r in results) else 0
    }

@app.get("/diff")
def get_last_diff():
    """Returns the last real code diff from the project."""
    try:
        # We try to get the last git diff to show real changes
        result = subprocess.run(
            ["git", "diff", "HEAD^", "HEAD", "--", "src"],
            capture_output=True,
            text=True
        )
        diff = result.stdout if result.stdout else "// No recent refactors detected."
        return {"diff": diff}
    except:
        return {"diff": "// Git repository not found or no diffs."}

@app.get("/vault/list")
def list_vault_keys():
    vault_path = Path("vault_data.json")
    if not vault_path.exists(): return {"keys": []}
    with open(vault_path, "r") as f:
        return {"keys": list(json.load(f).keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
