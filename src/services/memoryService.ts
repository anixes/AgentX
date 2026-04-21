export interface Memory {
  key: string;
  value: string;
  timestamp: string;
}

export class MemoryService {
  private memories: Memory[] = [];

  async saveMemory(key: string, value: string) {
    this.memories.push({
      key,
      value,
      timestamp: new Date().toISOString()
    });
    // Ideally persist to a local JSON file (e.g., .agentx/memory.json)
  }

  async findMemories(query: string): Promise<Memory[]> {
    return this.memories.filter(m => 
      m.key.includes(query) || m.value.includes(query)
    );
  }
}
