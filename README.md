# Project: Agentic AI Workflow (AgentX)
A high-performance agentic AI workflow engine and CLI tool inspired by modern agentic architectures.

## Core Features
1. **Tool-Enabled Agent Engine**: A robust loop that handles tool calls, retries, and thinking modes.
2. **Modular Tool System**: Easily extensible library of tools (Bash, File I/O, Search).
3. **Pluggable Workflows**: Define complex multi-step routines (e.g., Code Review, PR Creation) as atomic workflows.
4. **Terminal UI**: A premium command-line interface using React and Ink.
5. **MCP Integration**: First-class support for Model Context Protocol.

## Tech Stack
- **Runtime**: [Bun](https://bun.sh/) (for maximum performance)
- **Language**: TypeScript (Strict mode)
- **UI Framework**: React + [Ink](https://github.com/vadimdemedes/ink)
- **Schema Validation**: Zod
- **CLI Framework**: Commander.js

## Directory Structure (Proposed)
```text
/
├── src/
│   ├── engine/           # Core Agent Logic (QueryEngine, ToolRunner)
│   ├── tools/            # Tool implementations
│   ├── workflows/        # Pre-defined agentic workflows
│   ├── ui/               # Ink components
│   ├── commands/         # CLI command definitions
│   └── main.ts           # Entry point
├── tests/                # Unit and integration tests
├── .env.example          # Environment variables template
├── tsconfig.json
└── package.json
```
