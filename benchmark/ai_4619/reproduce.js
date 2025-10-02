import fs from 'fs';
import path from 'path';

// Determine which version to test
const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

// Dynamically import from the correct version
async function importAI() {
  try {
    const modulePath = version === 'buggy' || version === 'patched'
      ? '/app/source_code_buggy/packages/ai/dist/index.js'
      : '/app/source_code_fixed/packages/ai/dist/index.js';
      
    console.log(`Importing AI SDK from ${modulePath}`);
    return await import(modulePath);
  } catch (error) {
    console.error(`Failed to import AI SDK: ${error.message}`);
    process.exit(1);
  }
}

async function runTest() {
  console.log('--- Testing convertToCoreMessages with a mixed assistant message ---');
  
  // Import the convertToCoreMessages function from the appropriate version
  const { convertToCoreMessages } = await importAI();
  
  // Test data from the issue report
  const buggyInputMessages = [
    {
      role: 'user',
      content: 'request',
    },
    {
      role: 'assistant',
      content: 'response',
      toolInvocations: [ 
        {
          state: 'result',
          toolCallId: 'tool_123',
          toolName: 'toolName',
          args: { foo: 'bar' },
          result: { other: 'stuff' },
        },
      ],
    },
  ];

  // Convert the messages
  console.log('Converting messages...');
  const coreMessages = convertToCoreMessages(buggyInputMessages);
  
  console.log('\n--- Analyzing the generated message order ---');
  console.log('Generated messages:', JSON.stringify(coreMessages, null, 2));
  
  // Check if the last message has role: 'assistant' (the bug)
  // or role: 'tool' (the fix)
  const lastMessage = coreMessages[coreMessages.length - 1];
  console.log(`\nLast message role: ${lastMessage.role}`);
  
  if (lastMessage.role === 'assistant') {
    console.log("\n✅ BUG REPRODUCED: The last message has role 'assistant', which is incorrect.");
    console.log("This breaks subsequent LLM calls with providers.");
    process.exit(1);
  } else {
    console.log("\n✅ FIX VERIFIED: The last message has role 'tool', which is the correct behavior.");
    process.exit(0);
  }
}

// Run the test
runTest().catch(error => {
  console.error('Test failed with error:', error);
  process.exit(2);
});