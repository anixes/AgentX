# 🛡️ AgentX: Autonomous Secure Orchestration

**AgentX** is a high-performance, security-first agentic development environment. It is designed to bridge the gap between AI code generation and autonomous production maintenance through a "Fortress" architecture.

---

## 🚀 Key Pillars

### 1. 🐝 Self-Healing Swarm
A decentralized network of agents that monitor your territories (`src/prod`, `src/vault`, etc.). If a logic bug or crash is detected, the Swarm automatically diagnoses the error via the **AI Gateway** and applies a verified patch.

### 2. 🔐 The Secure Vault (AES-256-GCM)
A military-grade secret management system. Agents can retrieve deployment tokens and API keys privately in-process, ensuring credentials never leak into chat logs or terminal history.

### 3. 🛡️ SafeShell (Safety Gate)
A tiered risk auditing system that intercepts every bash command. It now classifies commands as **Allow / Ask / Deny**, pauses risky operations for explicit approval from either the CLI or dashboard, and blocks dangerous patterns like `curl | bash`.

### 4. 🛰️ Visual Command Center
A premium React + Vite dashboard that now surfaces the live approval queue, lets you approve or deny pending commands, and streams security events, baton task progress, territory health, and runtime diff telemetry over SSE from the shared AgentX runtime state.

---

## 🛠️ Technology Stack
- **Backend**: Node.js (TypeScript), Python 3.12 (FastAPI/Textual)
- **Frontend**: React 19, Framer Motion, Tailwind CSS, Vite
- **Security**: AES-256-GCM, Zod Validation, Custom Command Stripper
- **Orchestration**: Baton-Handoff Pattern (Multi-Process isolation)
- **Local AI Engine**: Ollama (E: Drive optimization)

---

## 🤖 Local AI Configuration (Optimized for 4GB VRAM)

AgentX is optimized to run fully offline using **Ollama**. For hardware with 4GB VRAM (e.g., GTX 1650 Ti), we use a multi-model "Swarm" approach:

- **Brain (Planner/Critic)**: `phi4-mini` (3.8B, Q4_K_M) - High reasoning, 2.5 GB.
- **Hands (Worker)**: `qwen2.5:3b` (3B, Q4_K_M) - Coding specialist, 1.9 GB.

### Model Performance
Run the benchmark to verify GPU acceleration:
```powershell
python scripts/performance_test.py
```
*Goal: >20 TPS for real-time agentic swarms.*

## ⚡ Quick Start

### 1. Setup Environment
```bash
npm install
cd dashboard && npm install
```

### 2. Launch the Ecosystem
Run the unified dashboard to start the API Bridge and the Visual Command Center:
```bash
npm run dashboard
```

### 3. CLI Missions
Use the CLI for autonomous planning:
```bash
npm run plan "Build a new module for X"
```

---

## 📂 Project Structure
- `scripts/`: Python-based AI agents, health checks, and API bridges.
- `src/tools/`: Hardened AgentX capabilities (Vault, BashTool).
- `.agentx/runtime-state.json`: Shared runtime state consumed by the dashboard API bridge.
- `src/runtime_actions.ts`: Dashboard-triggered approve/deny action runner for pending runtime approvals.
- `src/vault/`: Cryptographic core and storage logic.
- `dashboard/`: The Visual Command Center (React).
- `graphify-out/`: Live-updated Knowledge Graph of the codebase.

---

## 🧠 Philosophy
AgentX is built on the principle that **Autonomous Agents must be constrained by Human Security Patterns.** It is not just an AI that writes code; it is an AI that defends its own work.
