"""
agentx/planning/method_retriever.py
=====================================
Phase 12 - Method Retrieval & Fit Scoring.

Implements two public functions:

  retrieve_methods(goal, top_n)
    Returns the top-N most relevant methods from the library for a given
    goal string, ranked by a combined similarity + quality score.

  method_fit(method, goal, current_state)
    Computes a single fit score [0, 1] combining semantic similarity,
    historical success rate, and precondition compatibility with the
    current execution state.

Both functions use TF-IDF cosine similarity from method_pruner (stdlib only).
"""

from __future__ import annotations

from typing import Dict, List

from agentx.planning.method_store import MethodStore
from agentx.planning.method_pruner import tfidf_cosine

# Minimum similarity to even consider a method candidate
_MIN_SIMILARITY: float = 0.15

# Combined rank weights: similarity vs. stored quality score
_SIM_WEIGHT: float = 0.60
_SCORE_WEIGHT: float = 0.40


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_methods(goal: str, top_n: int = 5) -> List[Dict]:
    """
    Return the top-N methods most relevant to ``goal``.

    Parameters
    ----------
    goal : str
        The planning goal text to match against method patterns.
    top_n : int
        Maximum number of candidates to return.

    Returns
    -------
    List[dict] sorted by combined relevance rank (highest first).
    Empty list if no methods meet the minimum similarity threshold.
    """
    methods = MethodStore.load()
    if not methods:
        return []

    scored: List[tuple] = []
    for m in methods:
        pattern = m.get("pattern", "")
        sim = tfidf_cosine(goal, pattern)
        if sim < _MIN_SIMILARITY:
            continue
        method_score = m.get("score", 0.4)
        combined = _SIM_WEIGHT * sim + _SCORE_WEIGHT * method_score
        scored.append((combined, sim, m))

    # Sort descending by combined rank
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, _, m in scored[:top_n]]


# ---------------------------------------------------------------------------
# Fit scoring
# ---------------------------------------------------------------------------

def method_fit(method: Dict, goal: str, current_state: Dict) -> float:
    """
    Score how well a method fits a specific goal and current system state.

    Components
    ----------
    * 0.50 — TF-IDF cosine similarity between method pattern and goal
    * 0.30 — Historical success_rate (from stored metrics)
    * 0.20 — Precondition compatibility with current_state

    Parameters
    ----------
    method : dict
        A Phase 12 method entry.
    goal : str
        The planning goal text.
    current_state : dict
        The current system_state dict at the time of planning.

    Returns
    -------
    float in [0, 1].
    """
    pattern = method.get("pattern", "")
    similarity = tfidf_cosine(goal, pattern)

    metrics = method.get("metrics", {})
    success_rate = float(metrics.get("success_rate", 0.5))

    compat = _precondition_compat(method, current_state)

    return (
        0.50 * similarity
        + 0.30 * success_rate
        + 0.20 * compat
    )


def _precondition_compat(method: Dict, current_state: Dict) -> float:
    """
    Fraction of root-node preconditions in the plan_template satisfied by
    the current_state.

    If the template has no preconditions, returns 1.0 (fully compatible).
    """
    template = method.get("plan_template", {})
    nodes = template.get("nodes", [])
    if not nodes:
        return 1.0

    # Find root nodes (those with no dependencies)
    dep_targets = {dep for n in nodes for dep in n.get("dependencies", [])}
    roots = [n for n in nodes if n.get("id") not in dep_targets and not n.get("dependencies")]

    all_preconditions: Dict = {}
    for root in roots:
        all_preconditions.update(root.get("preconditions", {}))

    if not all_preconditions:
        return 1.0

    satisfied = sum(
        1 for k, v in all_preconditions.items()
        if current_state.get(k) == v
    )
    return satisfied / len(all_preconditions)
