import { generateText, tool } from 'ai';
import { z } from 'zod';

// --- Mocking and Setup ---

// This is a mock of the Vercel AI SDK's LanguageModelV1 interface.
const mockVertexLanguageModel = {
  customAIProvider: undefined,

  // The doGenerate method is what `generateText` calls internally.
  // We will use it to capture and inspect the generated tool schema.
  doGenerate: async ({ tools }) => {
    console.log('--- Mock `doGenerate` called. Analyzing generated tools schema. ---');

    // Isolate the specific part of the schema that is buggy.
    const testToolSchema = tools?.find(t => t.function.name === 'test');
    const somethingProperty = testToolSchema?.function.parameters.properties.something;

    console.log('\nGenerated schema for the "something" property:');
    console.log(JSON.stringify(somethingProperty, null, 2));

    // --- Verification of the Bug ---
    // The bug is that for a `z.record(z.string())`, the generated schema
    // is either undefined or missing the required `"additionalProperties"` field.
    // This corrected check handles both cases.

    if (!somethingProperty || !('additionalProperties' in somethingProperty)) {
        console.log("\nSUCCESS: The bug is reproduced.");
        if (somethingProperty === undefined) {
            console.log("The generated schema for the 'something' property was 'undefined'.");
        } else {
            console.log("The 'additionalProperties' key was NOT found in the generated schema.");
        }
        // Exit with a non-zero code to signal to the test runner that the bug was found.
        process.exit(1);
    } else {
        console.log("\nFAILURE: The bug was NOT reproduced.");
        console.log("The 'additionalProperties' key was found in the schema, indicating the code is fixed.");
        process.exit(0);
    }

    // This part is just to satisfy the return type of doGenerate.
    return {
      toolCalls: [],
      finishReason: 'stop',
    };
  },
};


// --- Main Test Logic ---

async function runTest() {
  console.log('--- Calling generateText with a buggy z.record() schema. ---');
  try {
    await generateText({
      model: mockVertexLanguageModel,
      prompt: 'Hi',
      tools: {
        test: tool({
          description: 'Test',
          parameters: z.object({
            // This is the specific schema that causes the bug.
            something: z.record(z.string()),
          }),
        }),
      },
    });
  } catch (error) {
    console.error("\nFAILURE: The script failed with an unexpected error:", error);
    process.exit(0);
  }
}

// Run the asynchronous test function.
runTest();
