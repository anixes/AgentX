# AJA Toolkit Capabilities and Playbook

This document outlines the practical use cases for AJA on AgentX Core: SafeShell, Telegram remote control, structured approvals, and the Unified Gateway toolkit.

## Top Use Cases

### 1. Cost-Free Agentic Development
**Problem**: Using Claude/GPT for every small terminal task is expensive.
**Solution**: Use the `Unified Gateway` to route terminal automation tasks to Groq or NVIDIA NIM. These providers offer massive free-tier credits for high-speed Llama 3 and Nemotron models.

### 2. The "Safety-First" Sandbox
**Problem**: Executing AI-generated shell commands is risky.
**Solution**: Route all commands through SafeShell. It uses `CommandStripper` and `FileGuardian` to unmask dangerous binaries and explain risks before execution.

### 3. Telegram Remote Control
**Problem**: You need to control your PC from your phone without opening a terminal.
**Solution**: AJA accepts Telegram text commands through the FastAPI bridge, whitelists your Telegram user ID, and returns concise mobile-readable output.

### 4. Production Human Approval
**Problem**: A risky action should never be approved from a vague prompt.
**Solution**: AJA creates a structured approval object with command preview, action type, reason, risk, rollback path, expiry, requester source, and dry-run summary. Approval can happen from Telegram or dashboard.

### 5. Model-Agnostic Prototyping
**Problem**: Coding for a specific API (like Anthropic) makes switching providers hard.
**Solution**: The `Unified Gateway` uses a standardized OpenAI-compatible interface. Switching from NVIDIA to Groq to Together AI is a 1-line configuration change.

### 6. High-Parallelism Swarms
**Problem**: Running 10 agents in parallel hits rate limits on a single provider.
**Solution**: Use the Gateway to load-balance across different providers. Agent A uses Groq, Agent B uses NVIDIA, and Agent C uses Together AI—all managed through a single local endpoint.

---

## 🛠️ Daily Workflows

| Workflow | Command | Best Provider |
| :--- | :--- | :--- |
| **Code Refactor** | `python scripts/gateway.py --provider groq "refactor..."` | Groq (Llama 3.1) |
| **Security Audit** | `python scripts/tui_shell.py` | NVIDIA (Nemotron) |
| **Bulk File Ops** | `python scripts/safe_shell.py` | NVIDIA (Llama 3.1) |
| **API Proxying** | `python scripts/proxy_server.py` | Multi-Provider |
| **Phone Control** | Telegram command to AJA | AgentX Core bridge |
| **Approval Review** | Dashboard or `approve <id>` in Telegram | Human |

---
*Generated via RARV analysis on 2026-04-22.*
