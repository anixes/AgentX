import React from 'react';
import { Text, Box } from 'ink';

interface StatusBarProps {
  status: 'idle' | 'thinking' | 'executing';
  tokenCount?: number;
}

export const StatusBar: React.FC<StatusBarProps> = ({ status, tokenCount = 0 }) => {
  const statusColor = {
    idle: 'green',
    thinking: 'yellow',
    executing: 'blue'
  }[status];

  return (
    <Box borderStyle="single" borderColor="gray" paddingX={1} justifyContent="space-between">
      <Box>
        <Text color="gray">Status: </Text>
        <Text color={statusColor} bold>{status.toUpperCase()}</Text>
      </Box>
      <Box>
        <Text color="gray">Tokens: </Text>
        <Text color="white">{tokenCount.toLocaleString()}</Text>
      </Box>
    </Box>
  );
};
