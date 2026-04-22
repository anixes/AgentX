import os
import argparse
from openai import OpenAI
from typing import Optional, List, Dict

class UnifiedGateway:
    """
    A unified client for multiple AI model providers.
    Supports NVIDIA, Groq, Together, OpenRouter, and Custom (BYO) endpoints.
    """
    
    PROVIDERS = {
        "nvidia": "https://integrate.api.nvidia.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "openai": "https://api.openai.com/v1"
    }

    def __init__(self, provider: str, api_key: str, base_url: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.base_url = base_url or self.PROVIDERS.get(self.provider)
        
        if not self.base_url:
            raise ValueError(f"Unknown provider '{provider}'. Please provide a base_url for custom endpoints.")
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, model: str, prompt: str, system: str = "You are a helpful assistant."):
        """Simple chat completion."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error using {self.provider}: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified AI API Gateway CLI")
    parser.add_argument("--provider", required=True, help="Provider name (nvidia, groq, together, openrouter, custom)")
    parser.add_argument("--key", required=True, help="API Key")
    parser.add_argument("--url", help="Custom base URL (required if provider is 'custom')")
    parser.add_argument("--model", required=True, help="Model string (e.g. nvidia/llama-3.1-nemotron-70b-instruct)")
    parser.add_argument("--prompt", required=True, help="User prompt")
    
    args = parser.parse_args()
    
    gateway = UnifiedGateway(args.provider, args.key, args.url)
    print(f"\n--- Result from {args.provider} ({args.model}) ---")
    print(gateway.chat(args.model, args.prompt))
