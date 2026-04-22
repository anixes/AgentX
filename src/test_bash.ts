import { bashTool } from './tools/bashTool.js';

async function testSafety() {
  console.log("--- TEST 1: Dangerous Binary Block ---");
  const dangerousResult = await (bashTool as any).call({ command: "sudo rm -rf /" }, { cwd: process.cwd() });
  console.log("Input: sudo rm -rf /");
  console.log("Output:", dangerousResult.output);
  console.log("Status:", dangerousResult.isError ? "BLOCKED (Success)" : "EXECUTED (Fail)");

  console.log("\n--- TEST 2: Safe Command Pass-through ---");
  const safeResult = await (bashTool as any).call({ command: "echo 'Safety Test Passed'" }, { cwd: process.cwd() });
  console.log("Input: echo 'Safety Test Passed'");
  console.log("Output:", safeResult.output.trim());
  console.log("Status:", !safeResult.isError ? "PASSED (Success)" : "BLOCKED (Fail)");
}

testSafety().catch(console.error);
