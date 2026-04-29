# Architecture Flow

```mermaid
graph TD
    User((User)) -->|Natural Language| AJA[AJA Operator]
    Phone((Phone)) -->|Telegram Bot API| Telegram[Telegram Webhook]
    AJA -->|Natural Language| TUI[SafeShell TUI]
    User -->|Web Browser| Dashboard[React Dashboard]
    TUI -->|Intent Translation| Gateway[AI Gateway]
    Dashboard -->|/swarm/run| API[API Bridge]
    Dashboard -->|/config| API
    Telegram -->|Text Command| API
    Gateway -->|Tool Directive| Gate{Safety Gate}
    
    Gate -->|Allow| Engine[SwarmEngine]
    Gate -->|Ask| Approval[Structured Approval Object]
    Gate -->|Deny| Audit[Threat Log]
    Approval -->|approve/reject| Engine[SwarmEngine]
    
    Engine -->|Background Monitoring| Healer[Self Healer Agent]
    Engine -->|Parallel Batching| Worker[Parallel Agent]
    Engine -->|Objective Delegation| Worker[Baton Agent]
    
    Worker -->|Read/Write| Vault[(Secure Vault)]
    Worker -->|Repair| Code[Project Codebase]
    Worker -->|Baton Status + Lifecycle History| Batons[temp_batons/*.json]
    
    Code -->|Events| Watcher[Live Watcher]
    Watcher -->|Update| Graph[Knowledge Graph]
    
    Worker -->|Runtime State| State[.agentx/runtime-state.json]
    AJA -->|Obligations + Follow-ups| Secretary[(SQLite Secretary Memory)]
    AJA -->|Outbound Drafts| Comms[(SQLite Communication Records)]
    Telegram -->|Secretary Commands| Secretary
    Telegram -->|Draft / Approve / Send Message| Comms
    API -->|/memory/*| Secretary
    API -->|/communications/*| Comms
    API -->|/scheduler/*| Scheduler[Executive Scheduler]
    Scheduler -->|Read + Escalate| Secretary
    Scheduler -->|Read Follow-ups| Comms
    Scheduler -->|Telegram Delivery| Phone
    Approval -->|Pending Approval| State
    Approval -->|Immutable JSONL| ApprovalAudit[.agentx/approval-audit.jsonl]
    Batons -->|Bridge Read + Snapshot Build| API
    State -->|Bridge Read + Snapshot Build| API
    API -->|Read/Write| Config[.agentx/config.json]
    API -->|Approve/Deny + Mission Launch| Runner[runtime_actions.ts]
    Runner -->|Tool Execution + State Update| State
    API -->|SSE Stream| Dashboard
    API -->|Telegram Replies| Phone
```

## Naming Model

- **AgentX Core** is the engine: runtime state, tools, safety gates, dashboard bridge, vault, and swarm orchestration.
- **AJA** is the operator: the assistant personality that receives intent, explains consequences, and routes work through AgentX Core.
- Practical shorthand: **AgentX Core powers AJA**.

## Unified CLI

```
agentx              → Start the interactive SafeShell TUI (default)
agentx dash         → Launch Dashboard + API Bridge in one command
agentx run [--bg]   → Delegate a mission to SwarmEngine (optionally in background)
agentx status       → Show swarm health & active batons
agentx setup        → Configure AI provider, API key & model interactively
agentx doctor       → Run system health checks and diagnostics
agentx memory       → Manage agent persistent memory
agentx help         → Show available commands
```

## Configuration

API settings are stored in `.agentx/config.json` and can be configured two ways:
- **CLI**: Run `agentx setup` for an interactive wizard
- **Dashboard**: Click the Settings (gear) icon in the sidebar

Both read from and write to the same config file. Gateway clients (TypeScript and Python) 
read config.json first, falling back to environment variables if the config is missing.

### Flow Breakdown:
1.  **Intent Layer**: User provides natural language via AJA, SafeShell TUI, Telegram, or the Dashboard's "Run Mission" input.
2.  **Safety Layer**: The command is stripped to its root binary by `CommandStripper`, checked for dangerous patterns, and classified as **Allow / Ask / Deny**.
3.  **Approval Layer**: Risky commands pause as structured approval objects. The user sees the request ID, command preview, action type, human-readable reason, risk level, rollback path, expiration timestamp, requester source, and dry-run summary before approving or rejecting.
4.  **Execution Layer**: The unified `SwarmEngine` handles task execution, supporting background healing, parallel processing, and objective-based baton handoffs.
5.  **Feedback Layer**: Runtime events, pending approvals, approval audit records, Telegram command history, and baton task state are persisted into shared state files, then surfaced through the `API Bridge` as live SSE snapshots for the Dashboard and concise Telegram replies.

## Phase 1: Telegram Remote Control

The Telegram Bot API connects to `POST /telegram/webhook` on the FastAPI bridge. The bridge whitelists `TELEGRAM_ALLOWED_USER_ID`, accepts text commands only, maps supported intents to known actions, and logs command history to `.agentx/telegram-history.jsonl`.

Supported initial commands:

- `status`
- `check gpu`
- `run training job`
- `git pull repo`
- `shutdown laptop tonight`
- `restart notebook process`

## Phase 2: Production Approval Workflow

The old phone-only confirmation-token pattern has been replaced by structured approval requests. Risky Telegram commands are written into `.agentx/runtime-state.json` so the dashboard queue sees the same approval object as the phone.

Approval decisions use:

- Telegram: `approve <id>` / `reject <id>`
- Dashboard: Approve / Deny buttons against the shared pending object
- CLI/runtime: `/approve` / `/deny` for local pending tool calls

All approvals expire and are re-checked through `FileGuardian` and `CommandStripper` before execution.

## Phase 3: Structured Secretary Memory

AJA stores obligations in SQLite at `.agentx/aja_secretary.sqlite3`, separate from transient runtime state. This memory tracks obligations, follow-ups, recurring responsibilities, reminders, escalation level, communication history, and source.

Interfaces:

- CLI: `agentx memory add|list|review|complete|archive`
- FastAPI: `/memory/tasks`, `/memory/review`, `/memory/summary`
- Telegram: `tasks`, `task review`, `complete <task_id>`, `archive <task_id>`, and natural obligation messages

The review path detects overdue, due-soon, stale, and blocked tasks. Stale tasks can escalate if ignored.

## Phase 4: Messaging Layer

AJA stores outbound communication in `secretary_communications` inside `.agentx/aja_secretary.sqlite3`.

Supported initial channels:

- Telegram outbound
- email drafting
- recruiter follow-up drafts
- reminder messages
- personal accountability check-ins

Every outbound message starts as an approval-required draft. The direct send path is only implemented for Telegram, and it still refuses to send until approval is recorded. Email and professional drafts remain tracked as ready/manual-send drafts until a real email adapter exists.

## Phase 5: Scheduler and Executive Review

The executive scheduler reads tasks and communications from SQLite, generates high-signal reviews, and records delivery events to prevent spam.

Review types:

- Morning: unfinished tasks, missed deadlines, urgent follow-ups, pending communication, top 3 priorities.
- Night: completed tasks, missed commitments, ignored reminders, carry-forward actions, tomorrow focus.
- Weekly: slipped commitments, stale work, blocked tasks, communication follow-ups, next-week priorities.

Scheduler endpoints live under `/scheduler/*`. Telegram commands can request reviews directly, and `/scheduler/run` can deliver due reviews during configured windows.
