import subprocess
from agentx.security.permissions import default_permissions

def is_safe(cmd):
    """Check if a command is safe to run against sandbox rules."""
    return default_permissions.validate_command(cmd)

def execute_command(cmd: str, timeout: int = 60, memory: str = "256m", cpus: str = "0.5"):
    """Execute command if safe, using a Hard Docker Sandbox."""
    if not is_safe(cmd):
        raise Exception(f"Unsafe command blocked by sandbox rules: {cmd}")

    docker_cmd = [
        "docker", "run", "--rm",
        "--network=none",
        "--read-only",
        f"--memory={memory}",
        f"--cpus={cpus}",
        "alpine",  # Fallback image, ideally agentx-sandbox
        "/bin/sh", "-c", cmd
    ]
    
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command execution timed out."
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }
