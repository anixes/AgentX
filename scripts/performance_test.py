import time
import requests
import json

def test_model(model_name, prompt):
    print(f"\n[TEST] Testing Model: {model_name}...")
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=60)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            duration = end_time - start_time
            # Ollama provides token counts in the response
            eval_count = data.get("eval_count", 0)
            tps = eval_count / duration if duration > 0 else 0
            
            print(f"  - Status   : Success")
            print(f"  - Duration : {duration:.2f} seconds")
            print(f"  - Tokens   : {eval_count}")
            print(f"  - Speed    : {tps:.2f} tokens/sec")
            return tps
        else:
            print(f"  - Status   : Failed (Code {response.status_code})")
            return 0
    except Exception as e:
        print(f"  - Status   : Error ({str(e)})")
        return 0

if __name__ == "__main__":
    test_prompt = "Write a Python script to sort a list of numbers without using .sort()."
    
    models = ["phi4-mini", "qwen2.5:3b"]
    results = {}
    
    print("--- AgentX Model Performance Benchmark ---")
    for m in models:
        tps = test_model(m, test_prompt)
        results[m] = tps
        
    print("\n+-------------------------+-----------------+")
    print("| Model Name              | Performance     |")
    print("+-------------------------+-----------------+")
    for m, tps in results.items():
        print(f"| {m:<23} | {tps:>8.2f} TPS |")
    print("+-------------------------+-----------------+")
    print("Note: Goal is >20 TPS for fluid agentic swarms.")
