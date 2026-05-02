import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from agentx.runtime.session import session_manager
from agentx.runtime.event_bus import bus, EVENTS
import agentx.config

app = FastAPI(title="AgentX Jarvis Server")

class TaskRequest(BaseModel):
    user_id: str
    task: str
    mode: str = "stable"

class InterruptRequest(BaseModel):
    user_id: str

# In-memory queue for task processing
task_queue = asyncio.Queue()

@app.post("/task")
async def submit_task(req: TaskRequest):
    if req.mode == "beta":
        agentx.config.AGENTX_DIVERSITY_BETA = True
    else:
        agentx.config.AGENTX_DIVERSITY_BETA = False
        
    session = session_manager.get_or_create(req.user_id)
    session.log_interaction("user", req.task)
    await task_queue.put({"session": session, "task": req.task})
    return {"status": "queued", "session_id": session.session_id, "mode": req.mode}

class ResumeRequest(BaseModel):
    user_id: str

class ModifyRequest(BaseModel):
    user_id: str
    new_plan_data: dict

@app.post("/interrupt")
async def interrupt_task(req: InterruptRequest):
    session = session_manager.get_or_create(req.user_id)
    session.interrupt()
    return {"status": "interrupted"}

@app.post("/resume")
async def resume_task(req: ResumeRequest):
    session = session_manager.get_or_create(req.user_id)
    session.resume()
    return {"status": "resumed"}

class ApproveRequest(BaseModel):
    user_id: str

@app.post("/approve")
async def approve_node(req: ApproveRequest):
    session = session_manager.get_or_create(req.user_id)
    if session.pending_node:
        session.pending_node.status = "APPROVED"
    session.resume()
    return {"status": "approved"}

class RejectRequest(BaseModel):
    user_id: str

@app.post("/reject")
async def reject_node(req: RejectRequest):
    session = session_manager.get_or_create(req.user_id)
    if session.pending_node:
        session.pending_node.status = "FAILED"
        session.pending_node.error = "User rejected execution."
    session.resume()
    return {"status": "rejected"}

@app.post("/modify")
async def modify_plan(req: ModifyRequest):
    session = session_manager.get_or_create(req.user_id)
    # Basic validation of new plan could happen here
    # Override active plan or checkpoint state
    session.checkpoint = req.new_plan_data
    return {"status": "plan_modified"}

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

from fastapi import Request
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    from agentx.scheduler.telegram import handle_telegram_message
    from agentx.runtime.session import session_manager
    try:
        data = await request.json()
        if "message" in data:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            
            # Fetch session for memory
            session = session_manager.get_or_create(chat_id)
            session.log_interaction("user", text)
            
            # Pass the session context to the message handler
            await handle_telegram_message(text, user_id=chat_id, session=session)
            
            # Note: We do not append the bot's response to the session history here
            # because the async sender doesn't return the text synchronously, but
            # intent_parser does generate a response. For complete history, we should
            # ideally log the bot response in handle_telegram_message.
            
    except Exception as e:
        print(f"[API] Telegram webhook error: {e}")
        
    return {"status": "ok"}

@app.get("/dashboard/failures")
async def get_failures_dashboard():
    try:
        from agentx.memory.failure_memory import failure_memory
        clusters = failure_memory.cluster_failures_by_embedding()
        analysis = failure_memory.analyze_failures()
        return {
            "status": "success",
            "clusters": clusters,
            "analysis": analysis,
            "total_failures_tracked": len(failure_memory.records)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
