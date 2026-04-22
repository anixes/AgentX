from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from pathlib import Path

app = FastAPI()

# Enable CORS for our React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def get_status():
    """Returns the health of all monitored territories."""
    return {
        "swarm_active": True,
        "territories": [
            {"name": "src/prod", "status": "healthy", "last_heal": "Never"},
            {"name": "src/vault", "status": "healthy", "last_heal": "Never"},
            {"name": "src/tools", "status": "warning", "last_heal": "2 mins ago"}
        ]
    }

@app.get("/vault/list")
def list_vault_keys():
    """Lists keys in the vault (without revealing values)."""
    vault_path = Path("vault_data.json")
    if not vault_path.exists():
        return {"keys": []}
    
    with open(vault_path, "r") as f:
        data = json.load(f)
        return {"keys": list(data.keys())}

@app.post("/command")
def run_command(cmd: dict):
    """Bridge to run safe agent commands via the dashboard."""
    # In a real app, this would call our 'agentx.py' orchestrator
    print(f"Executing intent from Dashboard: {cmd['intent']}")
    return {"status": "intent_received", "action": "processing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
