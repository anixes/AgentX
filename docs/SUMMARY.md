# AJA + AgentX Core Build Summary

## Project Milestone: "Remote Human Loop"
AgentX Core now powers AJA as a secure, self-healing agentic environment with phone-based remote control and production-grade approvals.

## Naming

- **AgentX Core**: the engine, runtime, tools, bridge, dashboard, vault, and swarm.
- **AJA**: the assistant/operator that turns intent into explainable action.
- **AgentX Core powers AJA**.

### Components Delivered:
- **Unified CLI**: Single `agentx` command with clean subcommands (`dash`, `run`, `status`, `setup`, `doctor`, `memory`, `help`).
- **Safety Gate**: Semantic command auditing via `CommandStripper`.
- **Secret Vault**: Encrypted credential storage.
- **Unified Swarm Engine**: Replaces disjointed scripts with a single engine supporting Background, Parallel, and Baton modes.
- **API Bridge & Dashboard**: Glassmorphic real-time telemetry with secure, CSRF-protected approval routes and a Mission Launcher panel.
- **Telegram Remote Control**: AJA can receive whitelisted phone commands through Telegram Bot API -> FastAPI bridge -> AgentX Core.
- **Structured Approval Workflow**: Risky actions become approval objects with command preview, action type, reason, risk level, rollback path, expiry, requester source, and dry-run summary.
- **Structured Secretary Memory**: AJA persists obligations, follow-ups, recurring tasks, reminders, stale-task review, and escalation state in SQLite.
- **Messaging Layer**: AJA drafts, manages, approves, and tracks outbound communication without unsafe auto-send behavior.
- **Scheduler and Executive Reviews**: AJA generates morning, night, and weekly reviews with urgency scoring, snooze, escalation, and Telegram delivery.
- **Centralized Gateway**: Unified `UnifiedGateway` utilizing a single `providers.json` source of truth. First-class OpenRouter support.
- **Priority Engine & Decision Layer**: Multi-factor judgment scoring (urgency, stakeholder weight, consequence of delay) that ranks tasks and challenges false urgency.
- **Definition of Done (DoD) Framework**: Mandatory success criteria for all delegations, with auto-generation support for common engineering and executive tasks.
- **Executive Desk Dashboard**: Refactored command center focusing on high-level agenda and delegation oversight.
- **Resilient Recovery Layer**: SQLite-backed authoritative task tracking, boot-time crash recovery, and atomic tool idempotency guards.
- **Persistent Presence Loop**: Continuous agent loop with triggers, guardrails, health dashboard, and remote human-in-the-loop approvals.
- **LLM Decision Engine**: Strategic dispatch layer that chooses optimal execution paths (Skill vs Compose vs Swarm) with hard risk gates and confidence fallbacks.

### User Experience:
| What you want | What you type |
|---|---|
| Interactive shell | `agentx` |
| Launch dashboard | `agentx dash` |
| Run a mission | `agentx run [--bg] "fix all bugs"` |
| Configure API keys | `agentx setup` |
| System diagnostics | `agentx doctor` |
| Manage memory | `agentx memory list` |
| Check swarm status | `agentx status` |
| Control from phone | Telegram command to AJA |
| Add an obligation | `agentx memory add "follow up with recruiter next Tuesday"` |
| Draft communication | `agentx message draft "draft recruiter follow-up"` |
| Run executive review | `agentx review morning` |
| Ask for priority | `what should I do first` (Telegram) |

### Security Metrics:
- **Zero-Trust Input**: All intents are translated and audited before execution.
- **Memory Isolation**: Each agent runs in its own OS process via the Baton pattern.
- **Endpoint Lockdown**: Critical endpoints require Bearer Token authorization to mitigate CSRF attacks.
- **Telegram Whitelist**: Only `TELEGRAM_ALLOWED_USER_ID` can issue phone commands.
- **Structured Human Review**: Risky actions default to ASK and must be explainable before approval.
- **Immutable Approval Audit**: Approval lifecycle events are appended to `.agentx/approval-audit.jsonl`.
- **Encrypted Persistence**: All secrets are stored using AES-256-GCM.
- **Execution Constraints**: Mandatory Definition of Done checklists prevent "agent drift" during autonomous missions.
- **Atomic Tool Idempotency**: `ToolGuard` prevents duplicate side-effects (payments, emails) using database-level reservation locks.
- **Crash Recovery**: Auto-detection and re-queuing of interrupted tasks ensures no mission is lost to process failures.
- **LLM Decoupling**: Decision engine cannot directly execute tools or modify DB; it only selects paths for the deterministic pipeline.
- **Risk-Gated Dispatch**: HIGH risk objectives are automatically routed to ASK/REJECT by the decision engine.

