import { z } from 'zod';

export type PermissionLevel = 'default' | 'high' | 'none';

export interface ToolContext {
  cwd: string;
  abortSignal: AbortSignal;
  sessionid: string;
}

export interface ToolResult<T = any> {
  output: T;
  summary?: string;
  isError?: boolean;
}

export interface ToolDefinition<T extends z.ZodObject<any> = any> {
  name: string;
  description: string;
  inputSchema: T;
  permissionLevel: PermissionLevel;
  call: (args: z.infer<T>, context: ToolContext) => Promise<ToolResult>;
  
  // UI Helpers (Inspired by Claude)
  renderToolUse?: (args: z.infer<T>) => string;
  renderResult?: (result: ToolResult) => string;
}
