"""
agentx/planning/method_pruner.py
==================================
Phase 12 - Method Library Pruning.

Keeps the method store healthy by:
  1. Removing low-quality methods (score < threshold AND reuse_count > 2).
  2. Keeping only the top-K methods per task_type.
  3. Deduplicating semantically similar methods using TF-IDF cosine similarity.

All similarity computation uses only the Python standard library (math, re,
collections) — no external ML packages required.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Tuple

from agentx.planning.method_store import MethodStore

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MIN_SCORE: float = 0.20
DEFAULT_TOP_K: int = 20
DEFAULT_SIMILARITY_THRESHOLD: float = 0.85


# ---------------------------------------------------------------------------
# TF-IDF cosine similarity (stdlib only)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if t]


def _tfidf_vectors(docs: List[List[str]]) -> List[Dict[str, float]]:
    """
    Compute TF-IDF vectors for a list of tokenized documents.

    Returns a list of dicts: {token: tfidf_weight}.
    """
    N = len(docs)
    if N == 0:
        return []

    # Document frequency
    df: Counter = Counter()
    for tokens in docs:
        for t in set(tokens):
            df[t] += 1

    vectors: List[Dict[str, float]] = []
    for tokens in docs:
        tf: Counter = Counter(tokens)
        total = max(len(tokens), 1)
        vec: Dict[str, float] = {}
        for t, count in tf.items():
            tf_score = count / total
            idf_score = math.log((N + 1) / (df[t] + 1)) + 1.0  # smoothed
            vec[t] = tf_score * idf_score
        vectors.append(vec)

    return vectors


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Cosine similarity between two TF-IDF vectors."""
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in shared)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def tfidf_cosine(text_a: str, text_b: str) -> float:
    """
    Convenience wrapper: cosine similarity between two text strings.
    """
    toks_a = _tokenize(text_a)
    toks_b = _tokenize(text_b)
    vecs = _tfidf_vectors([toks_a, toks_b])
    if len(vecs) < 2:
        return 0.0
    return _cosine_similarity(vecs[0], vecs[1])


# ---------------------------------------------------------------------------
# Pruner
# ---------------------------------------------------------------------------

def prune_methods(
    min_score: float = DEFAULT_MIN_SCORE,
    top_k_per_type: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> int:
    """
    Prune the method library in three passes.

    Parameters
    ----------
    min_score : float
        Methods with score below this AND reuse_count > 2 are removed.
    top_k_per_type : int
        Maximum number of methods to keep per ``task_type``.
    similarity_threshold : float
        TF-IDF cosine similarity above which two methods are considered
        duplicates.  The lower-scoring one is removed and its reuse_count
        is merged into the survivor.

    Returns
    -------
    int — total number of methods removed.
    """
    methods = MethodStore.load()
    before = len(methods)

    # Pass 1: Remove low-quality methods (but protect brand-new ones)
    methods = [
        m for m in methods
        if not (
            m.get("score", 0.5) < min_score
            and m.get("metrics", {}).get("reuse_count", 0) > 2
        )
    ]

    # Pass 2: Keep top-K per task_type
    by_type: Dict[str, List[Dict]] = {}
    for m in methods:
        t = m.get("task_type", "unknown")
        by_type.setdefault(t, []).append(m)

    methods = []
    for task_type, group in by_type.items():
        group.sort(key=lambda m: m.get("score", 0.0), reverse=True)
        methods.extend(group[:top_k_per_type])

    # Pass 3: Deduplicate by TF-IDF cosine similarity on pattern
    methods = _deduplicate(methods, similarity_threshold)

    removed = before - len(methods)
    MethodStore.save(methods)

    if removed > 0:
        print(f"[MethodPruner] Pruned {removed} method(s). Library size: {len(methods)}")

    return removed


def _deduplicate(
    methods: List[Dict],
    threshold: float,
) -> List[Dict]:
    """
    Merge methods whose ``pattern`` strings are cosine-similar above threshold.

    Keeps the higher-scoring method; merges reuse_count into it.
    """
    if len(methods) < 2:
        return methods

    patterns = [m.get("pattern", "") for m in methods]
    tokens_list = [_tokenize(p) for p in patterns]
    vecs = _tfidf_vectors(tokens_list)

    # Track which indices to keep and which to merge
    merged_into: Dict[int, int] = {}  # idx → survivor_idx

    for i in range(len(methods)):
        if i in merged_into:
            continue
        for j in range(i + 1, len(methods)):
            if j in merged_into:
                continue
            sim = _cosine_similarity(vecs[i], vecs[j])
            if sim >= threshold:
                # Decide winner by score
                score_i = methods[i].get("score", 0.0)
                score_j = methods[j].get("score", 0.0)
                survivor, duplicate = (i, j) if score_i >= score_j else (j, i)
                merged_into[duplicate] = survivor
                # Merge reuse_count into survivor
                dup_reuse = methods[duplicate].get("metrics", {}).get("reuse_count", 0)
                surv_metrics = methods[survivor].setdefault("metrics", {})
                surv_metrics["reuse_count"] = (
                    surv_metrics.get("reuse_count", 0) + dup_reuse
                )

    return [m for idx, m in enumerate(methods) if idx not in merged_into]
