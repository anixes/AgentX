# 🏗️ Architecture Flow

```mermaid
graph TD
    User((User)) -->|Natural Language| TUI[SafeShell TUI]
    TUI -->|Intent Translation| Gateway[AI Gateway]
    Gateway -->|Safe Command| Gate{Safety Gate}
    
    Gate -->|Approved| Exec[Baton Executor]
    Gate -->|Blocked| Audit[Threat Log]
    
    Exec -->|New Process| Worker[Swarm Agent]
    Worker -->|Read/Write| Vault[(Secure Vault)]
    Worker -->|Repair| Code[Project Codebase]
    
    Code -->|Events| Watcher[Live Watcher]
    Watcher -->|Update| Graph[Knowledge Graph]
    
    Worker -->|Telemetry| API[API Bridge]
    API -->|Visualize| Dashboard[React Dashboard]
```

### Flow Breakdown:
1.  **Intent Layer**: User provides natural language.
2.  **Safety Layer**: The command is stripped to its root binary and checked against the Risk DB.
3.  **Execution Layer**: A new OS process is spawned to ensure total memory isolation.
4.  **Feedback Layer**: Results are piped back to the Dashboard and Knowledge Graph simultaneously.
