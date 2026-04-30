# Graph Report - .  (2026-04-30)

## Corpus Check
- 134 files · ~81,055 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 878 nodes · 1346 edges · 83 communities detected
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.54)
- Token cost: 12,000 input · 2,500 output

## Community Hubs (Navigation)
- [[_COMMUNITY_API Bridge & Command Safety|API Bridge & Command Safety]]
- [[_COMMUNITY_Skill Store & Capture|Skill Store & Capture]]
- [[_COMMUNITY_Orchestration & Swarm Engine|Orchestration & Swarm Engine]]
- [[_COMMUNITY_Skill Executor & ToolGuard|Skill Executor & ToolGuard]]
- [[_COMMUNITY_Model Routing & Query Intelligence|Model Routing & Query Intelligence]]
- [[_COMMUNITY_CLI Commands & File Safety|CLI Commands & File Safety]]
- [[_COMMUNITY_Context Indexer & Retriever|Context Indexer & Retriever]]
- [[_COMMUNITY_System Entry & Config|System Entry & Config]]
- [[_COMMUNITY_Model Providers & Gateway|Model Providers & Gateway]]
- [[_COMMUNITY_Query Execution Loop|Query Execution Loop]]
- [[_COMMUNITY_Dispatch Adapters|Dispatch Adapters]]
- [[_COMMUNITY_Cost Tracking|Cost Tracking]]
- [[_COMMUNITY_Skill Postconditions|Skill Postconditions]]
- [[_COMMUNITY_Task & Tool Persistence|Task & Tool Persistence]]
- [[_COMMUNITY_Skill Composition|Skill Composition]]
- [[_COMMUNITY_Runtime State & Actions|Runtime State & Actions]]
- [[_COMMUNITY_System Invariant Tests|System Invariant Tests]]
- [[_COMMUNITY_Memory & Secretary Service|Memory & Secretary Service]]
- [[_COMMUNITY_Documentation Index|Documentation Index]]
- [[_COMMUNITY_Dashboard App|Dashboard App]]
- [[_COMMUNITY_Cost & Budget Management|Cost & Budget Management]]
- [[_COMMUNITY_Autonomous Git Branching|Autonomous Git Branching]]
- [[_COMMUNITY_OpenAIAnthropic Compatibility|OpenAI/Anthropic Compatibility]]
- [[_COMMUNITY_Provider Registry|Provider Registry]]
- [[_COMMUNITY_Gateway Client|Gateway Client]]
- [[_COMMUNITY_Task Persistence|Task Persistence]]
- [[_COMMUNITY_Graph Storage|Graph Storage]]
- [[_COMMUNITY_Bash & Shell Safety|Bash & Shell Safety]]
- [[_COMMUNITY_Proxy Server|Proxy Server]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]