## Phase 1: Telegram Remote Control

Implemented phone -> Telegram -> PC execution flow:

- `POST /telegram/webhook` receives Telegram Bot API updates.
- `POST /telegram/command` supports local testing through the same command router.
- Supported text commands: `status`, `check gpu`, `run training job`, `git pull repo`, `shutdown laptop tonight`, `restart notebook process`.
- Non-whitelisted users are denied.
- Non-text messages are rejected with a text-only explanation.
- Command history persists to `.agentx/telegram-history.jsonl`.

## Phase 2: Production Approval Workflow

Risky actions no longer rely on opaque confirmation prompts. AJA now creates a structured approval object and sends it to Telegram while syncing it to the dashboard queue through `.agentx/runtime-state.json`.

Approval objects include:

- request ID
- exact command preview
- action type
- human-readable reason
- risk level
- rollback path
- expiration timestamp
- requester source
- dry-run summary of expected effect

Approval commands:

- Telegram: `approve <id>` / `reject <id>`
- Dashboard: Approve / Deny buttons
- CLI/runtime: `/approve` / `/deny`

Before execution, approvals are checked for expiration and revalidated through `FileGuardian` and `CommandStripper`.

## Phase 3: Structured Secretary Memory

AJA now has a persistent SQLite task system at `.agentx/aja_secretary.sqlite3`.

The task object supports:

- task identity, title, context, owner, due date, recurrence, priority, and status
- follow-up state, reminder state, escalation level, approval state, related people, and communication history
- source tracking across Telegram, CLI, dashboard, and system-created tasks
- scheduled review, stale task detection, priority sorting, recurring task rescheduling, and Telegram summaries

Interfaces:

- CLI: `python agentx.py memory add|list|review|complete|archive`
- FastAPI: `/memory/tasks`, `/memory/review`, `/memory/summary`
- Telegram: `tasks`, `task review`, `complete <task_id>`, `archive <task_id>`, and natural obligation messages

## Phase 4: Messaging Layer

AJA now stores outbound communication records in the same SQLite secretary database.

The communication object supports:

- recipient, channel, subject, draft content, and tone profile
- approval required/status
- follow-up required/due
- related task ID and communication history
- delivery status and last sent timestamp

Workflow:

```text
Draft -> Edit -> Approval -> Send -> Follow-up tracking
```

Safety rules:

- AJA never auto-sends the first version.
- All outbound messages require approval.
- Telegram is the only direct outbound adapter for now.
- Email and recruiter messages are drafted and tracked, not silently sent.

Interfaces:

- CLI: `python agentx.py message draft|list|approve|reject`
- FastAPI: `/communications`, `/communications/{message_id}/approve`, `/communications/{message_id}/send`
- Telegram: `draft recruiter follow-up`, `approve message <id>`, `send message <id>`, `check pending unanswered messages`

## Phase 5: Scheduler and Daily Executive Review

AJA now generates proactive executive reviews from structured tasks and communications.

Supported reviews:

- morning review: unfinished work, missed deadlines, urgent follow-ups, pending communication, top 3 priorities
- night review: completed work, missed commitments, ignored reminders, carry-forward actions, tomorrow focus
- weekly review: slipped commitments, stale work, blocked tasks, communication follow-ups, next-week priorities

Scheduler capabilities:

- configurable review windows
- no-spam delivery event log
- snooze
- urgency scoring
- stale task escalation
- delayed follow-up escalation
- accountability prompts
- Telegram delivery through `/scheduler/run` or `/scheduler/review/{kind}/deliver`

Interfaces:

- CLI: `python agentx.py review morning|night|weekly`
- FastAPI: `/scheduler/config`, `/scheduler/review/{kind}`, `/scheduler/run`, `/scheduler/snooze/{task_id}`
- Telegram: `morning review`, `night review`, `weekly review`, `what am I avoiding today`, `what slipped this week`

## Phase 6: Priority Engine & Definition of Done (DoD)

AJA uses a multi-factor judgment scoring engine to rank tasks and enforces a mandatory Definition of Done (DoD) for all missions.

