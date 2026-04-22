import { z } from 'zod';
import { ToolDefinition } from '../types/tool.js';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

// Industry-standard risk categories for Agentic Security (Informed by security-auditor skill)
const RISK_LEVELS: Record<string, { level: string; reason: string }> = {
  // File Destruction & Modification
  'rm': { level: 'CRITICAL', reason: 'Permanent file/directory deletion.' },
  'chmod': { level: 'HIGH', reason: 'Modifying system permissions (Privilege Escalation risk).' },
  'chown': { level: 'HIGH', reason: 'Changing file ownership.' },
  'dd': { level: 'CRITICAL', reason: 'Low-level disk manipulation/wiping.' },
  'mkfs': { level: 'CRITICAL', reason: 'Filesystem formatting.' },
  'truncate': { level: 'MEDIUM', reason: 'File content destruction.' },
  'mv': { level: 'MEDIUM', reason: 'Moving/Renaming critical files.' },

  // Privilege Escalation
  'sudo': { level: 'HIGH', reason: 'Executing with root privileges.' },
  'su': { level: 'HIGH', reason: 'Switching users.' },
  'visudo': { level: 'CRITICAL', reason: 'Modifying sudoer configurations.' },
  'passwd': { level: 'HIGH', reason: 'Changing user passwords.' },

  // Network & Exfiltration
  'nc': { level: 'CRITICAL', reason: 'Netcat detected (Backdoor/Exfiltration risk).' },
  'netcat': { level: 'CRITICAL', reason: 'Netcat detected (Backdoor/Exfiltration risk).' },
  'ncat': { level: 'CRITICAL', reason: 'Netcat detected (Backdoor/Exfiltration risk).' },
  'telnet': { level: 'HIGH', reason: 'Unencrypted network communication.' },
  
  // System Tampering
  'reboot': { level: 'HIGH', reason: 'System restart.' },
  'shutdown': { level: 'HIGH', reason: 'System shutdown.' },
  'insmod': { level: 'CRITICAL', reason: 'Inserting kernel modules.' },
  'rmmod': { level: 'CRITICAL', reason: 'Removing kernel modules.' },
  
  // Process Manipulation
  'kill': { level: 'MEDIUM', reason: 'Terminating processes.' },
  'pkill': { level: 'MEDIUM', reason: 'Terminating processes by name.' }
};

export const bashTool: ToolDefinition<any> = {
  name: 'bash',
  description: 'Execute a shell command. Use this to run scripts, build tools, or perform system operations.',
  inputSchema: z.object({
    command: z.string().describe('The command to execute in the terminal.'),
  }),
  permissionLevel: 'high',
  call: async ({ command }, context) => {
    try {
      // 1. Semantic De-noising & Normalization (Claude-style)
      // We call our python stripper to identify the 'root' binary hidden under sudo/env vars
      const stripperPath = path.join(process.cwd(), 'scripts', 'stripper.py');
      const { stdout: stripperOutput } = await execAsync(`python "${stripperPath}" "${command.replace(/"/g, '\\"')}"`);
      const analysis = JSON.parse(stripperOutput);
      const rootBinary = analysis['Root Binary']?.toLowerCase();

      // 2. Safety Gate Check
      if (rootBinary in RISK_LEVELS) {
        const risk = RISK_LEVELS[rootBinary];
        return {
          output: `[SECURITY ALERT] Level: ${risk.level}\nTarget: ${rootBinary}\nReason: ${risk.reason}\n\nExecution blocked by AgentX Safety Gate.`,
          summary: `Blocked ${risk.level} risk: ${rootBinary}`,
          isError: true
        };
      }

      // 3. Execution
      const { stdout, stderr } = await execAsync(command, { 
        cwd: context.cwd, 
        signal: context.abortSignal,
        env: { ...process.env, ...analysis['Env Vars'] } // Apply extracted env vars
      });
      
      const output = stderr ? `${stdout}\nErrors:\n${stderr}` : stdout;
      return {
        output,
        summary: `Executed: ${command.slice(0, 50)}${command.length > 50 ? '...' : ''}`,
        isError: !!stderr
      };
    } catch (error: any) {
      return {
        output: `Execution failed: ${error.message}`,
        isError: true
      };
    }
  },
};
