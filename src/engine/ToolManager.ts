import { ToolDefinition } from '../types/tool.js';
import { bashTool } from '../tools/bashTool.js';

export class ToolManager {
  private tools: Map<string, ToolDefinition<any>> = new Map();

  constructor() {
    this.registerTool(bashTool);
  }

  registerTool(tool: ToolDefinition<any>) {
    this.tools.set(tool.name, tool);
  }

  getTool(name: string): ToolDefinition<any> | undefined {
    return this.tools.get(name);
  }

  listTools(): ToolDefinition<any>[] {
    return Array.from(this.tools.values());
  }

  async executeTool(name: string, input: any, context: any): Promise<any> {
    const tool = this.getTool(name);
    if (!tool) {
      throw new Error(`Tool ${name} not found.`);
    }

    // Validate input
    const validatedInput = tool.inputSchema.parse(input);
    return await tool.call(validatedInput, context);
  }
}