Capabilities:
- **Priority Scoring**: Ranks tasks (0-100) based on urgency, stakeholder weight, and consequence.
- **Urgency Challenge**: AJA questions false urgency to prevent burnout.
- **DoD Auto-Generation**: Backend keyword matching creates success criteria for delegations.
- **Executive Desk**: Dashboard refactored to prioritize high-level agenda and oversight.

Interfaces:
- FastAPI: `/memory/priority`, `/swarm/run` (enforced DoD)
- Telegram: `what should I do first`, `what actually matters today`, `what can be ignored this week`

## Phase 7: Resilient Recovery Layer

Transforming execution from ephemeral scripts into a state-aware platform.

- **Authoritative Task Tracking**: Every mission is persisted with a `logical_task_id` and `run_id`.
- **Atomic Tool Guard**: `INSERT OR IGNORE` reservation system for production-grade idempotency.
- **Execution Coalescing**: Duplicate or retried tool calls return cached results instead of re-executing.
- **Boot-time Recovery**: `agentx` automatically scans for crashed tasks on startup and resumes them.
- **Concurrent Safety**: Task-level locking prevents parallel execution collisions on the same objective.

Interfaces:
- CLI: `agentx status` (authoritative), `agentx run` (tracked)
- Persistence: `agentx/persistence/tasks.py`, `agentx/persistence/tools.py`, `agentx/persistence/recovery.py`

## Phase 8: Resilient Skill System

Shifting from ephemeral task execution to a production-grade library of reusable, verifiable behaviors.

- **Autonomous Skill Capture**: Successful missions are "crystallized" into versioned skill records in SQLite.
- **Verifiable Correctness**: Post-execution assertions (postconditions) ensure results satisfy semantic requirements (e.g., file existence, specific JSON keys).
- **Multi-Skill Composition**: Heuristic splitting of complex objectives into chains with context-aware variable injection (`{{key}}`).
- **Safe Replay Engine**: Step-level recovery via checkpoints, environment prerequisite validation, and unified risk-gating.
- **Explainability & Ambiguity Resolution**: Introspection interface for skill diffs and score-proximity gating for near-identical matches.

Interfaces:
- CLI: `agentx` (pre-execution recommendation), `agentx status` (skill usage tracking)
- Logic: `agentx/skills/skill_store.py`, `agentx/skills/skill_executor.py`, `agentx/skills/skill_composer.py`

## Documentation Index
- [ARCHITECTURE_FLOW.md](./ARCHITECTURE_FLOW.md): Visual mapping of the system and CLI reference.
- [PHASE_1_2_REMOTE_APPROVALS.md](./PHASE_1_2_REMOTE_APPROVALS.md): Telegram control and structured approval workflow.
- [PHASE_3_SECRETARY_MEMORY.md](./PHASE_3_SECRETARY_MEMORY.md): SQLite-backed secretary memory.
- [PHASE_4_MESSAGING_LAYER.md](./PHASE_4_MESSAGING_LAYER.md): Outbound communication drafts and follow-up tracking.
- [PHASE_5_SCHEDULER_EXECUTIVE_REVIEW.md](./PHASE_5_SCHEDULER_EXECUTIVE_REVIEW.md): Proactive scheduler and accountability reviews.
- [PHASE_6_PRIORITY_ENGINE_DOD.md](./PHASE_6_PRIORITY_ENGINE_DOD.md): Judgment engine and mandatory delegation constraints.
- [PHASE_7_RESILIENT_RECOVERY.md](./PHASE_7_RESILIENT_RECOVERY.md): Crash survival and tool-level idempotency.
- [PHASE_8_RESILIENT_SKILLS.md](./PHASE_8_RESILIENT_SKILLS.md): Autonomous skill capture, verification, and composition.
- [PHASE_9_RESILIENT_LOOP.md](./PHASE_9_RESILIENT_LOOP.md): Persistent agent loop, triggers, guardrails, and human-in-the-loop approvals.
- [AGENT_ORCHESTRATION.md](./AGENT_ORCHESTRATION.md): How the multi-process swarm works.
- [AUDIT_REPORT.md](./AUDIT_REPORT.md): Historical record of surgical architectural refactoring (Phases 1-3).
- [POST_MORTEM.md](./POST_MORTEM.md): Research findings from the Claude codebase audit.

## Phase 9: Resilient Loop & Presence

Transitioned from one-off command execution to a robust, continuous agentic runtime.

