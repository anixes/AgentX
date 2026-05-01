import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from agentx.runtime.session import session_manager
from agentx.runtime.event_bus import bus, EVENTS

app = FastAPI(title="AgentX Jarvis Server")

class TaskRequest(BaseModel):
    user_id: str
    task: str

class InterruptRequest(BaseModel):
    user_id: str

# In-memory queue for task processing
task_queue = asyncio.Queue()

@app.post("/task")
async def submit_task(req: TaskRequest):
    session = session_manager.get_or_create(req.user_id)
    session.log_interaction("user", req.task)
    await task_queue.put({"session": session, "task": req.task})
    return {"status": "queued", "session_id": session.session_id}

@app.post("/interrupt")
async def interrupt_task(req: InterruptRequest):
    session = session_manager.get_or_create(req.user_id)
    session.interrupt()
    return {"status": "interrupted"}

# Connection manager for streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Hook EventBus into WebSocket broadcast
def get_event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None

def broadcast_event(event_name, node):
    loop = get_event_loop()
    msg = json.dumps({"event": event_name, "node_id": getattr(node, 'id', 'unknown'), "tool": getattr(node, 'tool', 'unknown')})
    if loop and loop.is_running():
        asyncio.create_task(manager.broadcast(msg))
    else:
        # Fallback if no loop is running in thread
        pass

bus.subscribe(EVENTS["NODE_STARTED"], lambda n: broadcast_event("NODE_STARTED", n))
bus.subscribe(EVENTS["NODE_SUCCESS"], lambda n: broadcast_event("NODE_SUCCESS", n))
bus.subscribe(EVENTS["NODE_FAILED"], lambda n: broadcast_event("NODE_FAILED", n))
bus.subscribe(EVENTS["ROLLBACK"], lambda n: broadcast_event("ROLLBACK", n))
bus.subscribe(EVENTS["REPAIR"], lambda n: broadcast_event("REPAIR", n))
