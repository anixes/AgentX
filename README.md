# 🛡️ AgentX: Autonomous Secure Orchestration

**AgentX** is a high-performance, security-first agentic development environment. It is designed to bridge the gap between AI code generation and autonomous production maintenance through a "Fortress" architecture.

---

## 🚀 Key Pillars

### 1. 🐝 Self-Healing Swarm
A decentralized network of agents that monitor your territories (`src/prod`, `src/vault`, etc.). If a logic bug or crash is detected, the Swarm automatically diagnoses the error via the **AI Gateway** and applies a verified patch.

### 2. 🔐 The Secure Vault (AES-256-GCM)
A military-grade secret management system. Agents can retrieve deployment tokens and API keys privately in-process, ensuring credentials never leak into chat logs or terminal history.

### 3. 🛡️ SafeShell (Safety Gate)
A tiered risk auditing system that intercepts every bash command. It uses semantic de-noising to block dangerous binaries (like `rm`, `sudo`, `nc`) based on threat intelligence.

### 4. 🛰️ Visual Command Center
A premium React + Vite dashboard that provides real-time telemetry, swarm health maps, and live log streaming.

---

## 🛠️ Technology Stack
- **Backend**: Node.js (TypeScript), Python 3.12 (FastAPI/Textual)
- **Frontend**: React 19, Framer Motion, Tailwind CSS, Vite
- **Security**: AES-256-GCM, Zod Validation, Custom Command Stripper
- **Orchestration**: Baton-Handoff Pattern (Multi-Process isolation)

---

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
- `src/vault/`: Cryptographic core and storage logic.
- `dashboard/`: The Visual Command Center (React).
- `graphify-out/`: Live-updated Knowledge Graph of the codebase.

---

## 🧠 Philosophy
AgentX is built on the principle that **Autonomous Agents must be constrained by Human Security Patterns.** It is not just an AI that writes code; it is an AI that defends its own work.
