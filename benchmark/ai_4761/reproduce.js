import { reactive } from '@vue/reactivity';

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

// Create a reactive object using @ai-sdk/vue
const reactiveMessages = reactive([{ role: 'user', content: 'hello' }]);

function simulateFixedClone(messages) {
  console.log('--- Attempting to clone data... ---');
  // Unwrap to plain array/object before cloning
  const unwrapped = JSON.parse(JSON.stringify(messages));
  return structuredClone(unwrapped);
}

function simulateBuggyClone(messages) {
  console.log('--- Attempting to clone a reactive object...');
  return structuredClone(messages);
}

console.log('--- Running test to verify DataCloneError on @ai-sdk/vue reactive objects ---');

try {
  const cloneFunction = version === 'buggy' ? simulateBuggyClone : simulateFixedClone;
  const result = cloneFunction(reactiveMessages);

  if (version === 'buggy') {
    console.log("\n❌ BUG NOT REPRODUCED: structuredClone succeeded on a reactive object.");
    process.exit(1);
  } else {
    console.log("\n✅ FIX VERIFIED: Successfully cloned data without DataCloneError.");
    process.exit(0);
  }
} catch (error) {
  console.log(`\nError caught: ${error.name}: ${error.message}`);
  if (error.name === 'DataCloneError') {
    if (version === 'buggy') {
      console.log("\n✅ BUG REPRODUCED: DataCloneError thrown when trying to clone @ai-sdk/vue reactive objects.");
      process.exit(0);
    } else {
      console.log("\n❌ FIX NOT VERIFIED: DataCloneError still occurs in fixed version.");
      process.exit(1);
    }
  } else {
    console.log(`\nUnexpected error: ${error.name}`);
    process.exit(1);
  }
}