# Phase 6.1 — Worker Capability Registry + Recommendation Engine

## Status: COMPLETE

## Summary

AJA now understands worker capabilities and recommends the best worker for a task.
**AJA recommends -> Human confirms** — no auto-delegation, no hardcoded preferences.

---

## Architecture

```
Executive Desk (Dashboard)
  Worker Registry          Recommendation Engine
  * 7 profiles             * Task type inference
  * Capabilities           * 8-dimension scoring
  * History                * Risk/speed analysis
  * Expand/detail          * Ranked recommendations
                           * Cautions + reasons
                        |
                   REST API
                        |
api_bridge.py
  GET  /workers              (list all)
  GET  /workers/{id}         (get one)
  POST /workers              (create)
  PATCH /workers/{id}        (update)
  DELETE /workers/{id}       (delete)
  POST /workers/seed         (seed defaults)
  POST /workers/recommend    (recommendation engine)
  GET  /workers/{id}/history (execution history)
  POST /workers/{id}/log     (log execution outcome)
                        |
secretary_memory.py (SQLite)
  worker_registry table
  worker_execution_log table
  CRUD methods + seed_default_workers()
  log_worker_execution() with auto-stat updates
```

## Files Modified

| File | Changes |
|------|---------|
| scripts/secretary_memory.py | Added worker_registry + worker_execution_log tables, CRUD methods, execution logging, 7 default worker profiles |
| scripts/api_bridge.py | Added recommendation engine (8-dimension scoring), 9 new API endpoints |
| dashboard/src/App.tsx | Added Workers tab with Registry grid, Recommendation Engine UI, capability badges, score rings |

## Worker Registry Schema

| Column | Type | Description |
|--------|------|-------------|
| worker_id | TEXT PK | Unique identifier (e.g., github-copilot-cli) |
| worker_name | TEXT | Display name |
| worker_type | TEXT | cli_agent or internal_agent |
| availability_status | TEXT | available / unavailable / busy |
| primary_strengths | JSON | Array of strength descriptions |
| weak_areas | JSON | Array of known limitations |
| preferred_task_types | JSON | Tags like code, fix, test, deploy |
| blocked_task_types | JSON | Types this worker cannot handle |
| execution_speed | TEXT | fast / medium / slow |
| reliability_score | REAL | 0.0-1.0 reliability rating |
| cost_profile | TEXT | free / subscription / pay_per_use |
| supports_tests | BOOL | Can execute tests |
| supports_git_operations | BOOL | Can commit/branch/PR |
| supports_deployment | BOOL | Can deploy to production |
| supports_plan_mode | BOOL | Has plan/think mode |
| historical_success_rate | REAL | Auto-calculated from execution logs |
| total_tasks_executed | INT | Running total |
| total_tasks_failed | INT | Running total |
| recent_failures | JSON | Last 10 failure records |

## Recommendation Engine - 8 Scoring Dimensions

| Dimension | Max Points | Logic |
|-----------|-----------|-------|
| Task Type Match | 30 | Matches inferred types against preferred_task_types; -50 penalty for blocked types |
| Capability Requirements | 15 | Tests/Git/Deploy capability match |
| Reliability | 25 | Linear scale from reliability_score |
| Speed Match | 15 | Worker speed vs. task urgency |
| Cost Profile | 10 | Free > Subscription > Pay-per-use |
| Risk Alignment | 5 | Low-risk workers preferred for high-risk tasks |
| Historical Performance | 10 | Bonus for proven track record (>=5 tasks) |
| Strength Overlap | 5 | Keyword matching between objective and strengths |

Total: 0-100 composite score

## Default Worker Profiles (7 Seeded)

| Worker | Status | Speed | Reliability | Cost |
|--------|--------|-------|------------|------|
| GitHub Copilot CLI | Available | Fast | 88% | Subscription |
| Gemini CLI | Available | Medium | 85% | Subscription |
| Swarm Maintenance | Available | Fast | 92% | Free |
| Claude Code | Unavailable | Medium | 90% | Pay-per-use |
| Aider | Unavailable | Fast | 82% | Pay-per-use |
| Codex CLI | Unavailable | Medium | 78% | Pay-per-use |
| OpenCode | Unavailable | Medium | 75% | Pay-per-use |

## Dashboard Features

- Workers tab (new nav icon) with full registry view
- Recommendation Engine input - describe any task, get ranked suggestions
- Task analysis display - inferred types, risk level, speed requirements
- Score ring visualization for each recommendation (0-100)
- Expandable worker cards with strengths, weaknesses, use cases, failure patterns
- Capability badges (Tests / Git / Deploy / Plan Mode)
- Availability indicators with animated pulse
- Reliability bars with color-coded progress
- Seed Defaults button for one-click worker population

## Design Principles

1. Agent-Agnostic - No hardcoded preference for any worker
2. Human-in-the-Loop - AJA recommends, human confirms
3. Transparent Scoring - Every recommendation shows reasons + cautions
4. Learning System - Execution logging updates success rates over time
5. Subscription-Aware - Cost profiles factor into recommendations
