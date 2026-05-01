import uuid
from typing import Dict, Any, List, Optional

class Session:
    """Represents a continuous user interaction state."""
    def __init__(self, user_id: str):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.history: List[Dict[str, Any]] = []
        self.active_plan_id: Optional[str] = None
        self.state: Dict[str, Any] = {}
        self.is_interrupted: bool = False

    def log_interaction(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def interrupt(self):
        self.is_interrupted = True

    def resume(self):
        self.is_interrupted = False

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def get_or_create(self, user_id: str) -> Session:
        if user_id not in self.sessions:
            self.sessions[user_id] = Session(user_id)
        return self.sessions[user_id]

# Global session manager instance
session_manager = SessionManager()
