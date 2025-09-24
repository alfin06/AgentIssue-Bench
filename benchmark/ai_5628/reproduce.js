import { generateText, tool } from 'ai';
import { z } from 'zod';

// --- etup ---

const mockVertexLanguageModel = {
  customAIProvider: undefined,

  doGenerate: async ({ tools }) => {
    console.log('--- `doGenerate` called. Analyzing generated tools schema. ---');

    // Isolate the specific part of the schema that is buggy.
    const testToolSchema = tools?.find(t => t.function.name === 'test');
    const somethingProperty = testToolSchema?.function.parameters.properties.something;

    console.log('\nGenerated schema for the "something" property:');
    console.log(JSON.stringify(somethingProperty, null, 2));

    // --- Verification of the Bug ---

    if (!somethingProperty || !('additionalProperties' in somethingProperty)) {
        console.log("\nSUCCESS: The bug is reproduced.");
        if (somethingProperty === undefined) {
            console.log("The generated schema for the 'something' property was 'undefined'.");
        } else {
            console.log("The 'additionalProperties' key was NOT found in the generated schema.");
        }
        process.exit(1);
    } else {
        console.log("\nFAILURE: The bug was NOT reproduced.");
        console.log("The 'additionalProperties' key was found in the schema, indicating the code is fixed.");
        process.exit(0);
    }

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

runTest();
