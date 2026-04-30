# GSD Phase 7: Resilient Recovery Validation Plan

This plan outlines the systematic validation of the Resilient Recovery Layer (Phase 7) for AgentX.

## Objective
Verify the system's robustness against crashes, concurrency issues, and idempotency violations using real-world execution paths.

## Mandatory Invariants
1. `logical_task_id` side-effects execute at most once.
2. Tool `idempotency_key` never executes more than once.
3. `COMPLETED` tasks never revert to `RUNNING`.
4. Locks must not remain held indefinitely.
5. `retry_count` <= `MAX_RETRIES`.
6. Recovery creates no duplicate executions.
7. Duplicate requests return cached results.

## Task Breakdown

### Wave 1: Infrastructure & Invariants
- **Task 1.1**: Create `tests/invariants.py` with SQL-based assertion checks.
- **Task 1.2**: Implement `tests/system_tests.py` harness (execution wrapper, process simulation, DB inspector).
- **Task 1.3**: Add observability logs to `agentx/persistence/*.py` and `agentx.py`.

### Wave 2: Failure Scenario Tests
- **Task 2.1**: Implement Test 1 (Crash Mid Execution) and Test 6 (Partial Completion Edge Case).
- **Task 2.2**: Implement Test 4 (Lock Failure) and Test 5 (Retry Exhaustion).

### Wave 3: Concurrency & Idempotency
- **Task 3.1**: Implement Test 2 (Duplicate Request Flood) and Test 3 (Tool Idempotency Race).
- **Task 3.2**: Implement Concurrency Stress Test (10 parallel tasks) and Idempotency Validation (repeated rephrased inputs).

### Wave 4: Verification & Reporting
- **Task 4.1**: Execute all tests and generate `VERIFICATION.md` report.
- **Task 4.2**: Highlight any critical bugs or invariant violations.

## Empirical Verification Protocols
- All tests must use the real `.agentx/aja_secretary.sqlite3` database.
- Concurrency must be tested using Python's `multiprocessing` or `threading` to ensure real race conditions.
- Crashes must be simulated using `os._exit()` or process killing to ensure `finally` blocks are skipped where intended.
