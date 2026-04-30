# Phase 7: Resilient Recovery Layer

The **Resilient Recovery Layer** transforms AgentX from an ephemeral execution script into a robust, state-aware agent platform capable of surviving process crashes, network failures, and non-deterministic tool behavior.

## Core Objective
Ensure that no mission is lost to a crash and no side-effect (e.g., payments, emails) is duplicated during a retry. Move from "fire-and-forget" execution to a **Controller-driven** architecture where the database is the source of truth.

## Key Components

### 1. Authoritative Task Layer (`tasks.py`)
AgentX now tracks the full lifecycle of every execution mission in SQLite.
- **Statuses**: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `FAILED_PERMANENT`, `INTERRUPTED`, `SKIPPED_DUPLICATE`.
- **Deduplication**: Uses `logical_task_id` to detect and coalesce duplicate missions, even if rephrased or retried.
- **Run Identity**: Every mission is tagged with a unique `run_id` (UUID) to track execution lineage.

### 2. Recovery Engine (`recovery.py`)
An automated boot-time process that:
- Detects tasks left in `RUNNING` state (indicating a crash).
- Transitions them to `INTERRUPTED`.
- Re-queues them for execution if they haven't exceeded `MAX_RETRIES`.
- Cleans up stale task locks.

### 3. ToolGuard: Atomic Tool Idempotency (`tools.py`)
The most critical hardening layer. `ToolGuard` wraps tool calls to ensure safety.
- **Atomic Reservation**: Uses `INSERT OR IGNORE` in `BEGIN IMMEDIATE` transactions to prevent two agents from running the same tool call simultaneously.
- **Result Caching (Coalescing)**: If a tool was already completed successfully for a given task, `ToolGuard` returns the cached result instead of re-running the side-effect.
- **Failure Classification**: Differentiates between `RETRYABLE` (network/transient) and `PERMANENT` (logic/auth) errors.

### 4. Task-Level Locking
Prevents parallel execution collisions. Before a `logical_task_id` starts, it must acquire an atomic lock in the `task_locks` table. If another process is already working on it, the second process safely backs off.

### 5. Automatic TTL Maintenance
To prevent the SQLite database from growing indefinitely, AgentX runs a silent cleanup on startup:
- Prunes `tasks` older than 30 days.
- Prunes `tool_executions` older than 30 days.

## Interfaces

### CLI Integration
- **Recovery**: Runs automatically on every `agentx` command invocation.
- **Tracking**: `agentx status` now reflects authoritative DB state rather than just active process lists.

### FastAPI / API Bridge
- **Persistence**: New endpoints for querying task history and tool execution logs.
- **Resilience**: The `/swarm/run` endpoint now returns the `logical_task_id` and `run_id` for client-side tracking.

## Architecture Insight
> **LLM** = Unreliable Planner  
> **Runtime** = Reliable Controller  
> **DB** = Source of Truth  

By decoupling planning from execution state, AgentX can now manage long-running, autonomous missions with production-grade reliability.
