# Bash Security Patterns: Stripping & Validation

Claude Code uses a multi-layered approach to ensure that shell commands are safe before execution. This document deconstructs the patterns found in `bashPermissions.ts` and `bashSecurity.ts`.

## 🛡️ The Three-Layer Defense

### Layer 1: De-noising (The Stripper)
The goal is to find the **True Binary**. An attacker might try to hide a command:
`PORT=3000 sudo rm -rf /`
- Claude's `stripAllLeadingEnvVars()` removes `PORT=3000`.
- It then identifies `sudo` as a "safe wrapper" and looks at the next word.
- It finally arrives at `rm`, which triggers the "Ask/Deny" logic.

### Layer 2: Normalization
Commands that use relative paths are dangerous because they depend on the current working directory (CWD).
- `cd ../../etc && cat shadow`
- Claude normalizes the `cd` target. If the resulting path is a protected system directory, it blocks the command chain entirely.

### Layer 3: Pattern Validation
Even after stripping, the command might contain "Dangerous Patterns" in its arguments.
- **Redirection**: `echo "malicious" > ~/.ssh/authorized_keys`
- **Shell Escapes**: Using backticks `` ` `` or `$(...)` inside a seemingly safe command.
- **Network Pipes**: `curl ... | bash` (Strictly validated or blocked).

---

## 🛠️ Implementation Strategy

To mimic this in your own tools, follow this sequence:

1.  **Regex-based Env Stripping**: Identify strings matching `^[A-Z_]+=[^\s]+`.
2.  **Wrapper Look-through**: Maintain an allow-list of wrappers (`sudo`, `nice`, `timeout`, `time`, `nohup`).
3.  **AST Parsing**: For complex chains (pipes/semicolons), parse the full tree. If ANY node in the tree is destructive, flag the entire message.

---
*Generated via RARV analysis on 2026-04-22.*
