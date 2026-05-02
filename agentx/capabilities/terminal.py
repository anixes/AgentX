from .base import Capability, CapabilityResult
import subprocess

from agentx.runtime.sandbox import is_safe, execute_command

def run_in_sandbox(cmd: str, timeout: int = 60) -> CapabilityResult:
    """Runs a command with safety bounds using Docker."""
    if not is_safe(cmd):
        return CapabilityResult(success=False, output={}, error="Command rejected by security sandbox.")
    
    try:
        res = execute_command(cmd, timeout=timeout)
        if res["success"]:
            return CapabilityResult(success=True, output={"stdout": res["stdout"]})
        else:
            return CapabilityResult(success=False, output={"stdout": res["stdout"]}, error=res["stderr"])
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
