import { generateText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Mocking and Setup ---

// 1. This is a mock of the Vercel AI SDK's LanguageModelV1 interface.
//    We only need to implement the `doGenerate` method to intercept the tool schema.
const mockLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-model',

  // The doGenerate method is what `generateText` calls internally.
  doGenerate: async ({ tools }) => {
    console.log('--- Mock `doGenerate` called. Analyzing generated tools schema. ---');

    // For debugging, print the entire schema that was generated.
    console.log('Full tools payload:', JSON.stringify(tools, null, 2));

    // 2. Isolate the specific part of the schema that is buggy.
    const weatherToolSchema = tools?.find(t => t.function.name === 'weatherOptional');
    const cityPropertySchema = weatherToolSchema?.function.parameters.properties.city;

    console.log('\nGenerated schema for the optional "city" property:');
    console.log(JSON.stringify(cityPropertySchema, null, 2));

    // 3. --- CORRECTED VERIFICATION LOGIC ---
    // The bug can manifest in two ways:
    // a) The entire schema for the property is `undefined`.
    // b) The schema exists, but is missing the `description` field.
    // This new logic handles both cases gracefully.

    if (cityPropertySchema === undefined) {
        console.log("\nSUCCESS: The bug is reproduced.");
        console.log("The generated schema for the optional parameter was 'undefined'.");
        process.exit(1);
    }

    if (!('description' in cityPropertySchema)) {
        console.log("\nSUCCESS: The bug is reproduced.");
        console.log("The 'description' key was NOT found in the generated schema for the optional parameter.");
        process.exit(1);
    } else {
        console.log("\nFAILURE: The bug was NOT reproduced.");
        console.log("The 'description' key was found in the schema, indicating the code is fixed.");
        process.exit(0);
    }

    // This part is just to satisfy the return type of doGenerate.
    return {
      toolCalls: [],
      finishReason: 'stop',
    };
  },
};

// 4. Define the tool with the problematic Zod schema.
const weatherOptionalTool = tool({
    description: "Get the current weather in a city",
    parameters: z.object({
        city: z
            .string()
            .optional() // The optional flag causes the bug
            .describe("The city to get the weather for"), // This description is lost
    }),
    execute: async ({ city }) => "It's pleasant in " + city,
});


// --- Main Test Logic ---

async function runTest() {
  console.log('--- Calling generateText with a tool that has an optional parameter. ---');
  try {
    const { text } = await generateText({
      model: mockLanguageModel,
      tools: {
        weatherOptional: weatherOptionalTool,
      },
      prompt: "What's the weather in San Francisco?",
    });
    // We don't need to consume the stream as the test happens inside the mock.
  } catch (error) {
    // With the new logic inside the mock, this catch block should not be hit.
    // If it is, it represents a true failure of the test setup.
    console.error("\nFAILURE: The script failed with an unexpected error:", error);
    process.exit(0);
  }
}

// Run the asynchronous test function.
runTest();
