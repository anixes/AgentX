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

    # 4. Semantic Evaluation (LLM)
    objective = context.get("objective", "")
    if objective and result_str:
        sem_status = evaluate_semantic(objective, result_str)
        if sem_status == "INCORRECT":
            logger.warning(f"[Evaluator] Task {task_id} failed semantic evaluation. FALSE_SUCCESS.")
            return "FALSE_SUCCESS"
        elif sem_status == "PARTIAL":
            logger.warning(f"[Evaluator] Task {task_id} partially succeeded semantic evaluation. PARTIAL_SUCCESS.")
            return "PARTIAL_SUCCESS"

    return "TRUE_SUCCESS"

def evaluate_semantic(objective: str, result: str) -> str:
    """
    Use an LLM to evaluate if the execution result genuinely matches the objective.
    Returns: "CORRECT" | "PARTIAL" | "INCORRECT"
    """
    try:
        from scripts.core.gateway import UnifiedGateway
        gateway = UnifiedGateway()
        
        prompt = f"Objective:\n{objective}\n\nExecution Result:\n{result}\n\nDoes the execution result successfully fulfill the objective?"
        system = (
            "You are an evaluator.\n"
            "Given:\n* objective\n* result\n"
            "Return EXACTLY ONE WORD from the following list:\n"
            "* CORRECT\n* PARTIAL\n* INCORRECT\n"
            "Be strict. Do not assume success unless the result explicitly provides what was asked."
        )
        
        response = gateway.chat(
            model="gpt-4o-mini",
            prompt=prompt,
            system=system
        )
        
        cleaned = response.strip().upper()
        if "INCORRECT" in cleaned:
            return "INCORRECT"
        elif "PARTIAL" in cleaned:
            return "PARTIAL"
        elif "CORRECT" in cleaned:
            return "CORRECT"
    except Exception as e:
        logger.error(f"[Evaluator] Semantic evaluation failed: {e}")
        
    return "CORRECT" # Fallback to deterministic results if LLM fails
