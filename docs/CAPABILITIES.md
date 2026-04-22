# Toolkit Capabilities & Playbook

This document outlines the practical use cases for the SafeShell and Unified Gateway toolkit.

## 🚀 Top 4 Use Cases

### 1. Cost-Free Agentic Development
**Problem**: Using Claude/GPT for every small terminal task is expensive.
**Solution**: Use the `Unified Gateway` to route terminal automation tasks to Groq or NVIDIA NIM. These providers offer massive free-tier credits for high-speed Llama 3 and Nemotron models.

### 2. The "Safety-First" Sandbox
**Problem**: Executing AI-generated shell commands is risky.
**Solution**: Route all commands through `SafeShell`. It uses the `CommandStripper` to unmask dangerous binaries and calls the AI to explain risks *before* execution.

### 3. Model-Agnostic Prototyping
**Problem**: Coding for a specific API (like Anthropic) makes switching providers hard.
**Solution**: The `Unified Gateway` uses a standardized OpenAI-compatible interface. Switching from NVIDIA to Groq to Together AI is a 1-line configuration change.

### 4. High-Parallelism Swarms
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

---
*Generated via RARV analysis on 2026-04-22.*