- **Persistent Agent Loop**: A non-blocking execution engine with task prioritization (`INTERRUPTED > PENDING > FAILED`).
- **Execution Guardrails**: Integrated rate limiting, duplicate task detection, retry storm protection, no-progress stalling, and a circuit breaker that hard-stops the loop on catastrophic failure.
- **Trigger Engine**: Event-driven task enqueuing supporting `TIME` (intervals), `TASK_STATE` (cascading workflows), and `FILE_FLAG` (external synchronization) with chronos-safe filtering.
- **Real-time Awareness**: Added `agentx status` dashboard featuring system health indicators, load level scoring, and recent telemetry alerts.
- **Alerting & Notifications**: Telegram/CLI alerting for task completion, failures, stalls, and circuit breaker events with automated rate-limiting and duplicate collapse.
- **Human Approval Layer**: Implementation of a pause-and-wait workflow for `HIGH` risk tasks, allowing remote `approve`/`reject`/`modify` actions and emergency CLI loop controls (`pause-loop`, `resume-loop`, `kill-task`).

Interfaces:
- CLI: `agentx run-loop`, `agentx trigger`, `agentx status`, `agentx approve/reject`, `agentx pause-loop/resume-loop`
- Logic: `agentx/presence/agent_loop.py`, `agentx/presence/trigger_engine.py`, `agentx/presence/state.py`, `agentx/presence/notifier.py`, `agentx/presence/approval.py`

## Phase 10: LLM Decision Engine

Added an LLM-assisted strategy layer to autonomously determine the optimal execution path for any objective without compromising deterministic safety.

- **Strategic Decision Dispatch**: Replaces simple skill matching with a high-level `decide()` function that chooses between `SKILL`, `COMPOSE`, `NEW` (SwarmEngine), `ASK` (clarification), or `REJECT` (unsafe).
- **Gated LLM Interaction**: Enforces strict JSON schema validation and hard constraints: `HIGH` risk tasks must result in human intervention (`ASK`) or `REJECT`.
- **System-Aware Context**: Decision logic incorporates top-skill candidates, risk levels, and recent task history to improve reasoning quality.
- **Fail-Safe Fallbacks**: Low-confidence LLM outputs (<0.6) automatically fall back to the standard deterministic pipeline (`NEW`).
- **Composition Routing**: Automatically routes multi-step objectives through the `SkillComposer` when composition is the optimal strategy. Includes a pre-execution validation gate (`validate_chain`) that verifies tool existence, environment prerequisites, and chain length limits before any execution occurs.
- **Decision Feedback Loop**: Self-improving persistence layer that tracks outcomes (`SUCCESS`, `FAILURE`, `FALLBACK`) and applies confidence biasing to future decisions based on historical performance.
- **Evaluation Layer**: Analyzes execution results using both deterministic checks (malformed outputs, contradictions, failed postconditions) and a controlled LLM semantic check to distinguish between `TRUE_SUCCESS`, `PARTIAL_SUCCESS`, and `FALSE_SUCCESS`, preventing blind trust in simple 'COMPLETED' statuses.
- **Long-Term Decision Memory**: Extracts tags from objectives to detect patterns across similar past tasks. Automatically upgrades or downgrades decision priority if repeated successes or failures are detected for similar intents.
- **System State Awareness**: Injects loop health, load levels, and failure rates into the LLM context. Applies non-blocking decision bias (e.g., discouraging `COMPOSE` during high load or favoring `ASK` when the system is unhealthy).
- **Deterministic Rule Extraction**: Automatically generates hard rules from repeated failures (≥ 3 times) to forcibly override future LLM decisions (e.g., forcing `ASK` instead of failing continuously), completely bypassing the LLM.
- **Decision Traceability**: Real-time logging of an `evidence` array detailing exactly why an LLM decision or deterministic bias was applied. Includes a new CLI command (`agentx explain <task_id>`) for fully transparent post-mortem debugging of the decision pipeline.
- **Outcome-Aware Prompting**: Injecting previous decision results (exact and similar matches) directly into the LLM prompt to improve contextual reasoning for recurring objectives.
- **Deterministic Validation Layer**: A strict, code-only safety module that validates LLM decisions against hard system constraints (existence checks, risk gating, and minimum confidence) before dispatch.
- **Strategic Overrides**: Automatic correction of unsafe decisions (e.g., forcing `ASK` for high-risk tasks or falling back to `NEW` for low-confidence skill matches).

Interfaces:
- Core: Integrated into `agentx run` / `cmd_run` entry point.
- Logic: `agentx/decision/engine.py`, `agentx/decision/feedback.py`, `agentx/decision/validator.py`

