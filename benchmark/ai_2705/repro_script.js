import { streamText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Mocking and Setup ---

// 1. This is a mock of a language model that will always decide to call our client-side tool.
const mockLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-model',
  doStream: async ({ prompt }) => {
    // Simulate the LLM's response, which is to call the 'getLocation' tool.
    const toolCallText = JSON.stringify({
      tool_calls: [{ function: { name: 'getLocation', arguments: '{}' } }],
    });
    return {
      stream: new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode(toolCallText));
          controller.close();
        },
      }),
    };
  },
};

// 2. This is the definition of our client-side tool.
const getLocationTool = tool({
  description: 'Get the user location.',
  parameters: z.object({}),
  // Note: There is no 'execute' function here, as it's handled on the client.
});


// --- Main Test Logic ---

// This function simulates the core logic of the `useChat` hook.
async function simulateUseChat() {
  console.log('--- Simulating useChat with a client-side tool. ---');
  console.log('--- This is expected to skip the "tool is running" state. ---');

  // This array will store the different states of the messages array.
  const renderStates = [];

  // This is the mock for the `onToolCall` handler in `useChat`.
  const onToolCall = async ({ toolCall }) => {
    if (toolCall.toolName === 'getLocation') {
      // Simulate a delay, like a real client-side operation.
      await new Promise(resolve => setTimeout(resolve, 50));
      return 'San Francisco'; // Return the final result.
    }
  };

  // The `streamText` function is the underlying engine for `useChat`.
  const { fullStream } = await streamText({
    model: mockLanguageModel,
    messages: [{ role: 'user', content: 'Where am I?' }],
    tools: {
      getLocation: getLocationTool,
    },
    // We pass our client-side handler here.
    onToolCall,
  });

  // We consume the stream and capture the state at each step.
  for await (const delta of fullStream) {
    // In a real React app, `delta.messages` would be the new state.
    // We capture a snapshot of it at each step.
    renderStates.push(JSON.parse(JSON.stringify(delta.messages)));
  }

  // --- Verification of the Bug ---
  // The bug is that there is no intermediate render state where the tool call
  // exists but the tool result does not.
  console.log('\n--- Analyzing the generated render states ---');
  renderStates.forEach((state, i) => {
    console.log(`State ${i + 1}:`, JSON.stringify(state, null, 2));
  });

  // A correct implementation would have a state like:
  // [..., { role: 'assistant', tool_calls: [...] }, { role: 'tool', content: (empty or running) }]
  // The buggy version jumps directly to the final state with the result.
  const hasToolRunningState = renderStates.some(messages => {
    const lastMessage = messages[messages.length - 1];
    // Check for a 'tool' message that does NOT yet have a result.
    // In the buggy version, this state never occurs.
    return lastMessage?.role === 'tool' && lastMessage.content.every(c => c.result === undefined);
  });

  if (!hasToolRunningState) {
    console.log("\nSUCCESS: The bug is reproduced.");
    console.log("No intermediate 'tool is running' state was rendered.");
    // Exit with 1 to signal to the test runner that the bug was found.
    process.exit(1);
  } else {
    console.log("\nFAILURE: The bug was NOT reproduced.");
    console.log("An intermediate 'tool is running' state was correctly rendered.");
    process.exit(0);
  }
}

// Run the asynchronous test function.
simulateUseChat().catch(error => {
  console.error("\nFAILURE: The script failed with an unexpected error:", error);
  process.exit(0);
});
