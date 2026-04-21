import { z } from 'zod';
import { ToolDefinition } from '../types/tool.js';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export const bashTool: ToolDefinition<any> = {
  name: 'bash',
  description: 'Execute a shell command. Use this to run scripts, build tools, or perform system operations.',
  inputSchema: z.object({
    command: z.string().describe('The command to execute in the terminal.'),
  }),
  permissionLevel: 'high',
  call: async ({ command }, context) => {
    try {
      const { stdout, stderr } = await execAsync(command, { cwd: context.cwd, signal: context.abortSignal });
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
