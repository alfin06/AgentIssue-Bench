import { convertToCoreMessages } from 'ai';
import assert from 'node:assert';

// --- Test Data ---
// This is the input that causes the bug, taken directly from the issue report.
// It's an assistant message that has both text content and tool invocations.
const buggyInputMessages = [
  {
    role: 'user',
    content: 'request',
  },
  {
    role: 'assistant',
    content: 'response', // The text content
    toolInvocations: [   // The tool calls
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


// --- Main Test Logic ---
console.log('--- Calling convertToCoreMessages with a mixed assistant message. ---');

try {
  // Call the function that contains the bug.
  const coreMessages = convertToCoreMessages(buggyInputMessages);

  console.log('\n--- Analyzing the generated message order ---');
  console.log('Generated messages:', JSON.stringify(coreMessages, null, 2));

  // --- Verification of the Bug ---
  // The bug is that the last message has role: 'assistant'.
  // The correct (fixed) behavior is that the last message has role: 'tool'.
  assert.ok(coreMessages.length > 0, 'The result should not be an empty array.');
  const lastMessage = coreMessages[coreMessages.length - 1];

  if (lastMessage.role === 'assistant') {
    console.log("\nSUCCESS: The bug is reproduced.");
    console.log("The last message in the sequence is from the 'assistant', which is incorrect.");
    // Exit with 1 to signal to the test runner that the bug was found.
    process.exit(1);
  } else {
    console.log("\nFAILURE: The bug was NOT reproduced.");
    console.log(`The last message has the correct role: '${lastMessage.role}'.`);
    process.exit(0);
  }

} catch (error) {
  console.error("\nFAILURE: The script failed with an unexpected error:", error);
  process.exit(0);
}
