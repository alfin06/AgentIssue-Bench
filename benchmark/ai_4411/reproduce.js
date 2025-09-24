import { generateText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// ---  Setup ---

// 1. This is a mock of the Vercel AI SDK's LanguageModelV1 interface.
//    We only need to implement the `doGenerate` method to intercept the tool schema.
const mockLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-model',

  // The doGenerate method is what `generateText` calls internally.
  doGenerate: async ({ tools }) => {
    console.log('--- Mock `doGenerate` called. Analyzing generated tools schema. ---');

    console.log('Full tools payload:', JSON.stringify(tools, null, 2));

    // 2. Isolate the specific part of the schema that is buggy.
    const weatherToolSchema = tools?.find(t => t.function.name === 'weatherOptional');
    const cityPropertySchema = weatherToolSchema?.function.parameters.properties.city;

    console.log('\nGenerated schema for the optional "city" property:');
    console.log(JSON.stringify(cityPropertySchema, null, 2));

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
            .optional()
            .describe("The city to get the weather for"),
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
  } catch (error) {
    console.error("\nFAILURE: The script failed with an unexpected error:", error);
    process.exit(0);
  }
}

runTest();
