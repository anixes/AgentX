from agentx.scheduler.scheduler import scheduler
from agentx.autonomy.intent_engine import intent_engine
import uuid

def _send_telegram_report(message: str):
    print(f"[Telegram Bot] REPORT: {message}")
import uuid

def handle_telegram_command(command: str):
    parts = command.split(" ", 1)
    cmd = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    
    if cmd == "/schedule":
        # e.g., /schedule "backup project every 6h"
        task_id = str(uuid.uuid4())[:8]
        # Extremely basic parsing for interval (mocked to 6h = 21600s)
        scheduler.add_task(task_id, args, 21600)
        return f"Scheduled task {task_id}."
    elif cmd == "/tasks":
        return str(scheduler.get_tasks())
    elif cmd == "/pause":
        success = scheduler.pause_task(args.strip())
        return f"Paused {args}" if success else "Task not found"
    elif cmd == "/resume":
        success = scheduler.resume_task(args.strip())
        return f"Resumed {args}" if success else "Task not found"
    elif cmd == "/approve":
        # Example of approval workflow integration
        return f"Approved task {args}"
        
    # Phase 24: Goal Engine Commands
    from agentx.goals.goal_engine import goal_engine
    
    if cmd == "/goals":
        goals_info = [f"[{g.id}] {g.objective} (Status: {g.status}, Priority: {g.priority})" for g in goal_engine.goals]
        return "\n".join(goals_info) if goals_info else "No goals tracked."
    elif cmd == "/add_goal":
        # e.g. /add_goal "deploy project"
        gid = goal_engine.add_goal(args.strip())
        return f"Added goal {gid}: {args.strip()}"
    elif cmd == "/pause_goal":
        for g in goal_engine.goals:
            if g.id == args.strip():
                g.status = "PAUSED"
                goal_engine.save_state()
                return f"Paused goal {g.id}"
        return "Goal not found."
    elif cmd == "/resume_goal":
        for g in goal_engine.goals:
            if g.id == args.strip():
                g.status = "PENDING"
                goal_engine.save_state()
                return f"Resumed goal {g.id}"
        return "Goal not found."
    elif cmd == "/status":
        interrupted = goal_engine.is_interrupted
        autonomy = goal_engine.autonomy_enabled
        active_count = len(goal_engine.get_active_goals())
        return f"System Status\nAutonomy: {autonomy}\nInterrupted: {interrupted}\nActive Goals: {active_count}"
        
    # Phase 25: Intent Engine Commands
    elif cmd == "/auto_off":
        intent_engine.autonomy_enabled = False
        return "Self-initiated goals disabled."
    elif cmd == "/auto_on":
        intent_engine.autonomy_enabled = True
        return "Self-initiated goals enabled."
    elif cmd == "/auto_status":
        return f"Intent Autonomy Enabled: {intent_engine.autonomy_enabled}\nRecent Actions: {intent_engine.recent_actions}"
        
    return "Unknown command"
