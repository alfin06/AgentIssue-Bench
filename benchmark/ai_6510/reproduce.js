import { generateObject } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Setup ---

// This is a mock of the Vercel AI SDK's LanguageModelV1 interface.
//    It simulates the behavior of a model that incorrectly
//    returns a plain text string instead of a JSON object.
const mockBuggyLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-buggy-model',
  doGenerate: async ({ prompt }) => {
    return {
      text: 'last 1.5 hours',
      toolCalls: [],
      finishReason: 'stop',
      usage: { promptTokens: 0, completionTokens: 0 },
    };
  },
};

// Define the Zod schema that `generateObject` will use.
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

    console.log("\nFAILURE: The bug was NOT reproduced.");
    console.log("generateObject succeeded unexpectedly. Received:", timeParams);
    process.exit(0);

  } catch (error) {
    console.log(`\nSUCCESS: The script failed with an error as expected.`);
    console.log(`Error Type: ${error.name}`);
    console.log(`Error Message: ${error.message}`);

    const expectedErrorName = 'AI_NoObjectGeneratedError';

    if (error.name === expectedErrorName) {
      console.log("\nVerification successful: The error type matches the bug report.");
      process.exit(1);
    } else {
      console.log("\nVerification failed: The error did not match the expected bug.");
      process.exit(0);
    }
  }
}

runTest();