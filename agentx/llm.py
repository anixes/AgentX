
import json
import os
from agentx.gateway import UnifiedGateway

# Singleton gateway instance
_gateway = None

def get_gateway():
    global _gateway
    if _gateway is None:
        _gateway = UnifiedGateway()
    return _gateway

def get_gateway_for_model(model_str):
    """
    Returns a gateway instance configured for the specific model.
    Supports 'provider:model_name' syntax.
    """
    provider = "openrouter" # Default
    model_name = model_str

    if ":" in model_str:
        parts = model_str.split(":", 1)
        provider = parts[0]
        model_name = parts[1]
    else:
        # Smart detection fallback (can be expanded)
        if "gemini" in model_str.lower():
            provider = "google"
        elif "gemma" in model_str.lower() or "llama" in model_str.lower():
            # If it doesn't look like a cloud model, assume local llama_cpp
            provider = "llama_cpp"

    # Get API key from environment
    api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
    if not api_key and provider == "google":
        api_key = os.getenv("GEMINI_API_KEY", "")

    return UnifiedGateway(provider=provider, api_key=api_key), model_name

def completion(prompt, system_prompt="You are a helpful assistant.", model=None):
    """
    Standard completion interface used across AgentX.
    Routes to the correct provider based on model name/prefix.
    """
    if model is None:
        try:
            with open("agentx.json", "r") as f:
                config = json.load(f)
                model = config.get("swarm_settings", {}).get("models", {}).get("planner", "google:gemini-3-flash-preview")
        except Exception:
            model = "google:gemini-3-flash-preview"
            
    gw, model_name = get_gateway_for_model(model)
    return gw.chat(model=model_name, prompt=prompt, system=system_prompt) or ""
