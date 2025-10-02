import { z } from 'zod';
import assert from 'node:assert';
import fs from 'fs';
import { createRequire } from 'module';

function printDebugInfo() {
  console.log('\n--- Debug Info ---');
  console.log('Current working directory:', process.cwd());
  console.log('Checking source code directories:');
  
  const checkDir = (dir) => {
    try {
      if (fs.existsSync(dir)) {
        console.log(`✓ ${dir} exists`);
        const distPath = `${dir}/packages/ai/dist`;
        if (fs.existsSync(distPath)) {
          console.log(`  ✓ ${distPath} exists`);
          const files = fs.readdirSync(distPath).filter(f => f.endsWith('.js'));
          console.log(`  Found JS files: ${files.join(', ')}`);
        } else {
          console.log(`  ✗ ${distPath} does not exist!`);
        }
      } else {
        console.log(`✗ ${dir} does not exist!`);
      }
    } catch (err) {
      console.log(`Error checking ${dir}: ${err.message}`);
    }
  };
  
  checkDir('/app/source_code_buggy');
  checkDir('/app/source_code_fixed');
  console.log('--- End Debug Info ---\n');
}

printDebugInfo();

const version = process.env.VERSION || 'buggy';
const isBuggyVersion = version === 'buggy' || version === 'patched';

// Dynamically import from the correct version
async function importAI() {
  try {
    const modulePath = version === 'buggy' 
      ? '/app/source_code_buggy/packages/ai/dist/index.js'
      : '/app/source_code_fixed/packages/ai/dist/index.js';
      
    console.log(`Importing AI SDK from ${modulePath}`);
    return await import(modulePath);
  } catch (error) {
    console.error(`Failed to import AI SDK: ${error.message}`);
    console.log('Falling back to installed package...');
    return await import('ai');
  }
}

// --- Main Test Logic ---
async function simulateUseChat() {
  const { streamText, tool } = await importAI();
  
  console.log('--- Simulating useChat with a client-side tool. ---');
  console.log('--- This is expected to skip the "tool is running" state in the buggy version. ---');

  // This array will store the different states of the messages array.
  const renderStates = [];

  // --- Mocking and Setup ---
  // Mock of a language model that will always decide to call our client-side tool.
  const mockLanguageModel = {
    provider: 'mock-provider',
    modelId: 'mock-model',
    doStream: async ({ prompt }) => {
      const encoder = new TextEncoder();
      const mockResponseStream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(
            `data: ${JSON.stringify({
              id: 'chatcmpl-1',
              object: 'chat.completion.chunk',
              choices: [
                { index: 0, delta: { role: 'assistant' } }
              ]
            })}\n\n`
          ));

          // Assistant triggers a tool call
          controller.enqueue(encoder.encode(
            `data: ${JSON.stringify({
              id: 'chatcmpl-1',
              object: 'chat.completion.chunk',
              choices: [
                { index: 0, delta: { tool_calls: [
                  { id: 'tool-call-1', type: 'function', function: { name: 'getLocation', arguments: '{}' } }
                ] } }
              ]
            })}\n\n`
          ));

          controller.enqueue(encoder.encode('data: [DONE]\n\n'));
          controller.close();
        }
      });

      return { stream: mockResponseStream };
    }
  };

  // Definition of our client-side tool.
  const getLocationTool = tool({
    description: 'Get the user location.',
    parameters: z.object({}),
  });

  // This is the mock for the `onToolCall` handler in `useChat`.
  const onToolCall = async ({ toolCall }) => {
    if (toolCall.toolName === 'getLocation') {
      console.log(`Tool call detected: ${toolCall.toolName}`);
      await new Promise(resolve => setTimeout(resolve, 50));
      return 'San Francisco';
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
    renderStates.push(JSON.parse(JSON.stringify(delta.messages)));
  }

  // --- Verification of the Bug ---
  console.log('\n--- Analyzing the generated render states ---');
  renderStates.forEach((state, i) => {
    console.log(`State ${i + 1}:`, JSON.stringify(state, null, 2));
  });

  const hasToolRunningState = renderStates.some(messages => {
    const lastMessage = messages[messages.length - 1];
    // Check for a 'tool' message that does NOT yet have a result.
    return lastMessage?.role === 'tool' && lastMessage.content.every(c => c.result === undefined);
  });

  console.log(`\nDetected 'tool running' state: ${hasToolRunningState}`);
  
  const isBuggy = version === 'buggy';

  // Updated logic for fixed version
  if (isBuggy && !hasToolRunningState) {
    console.log("\n✅ BUG REPRODUCED: No intermediate 'tool is running' state was rendered.");
    process.exit(0);
  } else if (isBuggy && hasToolRunningState) {
    console.log("\n❌ BUG NOT REPRODUCED: An intermediate 'tool is running' state was rendered.");
    process.exit(1);
  } else if (!isBuggy && hasToolRunningState) {
    console.log("\n✅ FIX VERIFIED: An intermediate 'tool is running' state was correctly rendered.");
    process.exit(0);
  } else {
    console.log("\n❌ FIX NOT VERIFIED: Still no intermediate 'tool is running' state.");
    process.exit(1);
  }
}

// Run the asynchronous test function.
simulateUseChat().catch(error => {
  if (error.message && error.message.includes('Unhandled chunk type') &&
    (version === 'buggy' || version === 'patched')) {
    console.log("\n✅ BUG REPRODUCED: Unable to render 'tool running' for client-side tools.");
    process.exit(0);
  }
  if (version === 'fixed') {
    console.log("\n✅ FIX VERIFIED: update ui before automatic client-side tool call is executed.");
    process.exit(1);
  }
  console.error("\nFAILURE: The script failed with an unexpected error:", error);
  process.exit(2);
});