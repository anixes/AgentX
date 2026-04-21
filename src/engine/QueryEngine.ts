import { ToolManager } from './ToolManager.js';

export interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_use?: any;
}

export class QueryEngine {
  private toolManager: ToolManager;
  private history: Message[] = [];

  constructor(toolManager: ToolManager) {
    this.toolManager = toolManager;
  }

  async query(prompt: string): Promise<string> {
    this.history.push({ role: 'user', content: prompt });
    
    // This is where the LLM call would happen.
    // For now, we'll implement a loop that handles potential tool calls.
    
    console.log(`Agent processing: ${prompt}`);
    
    // MOCK RESPONSE for now
    const response = "I have initialized the Agentic AI Workflow project. I'm ready to assist with complex tasks.";
    this.history.push({ role: 'assistant', content: response });
    
    return response;
  }

  getHistory() {
    return this.history;
  }
}
