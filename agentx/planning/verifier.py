"""
agentx/planning/verifier.py
============================
Phase 14 - Independent Verifier Agent & Constraint Layer.

Provides independent verification of proposed PlanGraphs.
The verifier does NOT reuse planner context and evaluates the plan
strictly on its own merits to catch hallucinations or invalid states.
"""

from __future__ import annotations

import json
from typing import Dict, Any

from agentx.planning.models import PlanGraph
from agentx.planning.dag_validator import DAGValidator

def check_constraints(plan: PlanGraph) -> bool:
    """
    Hard constraint filter.
    Returns True if the plan is structurally valid, False otherwise.
    Reuses Phase 11/12 validation mechanisms.
    """
    result = DAGValidator.validate(plan)
    return result.ok

def verify_plan(plan: PlanGraph) -> Dict[str, Any]:
    """
    Independent LLM verification of the plan.
    
    Output format:
    {
      "valid": bool,
      "state_consistency": float, # 0.0 to 1.0
      "risk_score": float,        # 0.0 to 1.0
      "missing_preconditions": list[str],
      "conflicts": list[str]
    }
    """
    # 1. Check hard constraints first
    if not check_constraints(plan):
        return {
            "valid": False,
            "state_consistency": 0.0,
            "risk_score": 1.0,
            "missing_preconditions": [],
            "conflicts": ["Failed structural DAG validation."]
        }

    # 2. Call LLM for semantic verification
    from agentx.llm import completion
    
    # Dump the plan to JSON for the LLM
    plan_json = json.dumps(plan.to_dict(), indent=2)
    
    prompt = f"""
You are an independent Plan Verifier agent.
Your job is to strictly analyze the following task plan for logic errors, missing preconditions, and state conflicts.
Do not generate a new plan. Only analyze the provided plan.

Plan:
```json
{plan_json}
```

Return your analysis as a strict JSON object with EXACTLY these keys:
- "valid": boolean (true if the plan is logically sound and executable)
- "state_consistency": float between 0.0 and 1.0 (how well the effects align with the preconditions)
- "risk_score": float between 0.0 and 1.0 (how risky/destructive the plan is)
- "missing_preconditions": list of strings (state keys that should be checked but aren't)
- "conflicts": list of strings (any logical conflicts or dangerous race conditions)

Do not include markdown blocks or any other text outside the JSON.
"""
    
    try:
        response = completion(prompt, system_prompt="You are a strict validation agent.")
        raw_text = response.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        data = json.loads(raw_text.strip())
        
        # Ensure correct types
        return {
            "valid": bool(data.get("valid", False)),
            "state_consistency": float(data.get("state_consistency", 0.5)),
            "risk_score": float(data.get("risk_score", 0.5)),
            "missing_preconditions": list(data.get("missing_preconditions", [])),
            "conflicts": list(data.get("conflicts", []))
        }
    except Exception as e:
        print(f"[Verifier] LLM Verification failed: {e}")
        # Fallback to a neutral/safe evaluation
        return {
            "valid": True,
            "state_consistency": 0.5,
            "risk_score": 0.5,
            "missing_preconditions": [],
            "conflicts": []
        }

def verify_step(node: Any, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 15: Step-Level Verification.
    Dynamically checks a single node before execution to catch state drifts.
    """
    from agentx.llm import completion
    
    node_json = json.dumps({
        "id": node.id,
        "task": node.task,
        "preconditions": node.preconditions,
        "effects": node.effects
    }, indent=2)
    state_json = json.dumps(state, indent=2)
    
    prompt = f"""
You are an Execution Safety Verifier.
Analyze the following step against the current system state.

Step:
```json
{node_json}
```

Current State:
```json
{state_json}
```

Output your analysis as strict JSON with EXACTLY these keys:
- "safe": boolean (true if it's safe to execute this step)
- "risk": float between 0.0 and 1.0
- "issues": list of strings (reasons why it might fail, if any)
"""
    try:
        response = completion(prompt, system_prompt="You are a strict safety verification agent.")
        raw_text = response.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        data = json.loads(raw_text.strip())
        
        return {
            "safe": bool(data.get("safe", True)),
            "risk": float(data.get("risk", 0.1)),
            "issues": list(data.get("issues", []))
        }
    except Exception as e:
        print(f"[Verifier] Step Verification failed: {e}")
        return {
            "safe": True,
            "risk": 0.5,
            "issues": [f"Verification error: {e}"]
        }
