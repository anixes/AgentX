from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from stripper import CommandStripper
from gateway import UnifiedGateway
import os
import subprocess
import json

class RiskPanel(Static):
    """A panel to display AI Risk Analysis."""
    def update_risk(self, explanation: str, level: str = "info"):
        self.update(f"[{level}]AI RISK ANALYSIS:[\n]{explanation}")
        self.add_class(f"risk-{level}")

class SafeShellTUI(App):
    """A premium TUI for SafeShell."""
    
    CSS = """
    Screen {
        background: #1a1a1a;
    }
    
    #main-layout {
        height: 100%;
        width: 100%;
    }
    
    #log-container {
        height: 1fr;
        border: solid #333;
        background: #000;
        padding: 1;
    }
    
    #side-panel {
        width: 40;
        border-left: solid #333;
        padding: 1;
        background: #222;
    }
    
    #input-bar {
        dock: bottom;
        height: 3;
        border-top: solid #333;
    }
    
    .risk-warning {
        color: #ffaa00;
        border: double #ffaa00;
    }
    
    .risk-danger {
        color: #ff5555;
        border: double #ff5555;
    }
    
    .log-entry {
        margin-bottom: 1;
    }
    
    .command-text {
        color: #00ff00;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_log", "Clear Log"),
    ]

    def __init__(self, provider, key, model):
        super().__init__()
        self.gateway = UnifiedGateway(provider, key)
        self.model = model
        self.dangerous_binaries = {
            "rm", "mv", "chmod", "chown", "dd", "mkfs", "shutdown", "reboot",
            "kill", "pkill", "wget", "curl", "bash", "sh", "zsh", "python"
        }

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-layout"):
            with Horizontal():
                with Vertical():
                    yield ScrollableContainer(id="log-container")
                    yield Input(placeholder="Enter command here...", id="input-bar")
                with Vertical(id="side-panel"):
                    yield Static("🛡️ STATUS", id="status-header")
                    yield Static(f"Provider: {self.gateway.provider.upper()}")
                    yield Static(f"Model: {self.model}")
                    yield RiskPanel("No risks detected.", id="risk-display")
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw_input = event.value.strip()
        if not raw_input:
            return
            
        self.query_one("#input-bar").value = ""
        
        # 0. INTENT DETECTION: Is it English or a Command?
        # Simple heuristic: If it has spaces and no common symbols like /, -, |, it's probably an intent.
        is_intent = " " in raw_input and not any(char in raw_input for char in ['/', '-', '|', '>', '<', '$'])
        
        cmd = raw_input
        if is_intent:
            self.log_command(f"Translating intent: {raw_input}...")
            translation_prompt = (
                f"Translate this human intent into a single, efficient bash command: '{raw_input}'. "
                "Return ONLY the raw command string, no explanation, no backticks."
            )
            try:
                if self.gateway.key != "dummy":
                    cmd = await self.gateway.chat(self.model, translation_prompt)
                    cmd = cmd.strip().replace("`", "")
                else:
                    # Dummy mode translation
                    cmd = "ls -la" # Fallback
                self.log_command(f"Intent resolved to: [bold cyan]{cmd}[/]")
            except Exception as e:
                self.query_one("#risk-display").update_risk(f"Translation failed: {str(e)}", "warning")
                return

        self.log_command(cmd)
        
        # 1. Strip and Check
        stripper = CommandStripper(cmd)
        stripper.strip()
        report = stripper.report()
        root = report["Root Binary"]
        wrappers = ", ".join(report["Wrappers"]) if report["Wrappers"] else "None"
        envs = ", ".join([f"{k}={v}" for k, v in report["Env Vars"].items()]) if report["Env Vars"] else "None"

        # Security Risk Intelligence (Local Mirror of bashTool.ts logic)
        RISK_DB = {
            'rm': ('CRITICAL', 'Permanent deletion.'),
            'nc': ('CRITICAL', 'Netcat (Backdoor Risk).'),
            'netcat': ('CRITICAL', 'Netcat (Backdoor Risk).'),
            'sudo': ('HIGH', 'Root Privilege Escalation.'),
            'chmod': ('HIGH', 'Permission Tampering.'),
            'dd': ('CRITICAL', 'Disk Manipulation/Wiping.'),
            'reboot': ('HIGH', 'System Reset.'),
            'kill': ('MEDIUM', 'Process Termination.')
        }

        level, reason = RISK_DB.get(root, ("SAFE", "No immediate threat detected."))
        risk_color = "red" if level in ["CRITICAL", "HIGH"] else "yellow" if level == "MEDIUM" else "green"

        # Update status info
        self.query_one("#risk-display").update(
            f"[bold blue]SECURITY AUDIT[/]\n"
            f"Binary: [b]{root}[/b]\n"
            f"Level: [{risk_color}]{level}[/]\n"
            f"Reason: {reason}\n"
            f"\n[bold blue]WRAPPERS[/]\n"
            f"Prefix: [cyan]{wrappers}[/]\n"
            f"Env: [green]{envs}[/]\n"
        )

        if root in self.dangerous_binaries or level != "SAFE":
            self.query_one("#risk-display").update_risk(f"Analyzing {level} risk via AI Gateway...", "warning")
            
            # 2. Real AI Risk Analysis
            prompt = (
                f"You are a security auditor. Analyze this command: '{cmd}'. "
                f"The root binary is '{root}' (Risk: {level}, Reason: {reason}). "
                "Explain why this is dangerous in a professional developer environment. "
                "Keep it to 2 sentences max."
            )
            
            try:
                if self.gateway.key != "dummy":
                    explanation = await self.gateway.chat(self.model, prompt)
                else:
                    explanation = f"POTENTIAL {level} THREAT: {reason} Sudo/wrappers detected: {wrappers}."
                
                self.query_one("#risk-display").update_risk(explanation, "danger" if level != "MEDIUM" else "warning")
            except Exception as e:
                self.query_one("#risk-display").update_risk(f"AI Analysis Failed: {str(e)}", "danger")
        else:
            self.query_one("#risk-display").update_risk("Command appears safe. Executing...", "info")
            self.execute_command(cmd)

    def log_command(self, cmd: str):
        log = self.query_one("#log-container")
        log.mount(Static(f"> [bold green]{cmd}[/]", classes="log-entry"))
        log.scroll_end()

    def execute_command(self, cmd: str):
        try:
            # Use environment variables extracted by stripper
            stripper = CommandStripper(cmd)
            stripper.strip()
            env = os.environ.copy()
            env.update(stripper.report()["Env Vars"])

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
            log = self.query_one("#log-container")
            if result.stdout:
                log.mount(Static(result.stdout))
            if result.stderr:
                log.mount(Static(f"[red]{result.stderr}[/]"))
            log.scroll_end()
        except Exception as e:
            self.query_one("#log-container").mount(Static(f"[red]Error: {str(e)}[/]"))

if __name__ == "__main__":
    # For demo purposes, we use dummy values if not provided
    app = SafeShellTUI("nvidia", "dummy", "llama-3")
    app.run()
