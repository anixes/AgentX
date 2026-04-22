# Unified API Gateway & Proxy

This document explains how to use the Unified Gateway scripts to centralize multiple AI providers (NVIDIA, Groq, etc.) into a single interface.

## 🚀 1. Unified Gateway Client (`gateway.py`)

The `gateway.py` script is a lightweight Python wrapper that standardizes calls to any OpenAI-compatible provider.

### Usage
```bash
python scripts/gateway.py \
  --provider nvidia \
  --key YOUR_NVIDIA_KEY \
  --model "nvidia/llama-3.1-nemotron-70b-instruct" \
  --prompt "Write a story about a robot."
```

### Supported Providers
- `nvidia` (NVIDIA NIM)
- `groq` (Groq LPU)
- `together` (Together AI)
- `openrouter` (OpenRouter Aggregator)
- `custom` (Requires `--url` flag)

---

## 🌐 2. BYO-API Proxy Server (`proxy_server.py`)

The Proxy Server is an "API Point" where you can bring your own key and URL. It acts as a middleman, allowing tools that only support one "Base URL" to access any provider.

### How it works
1. Start the server: `python scripts/proxy_server.py`
2. Point your application to `http://localhost:8000/v1`
3. Add a custom header `X-Provider-Url` with the target provider's URL.

### Example Request (via `curl`)
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Provider-Url: https://api.groq.com/openai/v1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🏗️ Technical Architecture

1. **Standardization**: Both tools use the OpenAI API schema (Chat Completions) as the common language.
2. **BYO-K (Bring Your Own Key)**: No keys are stored. They are passed through via headers or CLI arguments.
3. **Async Performance**: The proxy uses `FastAPI` and `httpx` for non-blocking, high-speed routing.

---
*Generated via RARV analysis on 2026-04-22.*
