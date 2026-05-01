"""
agentx/planning/react_executor.py
===================================
Phase 11 - ReAct-style Executor.

Implements the core "Reason - Act - Observe" loop over a PlanGraph:

  1. **Reason**  - Scheduler identifies the next wave of ready nodes.
  2. **Act**     - ExecutionBridge runs each node through cmd_run.
  3. **Observe** - Result is inspected; Replanner is invoked on failures.
  4. **Persist** - PlanStore snapshots the graph state after each wave.

Hard-stop conditions
--------------------
* All nodes COMPLETED            - success
* A node ESCALATED and no more ready nodes - partial-failure exit
* Max wave iterations exceeded   - safety cap

The executor honours the `PLANNING_ENABLED` feature flag so the existing
agent_loop can safely gate its use.

Usage
-----
    executor = ReActExecutor(plan_id="abc123", graph=plan_graph)
    success = executor.run()
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from agentx.planning.models import PlanGraph, PlanNode
from agentx.planning.scheduler import Scheduler
from agentx.planning.execution_bridge import ExecutionBridge
from agentx.planning.replanner import Replanner, RecoveryAction, RepairRecord
from agentx.planning.plan_store import PlanStore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_WAVES: int = 50     # safety cap - prevents infinite replanning loops


# ---------------------------------------------------------------------------
# ReActExecutor
# ---------------------------------------------------------------------------

class ReActExecutor:
    """
    Runs a PlanGraph to completion using a ReAct (Reason-Act-Observe) loop.

    Parameters
    ----------
    graph : PlanGraph
        Validated DAG ready for execution.
    plan_id : str, optional
        Stable identifier for PlanStore persistence.
        Auto-generated if not provided.
    """

    def __init__(self, graph: PlanGraph, plan_id: Optional[str] = None, task_id: Optional[int] = None):
        self.graph = graph
        self.plan_id = plan_id or str(uuid.uuid4())
        self.task_id = task_id
        self.repair_history: List[RepairRecord] = []

        self._bridge = ExecutionBridge(graph, task_id=self.task_id)
        self._replanner = Replanner(graph, self.repair_history)

    # -- public API ---------------------------------------------------------

    def _split_into_safe_batches(self, nodes: List[PlanNode]) -> List[List[PlanNode]]:
        """
        Split nodes into batches by building a conflict graph to ensure
        conflict-serializable execution that perfectly matches sequential execution.
        """
        from collections import defaultdict
        
        adj = defaultdict(list)
        in_degree = {n.id: 0 for n in nodes}
        node_map = {n.id: n for n in nodes}

        # Build conflict graph (DAG based on original deterministic order)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                node_a = nodes[i]
                node_b = nodes[j]

                effects_a = set(node_a.effects.keys()) if node_a.effects else set()
                effects_b = set(node_b.effects.keys()) if node_b.effects else set()
                preconds_a = set(node_a.preconditions.keys()) if node_a.preconditions else set()
                preconds_b = set(node_b.preconditions.keys()) if node_b.preconditions else set()

                if (effects_a & effects_b) or (preconds_a & effects_b) or (preconds_b & effects_a):
                    # node_a MUST precede node_b to preserve sequential equivalence
                    adj[node_a.id].append(node_b.id)
                    in_degree[node_b.id] += 1

        # Topological sort into layers (batches)
        batches: List[List[PlanNode]] = []
        while True:
            # Find all nodes with no incoming conflict edges
            ready_ids = [nid for nid, deg in in_degree.items() if deg == 0]
            if not ready_ids:
                if in_degree:
                    # Cycle detected (should be impossible due to i < j construction)
                    raise RuntimeError("Cycle detected in conflict graph.")
                break

            # Sort to preserve deterministic sub-ordering
            ready_ids.sort()
            batch = [node_map[nid] for nid in ready_ids]
            batches.append(batch)

            # Remove these nodes and decrement successors
            for nid in ready_ids:
                del in_degree[nid]
                for successor_id in adj[nid]:
                    if successor_id in in_degree:
                        in_degree[successor_id] -= 1

        return batches

    def run(self) -> bool:
        """
        Execute the plan to completion.

        Returns
        -------
        bool - True if all nodes COMPLETED, False otherwise.
        """
        print(
            f"\n[ReActExecutor] [START] Starting plan '{self.plan_id}' "
            f"- goal: {self.graph.goal[:80]}"
        )
        self._persist()

        wave_count = 0
        scheduler = Scheduler(self.graph)

        while True:
            ready_nodes = scheduler.ready_nodes()
            if not ready_nodes:
                break

            if wave_count >= MAX_WAVES:
                print(f"[ReActExecutor] [WARN] Max wave limit ({MAX_WAVES}) reached - aborting.")
                break

            wave_count += 1
            print(f"[ReActExecutor] Wave {wave_count}: {[n.id for n in ready_nodes]}")

            safe_batches = self._split_into_safe_batches(ready_nodes)

            for batch_idx, batch in enumerate(safe_batches):
                if len(safe_batches) > 1:
                    print(f"[ReActExecutor]   Sub-batch {batch_idx+1}/{len(safe_batches)}: {[n.id for n in batch]}")

                # -- ACT -------------------------------------------------------
                results = {}
                with ThreadPoolExecutor() as executor:
                    futures = {executor.submit(self._bridge.run_node, node): node for node in batch}
                    for f in futures:
                        node = futures[f]
                        try:
                            results[node.id] = f.result()
                        except Exception as e:
                            results[node.id] = False
                            node.status = "FAILED"
                            node.error = f"Parallel execution error: {e}"
                            print(f"[ReActExecutor] [FAIL] Unhandled thread exception for '{node.id}': {e}")

                # -- OBSERVE ---------------------------------------------------
                has_escalated = False
                for node in batch:
                    if not results.get(node.id, False):
                        action = self._replanner.handle_failure(node)
                        self._record_repair(node, action)
                        if action == RecoveryAction.ESCALATE:
                            has_escalated = True
                
                if has_escalated:
                    print(f"[ReActExecutor] [FAIL] Node escalated - stopping wave sequence.")
                    # Persist partial failure before breaking
                    self._persist()
                    return False

            # Persist after every wave
            self._persist()

            # Rebuild scheduler to pick up any nodes injected by Decompose
            scheduler = Scheduler(self.graph)

        success = self._all_completed()
        status_icon = "[OK]" if success else "[FAIL]"
        print(
            f"[ReActExecutor] {status_icon} Plan '{self.plan_id}' finished "
            f"- success={success}, waves={wave_count}"
        )
        self._persist()
        self._update_or_learn_method(success)
        return success

    # -- helpers ------------------------------------------------------------

    def _all_completed(self) -> bool:
        return all(
            n.status == "COMPLETED"
            for n in self.graph.nodes
        )

    def _persist(self) -> None:
        try:
            PlanStore.save(self.plan_id, self.graph)
        except Exception as exc:
            print(f"[ReActExecutor] PlanStore.save() warning: {exc}")

    def _record_repair(self, node: PlanNode, action: RecoveryAction) -> None:
        # Find the latest RepairRecord for this node
        for rec in reversed(self.repair_history):
            if rec.node_id == node.id:
                try:
                    PlanStore.record_repair(
                        plan_id=self.plan_id,
                        node_id=rec.node_id,
                        attempt=rec.attempt,
                        failure_kind=rec.failure_kind,
                        action_taken=rec.action_taken,
                        notes=rec.notes,
                    )
                except Exception as exc:
                    print(f"[ReActExecutor] PlanStore.record_repair() warning: {exc}")
                break

    def summary(self) -> dict:
        """Return a human-readable execution summary."""
        counts = {"COMPLETED": 0, "FAILED": 0, "PENDING": 0, "RUNNING": 0}
        for n in self.graph.nodes:
            counts[n.status] = counts.get(n.status, 0) + 1
        return {
            "plan_id": self.plan_id,
            "goal": self.graph.goal,
            "total_nodes": len(self.graph.nodes),
            "node_counts": counts,
            "repairs": len(self.repair_history),
        }

    def _update_or_learn_method(self, success: bool) -> None:
        """
        Phase 12 post-execution hook.

        If the plan came from a cached method (tagged with _source_method_id),
        update that method's metrics.  Otherwise, if the plan was LLM-generated
        and successful, attempt to learn a new method from it.

        This method is intentionally wrapped in a broad try/except so that
        any learning failure never affects the final execution result.
        """
        primitives = self.graph.primitive_nodes()
        avg_uncertainty = (
            sum(n.uncertainty for n in primitives) / max(len(primitives), 1)
        )
        plan_score = max(0.0, 1.0 - avg_uncertainty) if success else 0.0

        source_method_id = getattr(self.graph, "_source_method_id", None)

        if source_method_id:
            # Update metrics for the method that generated this plan
            try:
                from agentx.planning.method_store import MethodStore
                from agentx.planning.method_scorer import update_metrics

                method = MethodStore.get_by_id(source_method_id)
                if method:
                    updated = update_metrics(
                        method,
                        success=success,
                        latency=0.0,
                        uncertainty=avg_uncertainty,
                    )
                    MethodStore.upsert(updated)
                    print(
                        f"[ReActExecutor] Updated metrics for method '{source_method_id}' "
                        f"(success={success}, score={updated.get('score', 0):.3f})"
                    )
            except Exception as exc:
                print(f"[ReActExecutor] Method metrics update failed (non-critical): {exc}")
        else:
            # LLM-generated plan: try to learn a new method
            try:
                from agentx.planning.method_learner import learn_method

                stored = learn_method(
                    self.graph,
                    goal=self.graph.goal,
                    success=success,
                    score=plan_score,
                )
                if stored:
                    print(f"[ReActExecutor] Learned new method from plan '{self.plan_id}'")
            except Exception as exc:
                print(f"[ReActExecutor] Method learning failed (non-critical): {exc}")
