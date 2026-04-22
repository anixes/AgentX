import re
import sys

class CommandStripper:
    """
    Mimics Claude's 'Permission Stripping' logic to find the core command binary.
    """
    
    SAFE_WRAPPERS = {"sudo", "nice", "timeout", "time", "nohup", "stdbuf", "watch"}

    def __init__(self, command: str):
        self.original = command.strip()
        self.env_vars = {}
        self.wrappers = []
        self.root_command = ""
        self.args = []

    def strip(self):
        parts = self.original.split()
        if not parts:
            return
            
        i = 0
        # 1. Strip Leading Env Vars (e.g. VAR=val)
        while i < len(parts) and "=" in parts[i] and not parts[i].startswith("-"):
            key, val = parts[i].split("=", 1)
            self.env_vars[key] = val
            i += 1
            
        # 2. Strip Safe Wrappers (e.g. sudo, timeout)
        while i < len(parts) and parts[i].lower() in self.SAFE_WRAPPERS:
            wrapper = parts[i].lower()
            self.wrappers.append(wrapper)
            i += 1
            # Special case for wrappers with flags (e.g. timeout 10s)
            if wrapper in {"timeout", "nice", "stdbuf", "watch"} and i < len(parts):
                # This is a simplification; real logic would parse flags properly
                if not parts[i].startswith("-") or wrapper == "timeout":
                    i += 1 

        # 3. Identify Root Command
        if i < len(parts):
            self.root_command = parts[i]
            self.args = parts[i+1:]

    def report(self):
        return {
            "Original": self.original,
            "Env Vars": self.env_vars,
            "Wrappers": self.wrappers,
            "Root Binary": self.root_command,
            "Arguments": " ".join(self.args)
        }

if __name__ == "__main__":
    test_cmd = sys.argv[1] if len(sys.argv) > 1 else "DEBUG=true sudo timeout 10s npm install"
    stripper = CommandStripper(test_cmd)
    stripper.strip()
    
    import json
    print(json.dumps(stripper.report(), indent=2))
