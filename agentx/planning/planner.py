"""
agentx/planning/planner.py
===========================
Phase 12 - Planner: Goal -> PlanGraph with method-first routing.

Phase 11 design is preserved unchanged.  Phase 12 adds a pre-LLM routing
stage: if the method library contains a high-confidence cached plan for
the incoming goal, it is instantiated directly without an LLM call.

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
from agentx.planning.dag_validator import DAGValidator


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

    # Default score threshold for method-first routing
    DEFAULT_METHOD_THRESHOLD: float = 0.55

    def __init__(
        self,
        gateway=None,
        max_nodes: int = 15,
        method_threshold: float = DEFAULT_METHOD_THRESHOLD,
        use_method_routing: bool = True,
    ):
        self._gateway = gateway
        self.max_nodes = max_nodes
        self.method_threshold = method_threshold
        self.use_method_routing = use_method_routing

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

    # -- method-first routing -----------------------------------------------

    def _try_method_plan(self, goal: str) -> "PlanGraph | None":
        """
        Attempt to build a PlanGraph from the method library without an LLM call.

        Returns a validated PlanGraph if a high-confidence match is found,
        otherwise returns None and the caller should fall back to LLM generation.
        """
        try:
            from agentx.planning.method_retriever import retrieve_methods, method_fit
        except ImportError:
            return None

        candidates = retrieve_methods(goal, top_n=5)
        if not candidates:
            return None

        # candidates is a list of (method, sim)
        scored = [
            (m, method_fit(m, sim, current_state={}))
            for m, sim in candidates
        ]
        best, best_fit = max(scored, key=lambda x: x[1])

        if best_fit < self.method_threshold:
            return None

        template = best.get("plan_template")
        if not template or not template.get("nodes"):
            return None

        try:
            graph = PlanGraph.from_dict(template)
        except Exception as exc:
            print(f"[Planner] Method template parse error: {exc}")
            return None

        # Override goal with the live goal (template may have generic goal text)
        graph.goal = goal

        # Validate before using
        result = DAGValidator.validate(graph)
        if not result.ok:
            print(f"[Planner] Method '{best.get('id')}' failed validation - penalizing and falling back to LLM.")
            try:
                from agentx.planning.method_scorer import update_metrics
                from agentx.planning.method_store import MethodStore
                # Penalize method due to bad DAG
                updated = update_metrics(best, success=False, latency=0.0, uncertainty=1.0)
                MethodStore.upsert(updated)
            except Exception as e:
                print(f"[Planner] Failed to penalize method: {e}")
            return None

        # Tag the graph with the source method id so ReActExecutor can update metrics
        object.__setattr__(graph, "_source_method_id", best["id"]) if hasattr(graph, "__dataclass_fields__") else None
        try:
            graph._source_method_id = best["id"]  # type: ignore[attr-defined]
        except AttributeError:
            pass

        print(
            f"[Planner] Method-first: using cached method '{best.get('id')}' "
            f"(score={best.get('score', 0):.3f}, fit={best_fit:.3f})"
        )
        return graph

    # -- public API ---------------------------------------------------------

    def decompose(self, goal: str, current_state: Optional[Dict] = None) -> PlanGraph:
        """
        Phase 14: Multi-Plan Planning Architecture.
        Generates, verifies, scores, and selects the optimal plan.
        """
        if not goal or not goal.strip():
            raise ValueError("Planner.decompose: goal must be a non-empty string")
            
        current_state = current_state or {}
        
        print(f"\\n[Planner] Initiating multi-plan generation for goal: '{goal}'")
        
        from agentx.planning.scorer import estimate_complexity, COMPLEXITY_LOW, COMPLEXITY_MEDIUM, score_plan
        from agentx.planning.generator import generate_candidate_plans, revise_plan
        from agentx.planning.verifier import verify_plan
        from agentx.planning.selector import select_plan

        # 1. Complexity Estimation
        complexity = estimate_complexity(goal)
        if complexity == COMPLEXITY_LOW:
            k = 1
        elif complexity == COMPLEXITY_MEDIUM:
            k = 3
        else:
            k = 5
            
        print(f"[Planner] Estimated complexity: {complexity}. Targeting {k} candidates.")

        # 2. Generate Candidates (Method Retrieval + LLM Generation + Diversity Filter)
        candidates = generate_candidate_plans(goal, current_state, k)
        if not candidates:
            print("[Planner] Failed to generate any candidate plans. Falling back to passthrough.")
            return _fallback_graph(goal)
            
        print(f"[Planner] Generated {len(candidates)} diverse candidate(s).")

        verified_plans = []
        for i, plan_candidate in enumerate(candidates):
            print(f"  -> Evaluating candidate {i+1}...")
            # 3. Verify Plan
            feedback = verify_plan(plan_candidate)
            
            # 4. Critique & Refine if necessary
            if not feedback.get("valid", True):
                plan_candidate = revise_plan(plan_candidate, feedback)
                # Re-verify after revision
                feedback = verify_plan(plan_candidate)
                
            if not feedback.get("valid", True):
                print(f"     [Reject] Candidate {i+1} failed verification.")
                continue
                
            # 5. Cost-Aware Scoring
            is_method = hasattr(plan_candidate, "_source_method_id")
            method_sr = getattr(plan_candidate, "_method_success_rate", 0.5) if is_method else 0.5
            
            score = score_plan(plan_candidate, feedback.get("state_consistency", 0.5), is_method, method_sr)
            risk = feedback.get("risk_score", 0.5)
            
            print(f"     [Accept] Candidate {i+1} - Score: {score:.2f}, Risk: {risk:.2f}")
            verified_plans.append((plan_candidate, score, risk))
            
            # 6. Early Exit Check
            if score > 0.9 and risk < 0.2:
                print(f"[Planner] Early exit triggered by high-confidence, low-risk plan (Candidate {i+1}).")
                return plan_candidate
                
        if not verified_plans:
            print("[Planner] All candidates rejected by Verifier. Falling back to passthrough.")
            return _fallback_graph(goal)

        # 7. Selection
        final_plan = select_plan(verified_plans)
        return final_plan