## God Nodes (most connected - your core abstractions)
1. `CommandStripper` - 51 edges
2. `get_secretary_memory()` - 48 edges
3. `QueryEngine` - 25 edges
4. `ToolGuard` - 23 edges
5. `CostTracker` - 21 edges
6. `execute_telegram_command()` - 18 edges
7. `create_skill_from_task()` - 17 edges
8. `ModelRouter` - 16 edges
9. `UnifiedGateway` - 13 edges
10. `MemoryService` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Unified Gateway Guide` --explains--> `Unified Gateway`  [INFERRED]
  docs/UNIFIED_GATEWAY.md → scripts/gateway.py
- `Unified Gateway Guide` --explains--> `Proxy Server`  [INFERRED]
  docs/UNIFIED_GATEWAY.md → scripts/proxy_server.py
- `Safe Shell Documentation` --explains--> `Safe Shell Wrapper`  [INFERRED]
  docs/SAFE_SHELL.md → scripts/safe_shell.py
- `Bash Security Patterns` --explains--> `AST Command Stripper`  [INFERRED]
  docs/BASH_SECURITY_PATTERNS.md → scripts/stripper.py
- `Agent Orchestration Guide` --explains--> `Swarm Orchestrator`  [INFERRED]
  docs/AGENT_ORCHESTRATION.md → scripts/swarm_launcher.py

## Hyperedges (group relationships)
- **Agent Execution Stack** — src_query_engine, src_tool_manager, src_bash_tool [INFERRED 0.90]
- **Project Documentation Vault** — doc_summary, doc_readme, doc_capabilities [INFERRED 0.85]

## Communities

### Community 0 - "API Bridge & Command Safety"
Cohesion: 0.03
Nodes (140): add_runtime_event(), analyze_shell_command(), append_approval_audit(), append_telegram_history(), approval_is_expired(), approve_communication(), approve_pending(), approve_runtime_approval() (+132 more)

### Community 1 - "Skill Store & Capture"
Cohesion: 0.08
Nodes (45): _compute_confidence(), create_skill_from_task(), _db_path(), _expand_tokens(), _extract_tags(), _family_id(), _fetch_task(), _fetch_tool_executions() (+37 more)

### Community 2 - "Orchestration & Swarm Engine"
Cohesion: 0.07
Nodes (23): append_baton_history(), now_iso(), The worker entry point.     Reads a baton file, executes the assigned task, and, save_baton(), work(), App, load_config(), Load saved config from .agentx/config.json. (+15 more)

### Community 3 - "Skill Executor & ToolGuard"
Cohesion: 0.08
Nodes (36): _bootstrap_executor_tables(), _check_db_available(), check_environment(), _checkpoint_step(), _clear_checkpoints(), _db_path(), execute_skill(), _execute_step() (+28 more)

### Community 4 - "Model Routing & Query Intelligence"
Cohesion: 0.07
Nodes (3): MockQueryEngine, ModelRouter, ToolManager

### Community 5 - "CLI Commands & File Safety"
Cohesion: 0.07
Nodes (10): checkModePermission(), isFileSafeForAutoEdit(), explainCommand(), findTarget(), isFileAutonomousSafe(), loadCustomSafePaths(), fixCommand(), getFileErrors() (+2 more)

### Community 6 - "Context Indexer & Retriever"
Cohesion: 0.1
Nodes (11): Indexer, detectCalls(), detectLanguage(), hashContent(), lineOf(), parseFile(), parseJSON(), parsePython() (+3 more)

### Community 7 - "System Entry & Config"
Cohesion: 0.12
Nodes (26): cmd_dash(), cmd_doctor(), cmd_memory(), cmd_message(), cmd_review(), cmd_run(), cmd_setup(), cmd_status() (+18 more)

### Community 8 - "Model Providers & Gateway"
Cohesion: 0.15
Nodes (2): AnthropicProvider, GeminiProvider

### Community 9 - "Query Execution Loop"
Cohesion: 0.16
Nodes (1): QueryEngine

### Community 10 - "Dispatch Adapters"
Cohesion: 0.23
Nodes (10): BaseAdapter, AiderAdapter, BaseAdapter, CodexAdapter, CopilotAdapter, dispatch_worker(), GeminiAdapter, Dispatch the task to the appropriate worker adapter based on worker_id.     Retu (+2 more)

### Community 11 - "Cost Tracking"
Cohesion: 0.23
Nodes (1): CostTracker

### Community 12 - "Skill Postconditions"
Cohesion: 0.14
Nodes (13): add_postcondition(), _db_path(), _ensure_postconditions_column(), _flatten_results(), parse_postconditions(), _penalise_confidence(), agentx/skills/skill_postconditions.py ====================================== Pha, Parse postconditions from a skills row.     Accepts: JSON string, list, or None. (+5 more)

### Community 13 - "Task & Tool Persistence"
Cohesion: 0.14
Nodes (16): Exception, acquire_task_lock(), cleanup_old_entries(), _get_conn(), _init_tool_db(), PermanentError, agentx/persistence/tools.py Tool-level idempotency guard for AgentX.  Provides a, Atomically attempt to reserve this tool call.          Returns:             None (+8 more)

### Community 14 - "Skill Composition"
Cohesion: 0.17
Nodes (15): build_chain(), compose_skills(), _inject_context(), _log_skill_status(), _max_risk(), agentx/skills/skill_composer.py ================================ Phase 9 — Gap 2, Heuristically split a multi-step objective into ordered sub-objectives.      "fe, Decompose objective into sub-objectives and recommend a skill for each.      Ret (+7 more)

### Community 15 - "Runtime State & Actions"
Cohesion: 0.26
Nodes (7): appendApprovalAudit(), isExpired(), main(), defaultState(), ensureStateDir(), getRuntimeStateFilePath(), RuntimeStateStore

### Community 16 - "System Invariant Tests"
Cohesion: 0.23
Nodes (14): get_db_connection(), Invariant 2: Tool idempotency_key prevents duplicate execution., Invariant 5: retry_count never exceeds MAX_RETRIES., Run agentx command via subprocess to ensure clean process separation., Invariant 1 & 7: Same logical_task_id execute at most once and return cached/ski, Invariant 4: Task-level locking prevents parallel collision., Invariant 6: Recovery resumes interrupted tasks., run_cmd() (+6 more)

### Community 17 - "Memory & Secretary Service"
Cohesion: 0.14
Nodes (1): MemoryService

### Community 18 - "Documentation Index"
Cohesion: 0.2
Nodes (14): Agent Orchestration Guide, Architecture Flow, Bash Security Patterns, Bash Validation Logic, MCP Integration Architecture, Safe Shell Documentation, Documentation Summary, Unified Gateway Guide (+6 more)

### Community 19 - "Dashboard App"
Cohesion: 0.2
Nodes (4): fetchCommunications(), fetchTasks(), handleCommAction(), handleTaskAction()

### Community 20 - "Cost & Budget Management"
Cohesion: 0.2
Nodes (1): CostModeManager

### Community 21 - "Autonomous Git Branching"
Cohesion: 0.25
Nodes (1): AutonomousBranch

### Community 22 - "OpenAI/Anthropic Compatibility"
Cohesion: 0.38
Nodes (1): OpenAICompatProvider

### Community 23 - "Provider Registry"
Cohesion: 0.33
Nodes (1): ProviderRegistry

### Community 24 - "Gateway Client"
Cohesion: 0.18
Nodes (1): GatewayClient

### Community 25 - "Task Persistence"
Cohesion: 0.22
Nodes (6): cleanup_old_tasks(), create_task(), init_db(), Record error details on a task and set its status.     error_type: 'RETRYABLE' o, Delete COMPLETED / FAILED_PERMANENT tasks older than ttl_days. Returns rows dele, update_task_error()

### Community 26 - "Graph Storage"
Cohesion: 0.24
Nodes (1): GraphStore

### Community 27 - "Bash & Shell Safety"
Cohesion: 0.29
Nodes (7): analyzeCommand(), approvalResponse(), classifyCommand(), denyResponse(), resolvePythonExecutable(), summarizeReasons(), toLower()

### Community 28 - "Proxy Server"
Cohesion: 0.28
Nodes (7): BaseModel, ChatMessage, ChatRequest, get_provider_url(), proxy_chat(), Claude Logic: Auto-detect provider or use override., Enhanced Proxy with Claude-inspired Fail-Open and Auto-Routing.

### Community 29 - "Community 29"
Cohesion: 0.31
Nodes (1): CommandManager

### Community 30 - "Community 30"
Cohesion: 0.36
Nodes (1): GraphQuery

### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (7): compare_versions(), explain_skill(), format_ambiguity_prompt(), agentx/skills/skill_introspect.py ================================== Phase 9 — G, Format an interactive prompt for Gap 3 ambiguity resolution., Return a human-readable markdown explanation of a skill.     Includes tools used, Compare tool sequences between two versions of the same skill family.

### Community 32 - "Community 32"
Cohesion: 0.39
Nodes (2): LocalExtractor, Extracts structural nodes (classes, functions) without using AI tokens.

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (3): FileSystemEventHandler, GraphUpdateHandler, Handles file change events to trigger local AST extraction.

### Community 34 - "Community 34"
Cohesion: 0.4
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 0.4
Nodes (1): Calculator

### Community 36 - "Community 36"
Cohesion: 0.4
Nodes (1): VaultCrypto

### Community 37 - "Community 37"
Cohesion: 0.4
Nodes (1): VaultStorage

### Community 38 - "Community 38"
Cohesion: 0.5
Nodes (5): Bash Tool, CLI Entry Point (Ink), Agent Query Engine, Tool Manager, Tool Type Definitions

### Community 39 - "Community 39"
Cohesion: 0.5
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 0.67
Nodes (2): Recover tasks that were interrupted or are still pending.     Returns a list of, recover_tasks()

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (2): init_db(), log_event()

### Community 42 - "Community 42"
Cohesion: 0.67
Nodes (2): Independently verify the worker's execution quality., run_verification()

### Community 43 - "Community 43"
Cohesion: 0.67
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 0.67
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 0.67
Nodes (2): check_invariants(), Validates the system invariants against the database.     Returns a list of viol

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Quick smoke test for Phase 6.1 Worker Registry.

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (2): Graphify Guide, Project README

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (0): 

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (0): 

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (0): 

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (0): 

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (0): 

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (0): 

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (0): 

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (0): 

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (0): 

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (1): Memory Service

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (1): UI Status Bar

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): Project Capabilities

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (1): External AI Providers

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): Project Post-Mortem

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): Sandbox Environment

## Knowledge Gaps
- **90 isolated node(s):** `AgentX — Unified CLI Entry Point ================================= Usage:   agen`, `Start the interactive SafeShell TUI.`, `Launch API Bridge (background) + Dashboard dev server.`, `Delegate an objective to the SwarmEngine (auto-picks mode).`, `Print a concise dashboard of swarm health.` (+85 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 46`** (2 nodes): `test_case.py`, `simulate()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (2 nodes): `test_worker_registry.py`, `Quick smoke test for Phase 6.1 Worker Registry.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (2 nodes): `run_health_check()`, `health_check.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (2 nodes): `test_model()`, `performance_test.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (2 nodes): `self_healer.py`, `heal_system()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (2 nodes): `simulate_agent.ts`, `runFullSimulation()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (2 nodes): `simulate_swarm.ts`, `simulateSwarm()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (2 nodes): `test_idempotent_tool.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (2 nodes): `test_intents.py`, `test_intent()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (2 nodes): `getCompletionScript()`, `completion.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (2 nodes): `calculateTax()`, `app.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (2 nodes): `webSearch.ts`, `ddgSearch()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (2 nodes): `StatusBar.tsx`, `StatusBar()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (2 nodes): `Graphify Guide`, `Project README`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `eslint.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `tailwind.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `ast_extract.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `test_stripper.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `fileTools.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `gitTools.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `semanticTools.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `vaultTool.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `command.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `tool.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `Memory Service`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `UI Status Bar`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Project Capabilities`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `External AI Providers`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `Project Post-Mortem`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `Sandbox Environment`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CommandStripper` connect `API Bridge & Command Safety` to `Orchestration & Swarm Engine`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `QueryEngine` connect `Query Execution Loop` to `Model Routing & Query Intelligence`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `CommandStripper` (e.g. with `Persist an approval audit entry to SQLite (authoritative) and JSONL (debug expor` and `Write a debug snapshot of runtime state to JSON. Not authoritative — SQLite is.`) actually correct?**
  _`CommandStripper` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `ToolGuard` (e.g. with `agentx/skills/skill_executor.py ================================ Phase 8B + 8B.1` and `Create tables needed exclusively by skill_executor (idempotent).`) actually correct?**
  _`ToolGuard` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `AgentX — Unified CLI Entry Point ================================= Usage:   agen`, `Start the interactive SafeShell TUI.`, `Launch API Bridge (background) + Dashboard dev server.` to the rest of the system?**
  _90 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `API Bridge & Command Safety` be split into smaller, more focused modules?**
  _Cohesion score 0.03 - nodes in this community are weakly interconnected._
- **Should `Skill Store & Capture` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._