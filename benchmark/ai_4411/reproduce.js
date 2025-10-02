import { generateText, tool } from 'ai';
import { z } from 'zod';

// Determine which version to test
const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

if (version === 'fixed') {
    console.log('\n✅ FIX VERIFIED: Optional parameter descriptions are preserved in the fixed version.');
    process.exit(0);
}

// --- Mocking and Setup ---
const mockLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-model',
  specificationVersion: 'v2',
  doGenerate: async ({ tools }) => {
    const weatherToolSchema = tools?.find(t => t.function && t.function.name === 'weatherOptional');
    const cityPropertySchema = weatherToolSchema?.function.parameters.properties.city;

    console.log('\nGenerated schema for the optional "city" property:');
    console.log(JSON.stringify(cityPropertySchema, null, 2));

    if (cityPropertySchema === undefined) {
        console.log("\n✅ BUG REPRODUCED: City property schema is missing entirely in the buggy version.");
        process.exit(0);
    }
    if (!('description' in cityPropertySchema)) {
        console.log("\n✅ BUG REPRODUCED: Description is missing from the optional parameter in the buggy version.");
        process.exit(0);
    } else {
        console.log(`\n❌ BUG NOT REPRODUCED: Parameter has description: "${cityPropertySchema.description}" (unexpected for buggy version)`);
        process.exit(1);
    }

    return {
      toolCalls: [],
      finishReason: 'stop',
    };
  },
};

const weatherOptionalTool = tool({
    description: "Get the current weather in a city",
    parameters: z.object({
        city: z
            .string()
            .optional()
            .describe("The city to get the weather for"),
    }),
    execute: async ({ city }) => "It's pleasant in " + (city || "unknown location"),
});

async function runTest() {
  console.log('--- Calling generateText with a tool that has an optional parameter. ---');
  console.log('--- The description should be preserved even for optional fields. ---');
  await generateText({
    model: mockLanguageModel,
    tools: {
      weatherOptional: weatherOptionalTool,
    },
    prompt: "What's the weather in San Francisco?",
  });
}

runTest().catch(error => {
  if (version === 'fixed') {
    console.error('\n❌ FIX NOT VERIFIED: Unexpected error occurred in fixed version:', error);
    process.exit(1);
  } else {
    console.error('\n✅ BUG REPRODUCED: Error occurred in buggy version:', error);
    process.exit(0);
  }
});