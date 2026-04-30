"""
agentx/planning/replanner.py
=============================
Phase 11 - Dynamic Replanner.

Classifies a failed PlanNode's error and decides the best recovery
strategy.  Keeps a repair history so the same node isn't retried
indefinitely.

Failure taxonomy
----------------
AUTH_ERROR      - Permanent; skip node, escalate
RATE_LIMIT      - Retry with exponential backoff
TOOL_NOT_FOUND  - Try alternative strategy (skill - direct)
CONTEXT_MISSING - Inject missing dependency, restart node
TIMEOUT         - Retry with simpler task decomposition
UNKNOWN         - Retry up to MAX_RETRIES, then mark permanent

Recovery actions
----------------
RETRY           - Requeue node with incremented attempt counter
SKIP            - Mark node SKIPPED_PERMANENT; unblock successors
DECOMPOSE       - Break node into sub-nodes (basic heuristic split)
ESCALATE        - Surface to human / circuit-breaker

The Replanner does NOT modify the DAGValidator or engine - it only
mutates node-level fields (status, task, error) and optionally injects
new PlanNode objects into the graph.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from agentx.planning.models import PlanGraph, PlanNode, DoD


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RETRIES: int = 3
BASE_BACKOFF_SECONDS: float = 2.0   # multiplied by 2^attempt
UNCERTAINTY_HARD_LIMIT: float = 0.8


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------

class FailureKind(Enum):
    AUTH_ERROR = auto()
    RATE_LIMIT = auto()
    TOOL_NOT_FOUND = auto()
    CONTEXT_MISSING = auto()
    TIMEOUT = auto()
    UNKNOWN = auto()


_PATTERNS: List[Tuple[re.Pattern, FailureKind]] = [
    (re.compile(r"auth|unauthori[zs]ed|403|401", re.I), FailureKind.AUTH_ERROR),
    (re.compile(r"rate.-limit|429|too many request", re.I), FailureKind.RATE_LIMIT),
    (re.compile(r"tool.-not.-found|no such tool|unknown skill", re.I), FailureKind.TOOL_NOT_FOUND),
    (re.compile(r"context|missing.-input|key.-error", re.I), FailureKind.CONTEXT_MISSING),
    (re.compile(r"timeout|timed.-out|deadline", re.I), FailureKind.TIMEOUT),
]


def classify_error(error: str) -> FailureKind:
    for pattern, kind in _PATTERNS:
        if pattern.search(error):
            return kind
    return FailureKind.UNKNOWN


# ---------------------------------------------------------------------------
# Recovery action
# ---------------------------------------------------------------------------

class RecoveryAction(Enum):
    RETRY = "RETRY"
    SKIP = "SKIP"
    DECOMPOSE = "DECOMPOSE"
    ESCALATE = "ESCALATE"


# ---------------------------------------------------------------------------
# Repair record
# ---------------------------------------------------------------------------

@dataclass
class RepairRecord:
    node_id: str
    attempt: int
    failure_kind: str
    action_taken: str
    timestamp: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Replanner
# ---------------------------------------------------------------------------

class Replanner:
    """
    Analyses a FAILED PlanNode and applies the appropriate recovery.

    Parameters
    ----------
    graph : PlanGraph
        The live plan graph (mutated in-place during repair).
    repair_history : list
        Running list of RepairRecord objects (injected for testability).
    """

    def __init__(self, graph: PlanGraph, repair_history: Optional[List[RepairRecord]] = None):
        self.graph = graph
        self.repair_history: List[RepairRecord] = repair_history if repair_history is not None else []

    # -- public API ---------------------------------------------------------

    def handle_failure(self, node: PlanNode) -> RecoveryAction:
        """
        Classify the failure and apply a recovery strategy.

        Returns the RecoveryAction that was applied so the caller
        (ReActExecutor) can decide what to do next.
        """
        kind = classify_error(node.error)
        action = self._decide_action(node, kind)
        self._apply(node, kind, action)

        record = RepairRecord(
            node_id=node.id,
            attempt=node.attempt,
            failure_kind=kind.name,
            action_taken=action.value,
            timestamp=_iso_now(),
            notes=node.error[:200],
        )
        self.repair_history.append(record)
        self._log(record)
        return action

    # -- decision logic -----------------------------------------------------

    def _decide_action(self, node: PlanNode, kind: FailureKind) -> RecoveryAction:
        if node.attempt >= MAX_RETRIES:
            return RecoveryAction.ESCALATE

        if kind == FailureKind.AUTH_ERROR:
            return RecoveryAction.ESCALATE          # can't retry auth failures

        if kind == FailureKind.RATE_LIMIT:
            return RecoveryAction.RETRY             # backoff + retry

        if kind == FailureKind.TOOL_NOT_FOUND:
            return RecoveryAction.RETRY             # strategy downgrade then retry

        if kind == FailureKind.CONTEXT_MISSING:
            return RecoveryAction.RETRY             # wait for predecessors

        if kind == FailureKind.TIMEOUT:
            # Tasks with multiple sentences (> 50 chars) qualify for decomposition
            return RecoveryAction.DECOMPOSE if len(node.task) > 50 else RecoveryAction.RETRY

        return RecoveryAction.RETRY                 # UNKNOWN - optimistic retry

    # -- recovery actions ---------------------------------------------------

    def _apply(self, node: PlanNode, kind: FailureKind, action: RecoveryAction) -> None:
        if action == RecoveryAction.RETRY:
            self._apply_retry(node, kind)
        elif action == RecoveryAction.SKIP:
            self._apply_skip(node)
        elif action == RecoveryAction.DECOMPOSE:
            self._apply_decompose(node)
        elif action == RecoveryAction.ESCALATE:
            self._apply_escalate(node)

    def _apply_retry(self, node: PlanNode, kind: FailureKind) -> None:
        backoff = BASE_BACKOFF_SECONDS * (2 ** (node.attempt - 1))

        if kind == FailureKind.TOOL_NOT_FOUND:
            # Downgrade strategy: skill - direct
            _DOWNGRADE = {"skill": "direct", "compose": "direct", "swarm": "direct"}
            node.strategy = _DOWNGRADE.get(node.strategy, "direct")
            print(f"[Replanner] Node '{node.id}' strategy downgraded to '{node.strategy}'")

        if kind == FailureKind.RATE_LIMIT:
            print(f"[Replanner] Rate-limit backoff {backoff:.1f}s for node '{node.id}'")
            time.sleep(backoff)

        node.status = "PENDING"
        node.error = ""

    def _apply_skip(self, node: PlanNode) -> None:
        node.status = "FAILED"
        node.error = f"[Replanner] Skipped after {node.attempt} attempts: {node.error}"
        print(f"[Replanner] [SKIP] Node '{node.id}' SKIPPED permanently")

    def _apply_decompose(self, node: PlanNode) -> None:
        """
        Heuristic decomposition: split a long task at sentence boundaries.
        Inserts two child nodes and marks the parent COMPLETED (delegated).
        """
        sentences = [s.strip() for s in node.task.split(".") if s.strip()]
        if len(sentences) < 2:
            # Can't decompose sensibly - fall back to retry
            node.status = "PENDING"
            node.error = ""
            return

        child_a_id = f"{node.id}_part_a"
        child_b_id = f"{node.id}_part_b"

        child_a = PlanNode(
            id=child_a_id,
            task=sentences[0] + ".",
            dependencies=node.dependencies,
            strategy=node.strategy,
            inputs=node.inputs,
            outputs={},
            dod=DoD(node.dod.success_criteria, node.dod.validation_type),
            uncertainty=node.uncertainty,
        )
        child_b = PlanNode(
            id=child_b_id,
            task=". ".join(sentences[1:]) + ".",
            dependencies=[child_a_id] + node.dependencies,
            strategy=node.strategy,
            inputs=[child_a_id] + node.inputs,
            outputs=node.outputs,
            dod=DoD(node.dod.success_criteria, node.dod.validation_type),
            uncertainty=node.uncertainty,
        )

        # Reroute successors to depend on child_b instead of original node
        for other in self.graph.nodes:
            if node.id in other.dependencies:
                other.dependencies = [
                    child_b_id if d == node.id else d for d in other.dependencies
                ]

        self.graph.nodes.extend([child_a, child_b])
        node.status = "COMPLETED"   # parent delegated
        print(
            f"[Replanner] [DECOMPOSE] Node '{node.id}' decomposed -> "
            f"'{child_a_id}' + '{child_b_id}'"
        )

    def _apply_escalate(self, node: PlanNode) -> None:
        node.status = "FAILED"
        node.error = (
            f"[Replanner] ESCALATED after {node.attempt} attempt(s). "
            f"Last error: {node.error}"
        )
        print(f"[Replanner] [ESCALATE] Node '{node.id}' ESCALATED - manual intervention required")
        try:
            from agentx.persistence.tracker import log_event
            log_event("PLAN_NODE_ESCALATED", {"node_id": node.id, "error": node.error})
        except Exception:
            pass

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _log(record: RepairRecord) -> None:
        print(
            f"[Replanner] node={record.node_id} attempt={record.attempt} "
            f"kind={record.failure_kind} action={record.action_taken}"
        )


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
