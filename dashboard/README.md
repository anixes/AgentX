# AgentX Dashboard

The dashboard is the Visual Command Center for AgentX. It renders runtime state exposed by `scripts/api_bridge.py` and is designed to make the security model visible instead of burying it inside terminal logs.

## Current Views

- **Approval Queue**: Shows the single pending risky command and lets you approve or deny it directly from the dashboard
- **Task Board**: Streams baton task state from `temp_batons/`, including lifecycle stage, failures, recent worker output, and the latest baton history
- **Security Events**: Recent `ALLOW`, `ASK`, `DENY`, `APPROVED`, and `DENIED` runtime events
- **Territories**: Health cards for monitored project areas
- **Runtime Diff**: Current git diff snapshot from the bridge
- **Git History**: Recent commit history

## Data Contract

The dashboard now keeps a live connection open to:

- `GET /runtime/stream`

and still uses these action endpoints when the user clicks buttons:

- `POST /runtime/approve`
- `POST /runtime/deny`

The SSE stream emits a runtime snapshot containing:

- `status`
- `batons`
- `events`
- `diff`
- `history`

The bridge reads from the shared runtime state file at `.agentx/runtime-state.json`, which is written by the TypeScript runtime, and combines it with git/diff status into each stream payload.
Approve and deny actions are executed through `src/runtime_actions.ts`, so the dashboard triggers the same tool system used by the CLI instead of simulating state changes locally.

## Runtime Notes

- The dashboard now uses **Server-Sent Events (SSE)** for live runtime updates.
- SSE snapshots are emitted from `scripts/api_bridge.py`.
- Pending approvals are single-item for now: one risky command can be awaiting review at a time.
- The bridge is state-driven: it reads `.agentx/runtime-state.json` rather than keeping its own in-memory approval queue.

## Development

```bash
npm install
npm run dev
```

Build for production:

```bash
npm run build
```
