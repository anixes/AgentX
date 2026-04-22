import subprocess
import os

def run_health_check():
    print("[-] Running Health Check on src/prod/app.ts...")
    try:
        # Try to run the app via tsx (using shell=True for Windows resolution)
        result = subprocess.run(
            "npx tsx src/prod/app.ts",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("[+] SYSTEM HEALTHY: No issues detected.")
            return True, None
        else:
            print("[!] SYSTEM FAILURE DETECTED!")
            print(f"Error Log: {result.stderr.strip()}")
            return False, result.stderr
            
    except Exception as e:
        print(f"[!] Health check crashed: {e}")
        return False, str(e)

if __name__ == "__main__":
    run_health_check()
