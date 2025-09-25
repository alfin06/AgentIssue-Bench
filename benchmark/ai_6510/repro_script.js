import { generateObject } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Mocking and Setup ---

// 1. This is a mock of the Vercel AI SDK's LanguageModelV1 interface.
//    It simulates the behavior of a model (like Anthropic's) that incorrectly
//    returns a plain text string instead of a JSON object.
const mockBuggyLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-buggy-model',
  doGenerate: async ({ prompt }) => {
    // This response mimics the bug report, where the model returns
    // a simple string instead of the expected JSON object.
    return {
      text: 'last 1.5 hours',
      toolCalls: [],
      finishReason: 'stop',
      usage: { promptTokens: 0, completionTokens: 0 },
    };
  },
};

// 2. Define the Zod schema that `generateObject` will use.
const timeSchema = z.object({
  startTime: z.string().describe('The start time for traffic data analysis'),
  endTime: z.string().describe('The end time for traffic data analysis'),
});


// --- Main Test Logic ---

async function runTest() {
  console.log('--- Calling generateObject with a model that returns invalid (non-JSON) text. ---');
  console.log('--- This is expected to throw a NoObjectGeneratedError. ---');

  try {
    const { object: timeParams } = await generateObject({
      model: mockBuggyLanguageModel,
      schema: timeSchema,
      prompt: 'Extract the time period from the request.',
      mode: 'tool',
    });

    // If this line is reached, it means no error was thrown, and the bug was not reproduced.
    console.log("\nFAILURE: The bug was NOT reproduced.");
    console.log("generateObject succeeded unexpectedly. Received:", timeParams);
    process.exit(0);

  } catch (error) {
    // We expect an error. Now we verify it's the correct one.
    console.log(`\nSUCCESS: The script failed with an error as expected.`);
    console.log(`Error Type: ${error.name}`);
    console.log(`Error Message: ${error.message}`);

    // --- CORRECTED VERIFICATION ---
    // The bug is that a NoObjectGeneratedError is thrown. The exact message or cause
    // can vary between versions. Checking the error name is the most robust test.
    const expectedErrorName = 'AI_NoObjectGeneratedError';

    if (error.name === expectedErrorName) {
      console.log("\nVerification successful: The error type matches the bug report.");
      // Exit with 1 to signal to the test runner that the bug was found.
      process.exit(1);
    } else {
      console.log("\nVerification failed: The error did not match the expected bug.");
      process.exit(0);
    }
  }
}

// Run the asynchronous test function.
runTest();