# AgentX: Adaptive Execution & Control Playbook

This document outlines the advanced capabilities of AgentX Core, a research-aligned agentic system built for reliable, autonomous terminal operations.

## 🔬 4-Layer Agent Architecture

AgentX follows a modern 4-layer agentic architecture to ensure stability and explainability:

1.  **Execution Layer**: Handles raw actions via a curated **Skill Library** (Action Abstractions) and **Hierarchical Execution** (Composition).
2.  **Control Layer**: Enforces reliability through a **Multi-Agent Evaluation Layer** and a **Strategy Selection Module**.
3.  **Learning Layer**: Persists experience in **Vectorized Memory** and **Adaptive Replanning Loops** to self-correct failures.
4.  **Routing Layer**: Performs **Predictive Routing** to choose optimal execution paths before spending tokens.

---

## 🚀 Key Capabilities

### 1. Strategy Selection Module (Decision Making)
**Problem**: Hardcoded rules fail on complex, novel tasks.
**Solution**: The system uses a strategic dispatch layer to choose between low-level Skills, Hierarchical Composition, or Parallel Swarms. Decisions are gated by a **Rule Engine** that converts repeated failures into deterministic policies.

### 2. Multi-Agent Evaluation & Judge Layer
**Problem**: Single-model evaluation is prone to hallucinations and "Yes-man" bias.
**Solution**: AgentX uses a layered consensus pipeline:
*   **Deterministic Guards**: Code-level verification of postconditions.
*   **Weighted Consensus**: Votes from diverse models (GPT-4o, Gemini 1.5, Claude 3.5) weighted by historical accuracy.
*   **Minority Veto**: High-reliability models can override a success verdict if they detect a failure.
*   **Meta-Evaluation**: The system evaluates its own judges to detect drift or bias.

### 3. Uncertainty-Aware Execution
**Problem**: Errors accumulate silently in long-horizon tasks, leading to "hallucination loops."
**Solution**: Uncertainty is a first-class control signal.
*   **Uncertainty Propagation**: Every step carries an `uncertainty_score`.
*   **Compound Risk Tracking**: The system tracks drift across the entire task trajectory.
*   **Hard Stop Gates**: Execution halts immediately and escalates to a human if cumulative uncertainty exceeds safe bounds (0.8).

### 4. Predictive Routing Layer
**Problem**: Complex multi-evaluator cascades are expensive and slow for simple tasks.
**Solution**: Before execution starts, the system analyzes the objective's complexity and uncertainty trend.
*   **Fast-Path**: Simple tasks use a single evaluator to save cost and latency.
*   **Cascade-Path**: High-complexity tasks are forced into the full multi-agent consensus gate.
*   **Early Abstention**: If the task is predicted to be unresolvable, the system escalates to the user *before* attempting execution.

### 5. Causal Failure Recovery
**Problem**: Generic retries repeat the same mistake.
**Solution**: Errors are classified into causal categories (`AUTH_ERROR`, `RATE_LIMIT`, `TOOL_NOT_FOUND`). The **Adaptive Replanning Loop** uses these types to select targeted recovery strategies (e.g., refreshing auth tokens vs. switching models).

---

## 🛠️ Research-Aligned Workflows

| Component | Research Mapping | Focus |
| :--- | :--- | :--- |
| **Skill Library** | Action Abstractions | Tool-use efficiency |
| **Hierarchical Execution** | Task Decomposition | Complex multi-step chains |
| **Strategy Selection** | Strategy Optimization | Cost/Accuracy trade-offs |
| **Multi-Agent Judge** | Reflection & Verification | Correctness guarantees |
| **Replanning Loop** | Self-Correction | Autonomous recovery |

---
*Updated via Phase 10 Hardening on 2026-04-30.*
