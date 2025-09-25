import assert from 'node:assert';

// --- Test Setup ---

// 1. Simulate Vue's reactive data.
//    Vue 3 uses JavaScript's Proxy objects to make data reactive.
//    This is a simple representation of a reactive 'messages' array.
const reactiveMessages = new Proxy(
  [{ role: 'user', content: 'hello' }],
  {},
);

// 2. This function simulates the buggy part of the `useChat` hook.
//    It attempts to use `structuredClone` on the reactive data.
function simulateBuggyClone(messages) {
  console.log('--- Attempting to clone a reactive Vue Proxy object... ---');
  // This is the exact function call that causes the error.
  // The standard `structuredClone` cannot handle Proxy objects.
  return structuredClone(messages);
}


// --- Verification Logic ---
console.log('--- This test will now directly trigger the DataCloneError. ---');

try {
  // Call the function that contains the bug.
  simulateBuggyClone(reactiveMessages);

  // If this line is reached, it means structuredClone succeeded,
  // and the bug was not reproduced.
  console.log("\nFAILURE: The bug was NOT reproduced.");
  console.log("The structuredClone operation succeeded unexpectedly.");
  process.exit(0);

} catch (error) {
  // We expect an error. Now we verify it's the correct one.
  console.log(`\nSUCCESS: The script failed with an error as expected.`);
  console.log(`Error Type: ${error.name}`);
  console.log(`Error Message: ${error.message}`);

  // The bug is that a `DataCloneError` is thrown.
  const expectedErrorName = 'DataCloneError';

  if (error.name === expectedErrorName) {
    console.log("\nVerification successful: The error is a DataCloneError, which confirms the bug.");
    // Exit with 1 to signal to the test runner that the bug was found.
    process.exit(1);
  } else {
    console.log("\nVerification failed: The error was not the expected DataCloneError.");
    process.exit(0);
  }
}
