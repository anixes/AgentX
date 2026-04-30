"""
agentx/planning/models.py
==========================
Phase 11 - PlanNode and PlanGraph data model.

Strict schema - all fields required. Serialises to / from plain dicts
so the planner (LLM output), scheduler, and DB layer all share one type.

PlanNode fields
---------------
id              : unique snake_case identifier within the graph
task            : executable instruction passed verbatim to the engine
dependencies    : list of node IDs that must complete before this node runs
strategy        : execution mode  ["direct" | "skill" | "compose" | "swarm"]
inputs          : list of node IDs whose *outputs* are needed as context
outputs         : dict of key - description of data this node produces
dod             : Definition-of-Done contract used by the evaluator
uncertainty     : float 0.0-1.0 - controls retry / routing behaviour

PlanGraph fields
----------------
goal            : human-readable description of the top-level objective
nodes           : ordered list of PlanNode objects
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# DoD (Definition of Done) sub-structure
# ---------------------------------------------------------------------------

@dataclass
class DoD:
    success_criteria: str
    validation_type: str  # "deterministic" | "semantic" | "hybrid"

    def __post_init__(self):
        valid = {"deterministic", "semantic", "hybrid"}
        if self.validation_type not in valid:
            raise ValueError(
                f"DoD.validation_type must be one of {valid}, got '{self.validation_type}'"
            )

    def to_dict(self) -> Dict[str, str]:
        return {"success_criteria": self.success_criteria,
                "validation_type": self.validation_type}

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "DoD":
        return cls(
            success_criteria=d.get("success_criteria", ""),
            validation_type=d.get("validation_type", "hybrid"),
        )


# ---------------------------------------------------------------------------
# PlanNode
# ---------------------------------------------------------------------------

VALID_STRATEGIES = {"direct", "skill", "compose", "swarm"}
VALID_NODE_TYPES = {"compound", "primitive"}


@dataclass
class PlanNode:
    id: str
    task: str
    dependencies: List[str] = field(default_factory=list)
    strategy: str = "direct"
    inputs: List[str] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)
    preconditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    
    dod: DoD = field(default_factory=lambda: DoD("Task completes without error.", "deterministic"))
    uncertainty: float = 0.3

    # HTN fields ----------------------------------------------------------
    # node_type  : "primitive"  - directly executable by the engine
    #              "compound"   - structural organiser; NEVER executed directly
    # children   : ordered list of child node IDs (populated for compound nodes)
    node_type: str = "primitive"
    children: List[str] = field(default_factory=list)

    # Runtime-only fields (not serialised to the planner schema)
    status: str = field(default="PENDING", repr=False)   # PENDING | RUNNING | COMPLETED | FAILED
    result: Any = field(default=None, repr=False)
    error: str = field(default="", repr=False)
    attempt: int = field(default=0, repr=False)

    def __post_init__(self):
        if self.strategy not in VALID_STRATEGIES:
            raise ValueError(
                f"PlanNode.strategy must be one of {VALID_STRATEGIES}, got '{self.strategy}'"
            )
        if self.node_type not in VALID_NODE_TYPES:
            raise ValueError(
                f"PlanNode.node_type must be one of {VALID_NODE_TYPES}, got '{self.node_type}'"
            )
        if not (0.0 <= self.uncertainty <= 1.0):
            raise ValueError(f"PlanNode.uncertainty must be in [0, 1], got {self.uncertainty}")
        if not self.id:
            raise ValueError("PlanNode.id must be a non-empty string")
        if not self.task:
            raise ValueError("PlanNode.task must be a non-empty string")

    # -- HTN helpers --------------------------------------------------------

    @property
    def is_primitive(self) -> bool:
        """True if this node can be executed directly by the engine."""
        return self.node_type == "primitive"

    @property
    def is_compound(self) -> bool:
        """True if this node is a structural organiser with child nodes."""
        return self.node_type == "compound"

    # -- serialisation ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "type": self.node_type,
            "children": self.children,
            "dependencies": self.dependencies,
            "strategy": self.strategy,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "preconditions": self.preconditions,
            "effects": self.effects,
            "dod": self.dod.to_dict(),
            "uncertainty": self.uncertainty,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanNode":
        dod_raw = d.get("dod", {})
        dod = DoD.from_dict(dod_raw) if isinstance(dod_raw, dict) else DoD(str(dod_raw), "hybrid")
        return cls(
            id=d["id"],
            task=d["task"],
            dependencies=d.get("dependencies", []),
            strategy=d.get("strategy", "direct"),
            inputs=d.get("inputs", []),
            outputs=d.get("outputs", {}),
            preconditions=d.get("preconditions", {}),
            effects=d.get("effects", {}),
            dod=dod,
            uncertainty=float(d.get("uncertainty", 0.3)),
            node_type=d.get("type", "primitive"),
            children=d.get("children", []),
        )


# ---------------------------------------------------------------------------
# PlanGraph
# ---------------------------------------------------------------------------

@dataclass
class PlanGraph:
    goal: str
    nodes: List[PlanNode] = field(default_factory=list)

    # -- convenience lookup -------------------------------------------------

    def node_by_id(self, node_id: str) -> PlanNode | None:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def root_nodes(self) -> List[PlanNode]:
        """Nodes with no dependencies - the execution entry points."""
        return [n for n in self.nodes if not n.dependencies]

    # -- HTN helpers --------------------------------------------------------

    def primitive_nodes(self) -> List[PlanNode]:
        """All nodes that can be executed directly by the engine."""
        return [n for n in self.nodes if n.is_primitive]

    def compound_nodes(self) -> List[PlanNode]:
        """All structural organiser nodes - never executed directly."""
        return [n for n in self.nodes if n.is_compound]

    def leaf_primitives(self) -> List[PlanNode]:
        """
        Primitive nodes that are not listed as children of any compound node.
        These are the true top-level executable leaves (roots of the execution
        graph after compound nodes are stripped out).
        """
        child_ids = {cid for n in self.nodes for cid in n.children}
        return [n for n in self.nodes if n.is_primitive and n.id not in child_ids]

    def children_of(self, node_id: str) -> List[PlanNode]:
        """Return the ordered child PlanNodes for a compound node."""
        parent = self.node_by_id(node_id)
        if parent is None:
            return []
        return [n for cid in parent.children for n in [self.node_by_id(cid)] if n is not None]

    # -- serialisation ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanGraph":
        nodes = [PlanNode.from_dict(n) for n in d.get("nodes", [])]
        return cls(goal=d.get("goal", ""), nodes=nodes)

    @classmethod
    def from_json(cls, raw: str) -> "PlanGraph":
        return cls.from_dict(json.loads(raw))

    def __repr__(self) -> str:
        return f"PlanGraph(goal={self.goal!r}, nodes={len(self.nodes)})"
