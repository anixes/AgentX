"""
agentx/decision/evaluator.py
===========================
Phase 10 — Decision Evaluation Layer.

Distinguishes between TRUE_SUCCESS and FALSE_SUCCESS to ensure
the agent doesn't blindly trust the "COMPLETED" status if the actual
result is empty, malformed, or contradictory.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("agentx.decision.evaluator")

def evaluate_task(task_id: int, result: str, context: Dict[str, Any]) -> str:
    """
    Evaluate the true outcome of a task execution.
    
    Returns:
        "TRUE_SUCCESS" | "FALSE_SUCCESS" | "FAILURE"
    """
    if result is None:
        # If no result is available to check, we might assume TRUE_SUCCESS if it reached here without failing,
        # but the prompt implies we should check. We'll proceed with checking what we have.
        pass

    result_str = str(result).strip().lower() if result else ""
    
    # 1. Postconditions (if any are present in the skill / context)
    skill = context.get("skill", {})
    if skill and skill.get("postconditions"):
        try:
            from agentx.skills.skill_postconditions import validate_postconditions
            # Provide dummy step_results since validate_postconditions may just check global state
            step_results = [{"step": 0, "result": result_str, "ok": True}]
            pc_ok, pc_failures = validate_postconditions(skill, step_results)
            if not pc_ok:
                logger.warning(f"[Evaluator] Task {task_id} failed postconditions: {pc_failures}. FALSE_SUCCESS.")
                return "FALSE_SUCCESS"
        except ImportError:
            pass

    # 2. Check for empty or malformed results
    if not result_str or result_str in ["none", "null", "[]", "{}", "()", "false"]:
        logger.warning(f"[Evaluator] Task {task_id} returned empty/malformed result. FALSE_SUCCESS.")
        return "FALSE_SUCCESS"
        
    # 3. Check for contradiction / common error strings
    contradictory_terms = ["error", "exception", "failed to", "traceback", "not found", "unauthorized", "denied"]
    for term in contradictory_terms:
        if term in result_str:
            logger.warning(f"[Evaluator] Task {task_id} result contains contradictory term '{term}'. FALSE_SUCCESS.")
            return "FALSE_SUCCESS"

    return "TRUE_SUCCESS"
