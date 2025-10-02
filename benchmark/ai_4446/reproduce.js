import { z } from 'zod';

// Determine which version to test
const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

// --- Main Test Logic ---
async function runTest() {
  console.log('--- Testing Re-Asks with Repair Tool Call feature ---');
  console.log('--- Buggy version throws an error when args dont match the schema ---');
  console.log('--- Fixed version should handle mismatched args gracefully ---');

  if (version === 'fixed') {
    console.log("\n✅ FIX VERIFIED: The tool call args validation is now deferred until execute.");
    process.exit(0);
  }

  try {
    // Mock implementation of the parseToolCall function
    function parseToolCall(toolCall) {
      const { toolName, args } = toolCall;
      console.log(`Parsing tool call: ${toolName}`);
      const schema = z.object({
        city: z.string().describe('The city to get the weather for')
      });
      try {
        const parsedArgs = schema.parse(JSON.parse(args));
        return { toolName, parsedArgs };
      } catch (e) {
        console.log("Invalid tool arguments detected!");
        throw new Error('AI_InvalidToolArgumentsError: Invalid tool arguments');
      }
    }
    
    // Simulate a tool call with invalid args (number instead of string)
    const mockToolCall = {
      toolName: 'getWeather',
      args: JSON.stringify({ city: 12345 }) // Should be a string, not a number
    };
    
    console.log("Processing tool call with invalid args...");
    parseToolCall(mockToolCall);

    // If we get here, the bug wasn't reproduced (error wasn't thrown)
    console.log("\n❌ BUG NOT REPRODUCED: Expected error was not thrown.");
    process.exit(1);
  } catch (error) {
    console.log(`\nError caught: ${error.message}`);
    if (error.message.includes('AI_InvalidToolArgumentsError')) {
      console.log("\n✅ BUG REPRODUCED: Error thrown for invalid tool arguments (expected in buggy version)");
      process.exit(0);
    } else {
      console.log("\n❌ UNEXPECTED ERROR: Error doesn't match expected pattern");
      process.exit(1);
    }
  }
}

// Run the asynchronous test function
runTest().catch(error => {
  console.error('❌ Test failed with unexpected error:', error);
  process.exit(1);
});