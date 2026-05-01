from .base import Capability, CapabilityResult
import subprocess

def is_safe(cmd: str) -> bool:
    """Basic sandbox security check."""
    dangerous_keywords = ["rm -rf /", "mkfs", "dd ", "> /dev/sda"]
    for kw in dangerous_keywords:
        if kw in cmd:
            return False
    return True

def run_in_sandbox(cmd: str, timeout: int = 60) -> CapabilityResult:
    """Runs a command with safety bounds."""
    if not is_safe(cmd):
        return CapabilityResult(success=False, output={}, error="Command rejected by security sandbox.")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return CapabilityResult(success=True, output={"stdout": result.stdout})
        else:
            return CapabilityResult(success=False, output={"stdout": result.stdout}, error=result.stderr)
    except subprocess.TimeoutExpired:
        return CapabilityResult(success=False, output={}, error="Command execution timed out.")
    except Exception as e:
        return CapabilityResult(success=False, output={}, error=str(e))

class TerminalExec(Capability):
    name = "terminal.exec"
    input_schema = {
        "cmd": "str",
        "timeout": "int (optional)"
    }

    def execute(self, inputs: dict) -> CapabilityResult:
        cmd = inputs.get("cmd")
        if not cmd:
            return CapabilityResult(success=False, output={}, error="Missing 'cmd' in inputs.")
            
        timeout = inputs.get("timeout", 60)
        return run_in_sandbox(cmd, timeout=timeout)
