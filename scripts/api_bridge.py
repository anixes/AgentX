import asyncio
import sys
import json
import os
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNTIME_STATE_PATH = Path(".agentx") / "runtime-state.json"
BATON_DIR = Path("temp_batons")
API_TOKEN = os.getenv("AGENTX_API_TOKEN", "dev-token-123")

def verify_token(authorization: str = Header(None)):
    if not authorization or authorization.replace("Bearer ", "") != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def run_runtime_action(action: str):
    try:
        result = subprocess.run(
            ["npx", "tsx", "src/runtime_actions.ts", action],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch runtime action: {exc}") from exc

    payload_raw = (result.stdout or result.stderr).strip()
    try:
        payload = json.loads(payload_raw) if payload_raw else {"ok": result.returncode == 0, "message": ""}
    except json.JSONDecodeError:
        payload = {"ok": result.returncode == 0, "message": payload_raw}

    if result.returncode != 0:
      raise HTTPException(status_code=500, detail=payload.get("message") or "Runtime action failed.")

    return payload


def load_runtime_state():
    if not RUNTIME_STATE_PATH.exists():
        return {"pendingApproval": None, "events": []}

    try:
        return json.loads(RUNTIME_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"pendingApproval": None, "events": []}


def build_status_payload(runtime_state=None):
    territories = []
    monitored_paths = ["src/prod", "src/vault", "src/tools"]
    runtime_state = runtime_state or load_runtime_state()

    for folder in monitored_paths:
        path = Path(folder)
        baton = path / ".baton"
        status = "healing" if baton.exists() else "stable"
        file_count = len(list(path.glob("*"))) if path.exists() else 0
        load = (file_count * 15) % 100

        territories.append(
            {
                "name": folder,
                "status": status,
                "load": f"{load}%",
            }
        )

    pending = runtime_state.get("pendingApproval")
    return {
        "territories": territories,
        "total_files": sum(len(files) for _, _, files in os.walk("src")) if Path("src").exists() else 0,
        "active_agents": len(territories),
        "safety_alerts": 1 if pending else 0,
        "pending_approval": pending,
        "baton_count": len(load_baton_state()),
        "token_stats": runtime_state.get("tokenStats"),
    }


def load_baton_state():
    if not BATON_DIR.exists():
        return []

    batons = []
    for baton_file in sorted(BATON_DIR.glob("*.json")):
        try:
            baton = json.loads(baton_file.read_text(encoding="utf-8"))
            baton["file"] = baton_file.name
            baton["history_count"] = len(baton.get("history", []))
            
            # Extract live telemetry
            baton["progress"] = baton.get("progress", 0)
            baton["last_pulse"] = baton.get("updated_at", time.time())
            
            batons.append(baton)
        except Exception:
            batons.append(
                {
                    "file": baton_file.name,
                    "status": "invalid",
                    "task": baton_file.stem,
                    "error": "Unable to parse baton file.",
                }
            )

    return batons


def build_runtime_snapshot():
    runtime_state = load_runtime_state()
    return {
        "status": build_status_payload(runtime_state),
        "events": runtime_state.get("events", [])[:10],
        "diff": get_diff().get("diff"),
        "history": get_git_history().get("commits", []),
        "batons": load_baton_state(),
    }


@app.get("/status")
def get_status():
    """Returns dynamic engineering and safety status."""
    return build_status_payload()


@app.get("/diff")
def get_diff():
    try:
        diff = subprocess.check_output(["git", "diff", "HEAD"], stderr=subprocess.STDOUT).decode()
        if not diff.strip():
            return {"diff": "// All systems synchronized. No pending structural changes."}
        return {"diff": diff}
    except Exception:
        return {"diff": "// Unable to access structural history."}


@app.get("/git/history")
def get_git_history():
    try:
        output = subprocess.check_output(
            ["git", "log", "-n", "5", "--pretty=format:%h|%an|%ar|%s"],
            stderr=subprocess.STDOUT,
        ).decode()

        commits = []
        for line in output.split("\n"):
            if not line:
                continue
            h, an, ar, s = line.split("|")
            commits.append({"hash": h, "author": an, "time": ar, "subject": s})
        return {"commits": commits}
    except Exception:
        return {"commits": []}


@app.get("/runtime/approvals")
def get_pending_approval():
    state = load_runtime_state()
    return {"pending": state.get("pendingApproval")}


@app.get("/runtime/events")
def get_runtime_events():
    state = load_runtime_state()
    return {"events": state.get("events", [])[:10]}


@app.get("/runtime/batons")
def get_runtime_batons():
    return {"batons": load_baton_state()}


@app.get("/runtime/stream")
async def runtime_stream(request: Request):
    async def event_generator():
        last_payload = None

        while True:
            if await request.is_disconnected():
                break

            snapshot = await asyncio.to_thread(build_runtime_snapshot)
            payload = json.dumps(snapshot)

            if payload != last_payload:
                yield f"data: {payload}\n\n"
                last_payload = payload
            else:
                yield ": keepalive\n\n"

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/runtime/approve", dependencies=[Depends(verify_token)])
def approve_pending():
    state = load_runtime_state()
    if not state.get("pendingApproval"):
        raise HTTPException(status_code=404, detail="There is no pending approval.")
    return run_runtime_action("approve")


@app.post("/runtime/deny", dependencies=[Depends(verify_token)])
def deny_pending():
    state = load_runtime_state()
    if not state.get("pendingApproval"):
        raise HTTPException(status_code=404, detail="There is no pending approval.")
    return run_runtime_action("deny")


@app.post("/swarm/run", dependencies=[Depends(verify_token)])
async def swarm_run(request: Request):
    """Trigger a SwarmEngine mission from the dashboard."""
    body = await request.json()
    objective = body.get("objective", "").strip()
    if not objective:
        raise HTTPException(status_code=400, detail="Missing 'objective' field.")

    try:
        proc = subprocess.Popen(
            [sys.executable, "scripts/swarm_engine.py", "--mode", "baton", "--objective", objective],
            cwd=str(Path(__file__).resolve().parent.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return {"ok": True, "message": f"Mission delegated: {objective}", "pid": proc.pid}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch SwarmEngine: {exc}") from exc


@app.get("/safety/pending")
def get_pending_legacy():
    state = load_runtime_state()
    pending = state.get("pendingApproval")
    return {"pending": [pending] if pending else []}


@app.get("/safety/history")
def get_safety_history():
    state = load_runtime_state()
    return {"events": state.get("events", [])[:10]}


CONFIG_PATH = Path(".agentx") / "config.json"


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


@app.get("/config")
def get_config():
    cfg = load_config()
    # Mask the API key for safety — only show last 4 chars
    key = cfg.get("api_key", "")
    masked = ("*" * max(0, len(key) - 4)) + key[-4:] if len(key) > 4 else key
    return {
        "provider": cfg.get("provider", "openrouter"),
        "api_key_masked": masked,
        "api_key_set": bool(key),
        "model": cfg.get("model", ""),
    }


@app.post("/config", dependencies=[Depends(verify_token)])
async def update_config(request: Request):
    body = await request.json()
    cfg = load_config()

    if "provider" in body:
        cfg["provider"] = body["provider"]
    if "api_key" in body and body["api_key"]:
        cfg["api_key"] = body["api_key"]
    if "model" in body:
        cfg["model"] = body["model"]

    save_config(cfg)
    return {"ok": True, "message": "Configuration saved."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
