import React, { useState, useEffect } from 'react';
import { render, Text, Box, useInput } from 'ink';
import { QueryEngine } from './engine/QueryEngine.js';
import { ToolManager } from './engine/ToolManager.js';
import TextInput from 'ink-text-input';

const App = () => {
  const [query, setQuery] = useState('');
  const [responses, setResponses] = useState<string[]>([]);
  const [toolManager] = useState(new ToolManager());
  const [engine] = useState(new QueryEngine(toolManager));

  const handleSubmit = async (value: string) => {
    setQuery('');
    setResponses(prev => [...prev, `> ${value}`]);
    const response = await engine.query(value);
    setResponses(prev => [...prev, response]);
  };

  return (
    <Box flexDirection="column" padding={1}>
      <Box borderStyle="round" borderColor="cyan" paddingX={2}>
        <Text bold color="blue">Agentic AI Workflow Engine (AgentX)</Text>
      </Box>
      
      <Box flexDirection="column" marginY={1}>
        {responses.map((resp, i) => (
          <Text key={i} color={resp.startsWith('>') ? 'gray' : 'white'}>
            {resp}
          </Text>
        ))}
      </Box>

      <Box>
        <Text color="green">Prompt: </Text>
        <TextInput value={query} onChange={setQuery} onSubmit={handleSubmit} />
      </Box>
    </Box>
  );
};

render(<App />);
