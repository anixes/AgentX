"""
agentx/planning/planner.py
===========================
Phase 11 - Planner: Goal - PlanGraph.

Sends a deterministic prompt to the UnifiedGateway LLM and parses the
JSON response into a validated PlanGraph.  Falls back gracefully if the
LLM is unavailable (returns a single-node passthrough graph).

Design decisions
----------------
* The prompt is a **zero-shot deterministic compiler prompt** - no conversational
  history, no system-message chaining.  This keeps output consistent.
* We strip markdown fences before JSON parsing to tolerate LLM formatting drift.
* Uncertainty threshold > 0.8 is rejected at validation time (DAGValidator).
* `max_nodes` caps combinatorial explosion from over-eager decomposers.
"""

from __future__ import annotations

import json
import re
import os
from typing import Any, Dict, Optional

from agentx.planning.models import PlanGraph, PlanNode, DoD


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_PLANNER_SYSTEM_PROMPT = """\
You are a deterministic HTN planning compiler for AgentX.

Your task is to convert a goal into a VALID hierarchical plan that satisfies ALL structural, execution, and state constraints.

Return ONLY valid JSON. No explanations. No extra text.

---

## CORE MODEL

The plan is a Hierarchical Task Network:

* Compound tasks -> must be decomposed
* Primitive tasks -> must be executable
* Planning ends ONLY when all executable tasks are primitive

---

## KNOWN METHODS
{methods}

---

## OUTPUT SCHEMA (STRICT)

{
  "goal": "string",
  "nodes": [
    {
      "id": "string",
      "task": "string",
      "type": "compound | primitive",
      "children": ["string"],
      "dependencies": ["string"],
      "strategy": "direct | skill | swarm | compose",
      "inputs": ["string"],
      "outputs": {"string": "string"},
      "preconditions": {"string": "any"},
      "effects": {"string": "any"},
      "dod": {
        "success_criteria": "string",
        "validation_type": "deterministic | semantic | hybrid"
      },
      "uncertainty": 0.0
    }
  ]
}

---

## HARD CONSTRAINTS (NON-NEGOTIABLE)

### 1. HIERARCHY
* Compound nodes MUST have children
* Primitive nodes MUST NOT have children
* Planning must decompose until only primitive tasks remain

### 2. EXECUTION VALIDITY
* ONLY primitive nodes are executable
* Every primitive task must map to an agent capability

### 3. STATE CORRECTNESS
* Preconditions MUST be satisfied by prior effects
* Effects MUST update system state
* Dependencies MUST reflect state flow

### 4. METHOD CONSISTENCY
* If a known method exists, reuse it
* Similar tasks MUST produce similar decompositions

### 5. DAG VALIDITY
* No cycles
* All dependencies must exist
* Compound nodes cannot be depended on directly

### 6. DATA FLOW
* outputs of a node must match inputs of dependent nodes

---

## OPTIMIZATION RULES

* Prefer lower uncertainty paths
* Prefer "skill" over "compose" when possible
* Parallelize independent nodes
* Minimize total number of primitive steps

---

## FAILURE PREVENTION RULES

* Do NOT generate development tasks (e.g. "write code", "create file")
* Do NOT leave compound nodes undecomposed
* Do NOT produce nodes without DoD
* Do NOT violate preconditions/effects chain

---

## SELF-VALIDATION (MANDATORY)

Before output, verify:

* Graph is acyclic
* All dependencies valid
* All compound nodes decomposed
* Preconditions match effects chain
* JSON is valid

---

## OBJECTIVE

Generate a COMPLETE, VALID, and EXECUTABLE HTN plan.
"""

_PLANNER_USER_TEMPLATE = """\
Goal: {goal}

Decompose this goal into an execution graph following the schema above.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers."""
    text = text.strip()
    text = re.sub(r"^```(-:json)-\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _fallback_graph(goal: str) -> PlanGraph:
    """Single-node passthrough plan used when LLM is unavailable."""
    node = PlanNode(
        id="execute_goal",
        task=goal,
        dependencies=[],
        strategy="direct",
        inputs=[],
        outputs={"result": "Output of direct goal execution"},
        dod=DoD("Task completes without error.", "deterministic"),
        uncertainty=0.1,
    )
    return PlanGraph(goal=goal, nodes=[node])


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

class PlanTooComplexError(Exception):
    """Raised when a goal decomposes into too many nodes, requiring human refinement."""
    pass

class Planner:
    """
    Converts a free-text goal into a validated PlanGraph.

    Parameters
    ----------
    gateway : optional UnifiedGateway instance.
              If None, the planner loads it lazily from agentx.gateway.
    max_nodes : hard cap on the number of nodes in the decomposed graph.
    """

    def __init__(self, gateway=None, max_nodes: int = 15):
        self._gateway = gateway
        self.max_nodes = max_nodes

    # -- internal helpers ---------------------------------------------------

    def _get_gateway(self):
        if self._gateway is not None:
            return self._gateway
        try:
            from agentx.gateway import UnifiedGateway
            self._gateway = UnifiedGateway()
        except Exception:
            self._gateway = None
        return self._gateway

    def _call_llm(self, goal: str) -> Optional[str]:
        gw = self._get_gateway()
        if gw is None:
            return None
            
        try:
            from agentx.planning.methods import MethodLibrary
            methods_str = MethodLibrary.format_for_prompt()
        except Exception:
            methods_str = "{}"
            
        system_prompt = _PLANNER_SYSTEM_PROMPT.format(methods=methods_str)
        prompt = _PLANNER_USER_TEMPLATE.format(goal=goal)
        try:
            # UnifiedGateway.complete(system, user) - str
            response = gw.complete(system=system_prompt, user=prompt)
            return response
        except Exception as exc:
            print(f"[Planner] LLM call failed: {exc}")
            return None

    def _parse_response(self, raw: str, goal: str) -> PlanGraph:
        cleaned = _strip_markdown_fences(raw)
        data: Dict[str, Any] = json.loads(cleaned)
        # Enforce max_nodes
        if len(data.get("nodes", [])) > self.max_nodes:
            raise PlanTooComplexError(f"Plan exceeds max_nodes ({self.max_nodes}). Refinement required.")
        graph = PlanGraph.from_dict(data)
        # Backfill goal if LLM omitted it
        if not graph.goal:
            graph.goal = goal
        return graph

    # -- public API ---------------------------------------------------------

    def decompose(self, goal: str) -> PlanGraph:
        """
        Main entry point.

        1. Calls the LLM with the deterministic compiler prompt.
        2. Parses and validates the JSON response.
        3. Falls back to a single-node passthrough graph on any failure.

        Returns
        -------
        PlanGraph  (always - never raises)
        """
        if not goal or not goal.strip():
            raise ValueError("Planner.decompose: goal must be a non-empty string")

        raw = self._call_llm(goal)
        if raw is None:
            print("[Planner] LLM unavailable - using fallback single-node graph")
            return _fallback_graph(goal)

        try:
            graph = self._parse_response(raw, goal)
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"[Planner] Failed to parse LLM response ({exc}) - using fallback graph")
            return _fallback_graph(goal)

        print(f"[Planner] Decomposed '{goal[:60]}' - {len(graph.nodes)} node(s)")
        return graph
