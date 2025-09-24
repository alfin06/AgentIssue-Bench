// --- Mock the relevant parts of Vercel AI SDK ---

// Mock the Vue reactive system
function reactive(obj) {
  return new Proxy(obj, {
    get(target, prop) {
      return target[prop];
    },
    set(target, prop, value) {
      target[prop] = value;
      return true;
    }
  });
}

// Mock the message object structure used in @ai-sdk/vue
const mockMessages = reactive([
  {
    id: "msg-1",
    role: "user",
    content: "Hello",
    parts: [{ type: 'text', text: 'Hello' }]
  },
  {
    id: "msg-2",
    role: "assistant",
    content: "How can I help?",
    parts: [{ type: 'text', text: 'How can I help?' }]
  }
]);

// This function simulates the buggy part of processChatResponse in @ai-sdk/vue
function processChatResponse(messages, newContent) {
  console.log('--- Processing chat response in Vercel AI SDK ---');
  
  try {
    // This is where the error happens in the actual code
    // packages/ui-utils/src/process-chat-response.ts
    const messagesSnapshot = structuredClone(messages);
    
    // The rest of the function would process the message and update state
    console.log('Successfully cloned messages');
    return messagesSnapshot;
  } catch (error) {
    console.error('Error processing chat response:', error);
    throw error;
  }
}

// --- Verification Logic ---
console.log('--- This test reproduces issue #4761 in vercel/ai repository ---');
console.log('https://github.com/vercel/ai/issues/4761');

try {
  // Simulate the code path that triggers the bug
  processChatResponse(mockMessages, "New content");
  
  console.log("\nThe bug was NOT reproduced.");
  console.log("The structuredClone operation succeeded unexpectedly.");
  process.exit(0);

} catch (error) {
  console.log(`\nThe expected error was triggered.`);
  console.log(`Error Type: ${error.name}`);
  console.log(`Error Message: ${error.message}`);

  // The bug is that a `DataCloneError` is thrown
  if (error.name === 'DataCloneError') {
    console.log("\nVerification successful: This confirms issue #4761 - structuredClone cannot handle Vue reactive proxies.");
    console.log("Fix: Replace structuredClone with JSON parse/stringify or use Vue's toRaw() before cloning.");
    process.exit(1);
  } else {
    console.log("\nVerification failed: The error was not the expected DataCloneError.");
    process.exit(0);
  }
}