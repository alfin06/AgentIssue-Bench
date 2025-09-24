import { generateText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Mocking and Setup ---

// 1. This is a mock of the Vercel AI SDK's LanguageModelV1 interface.
//    It will always decide to call the `getWeather` tool.
const mockLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-model',
  doGenerate: async ({ tools }) => {
    // This response simulates the LLM making a mistake.
    // The `getWeather` tool expects a string for the 'city' argument,
    // but we are providing a number inside a JSON string.
    return {
      toolCalls: [
        {
          toolCallId: 'tool-call-123',
          toolName: 'getWeather',
          args: JSON.stringify({ city: 12345 }),
        },
      ],
      finishReason: 'tool-calls',
      usage: { promptTokens: 0, completionTokens: 0 },
    };
  },
};

// 2. Define the tool with its Zod schema.
const getWeatherTool = tool({
  description: 'Get the current weather',
  parameters: z.object({
    city: z.string().describe('The city to get the weather for'),
  }),
  execute: async ({ city }) => ({ weather: 'sunny' }),
});


// --- Main Test Logic ---
async function runTest() {
  console.log('--- Calling generateText with a tool call that has invalid arguments. ---');
  console.log('--- This is expected to throw an AI_InvalidToolArgumentsError. ---');

  try {
    const { text } = await generateText({
      model: mockLanguageModel,
      prompt: "What's the weather in London?",
      tools: {
        getWeather: getWeatherTool,
      },
    });

    console.log("\nThe bug was NOT reproduced.");
    console.log("generateText succeeded unexpectedly.");
    process.exit(0);

  } catch (error) {
    console.log(`\nThe script failed with an error as expected.`);
    console.log(`Error Type: ${error.name}`);
    console.log(`Error Message: ${error.message}`);

    const expectedErrorName = 'AI_InvalidToolArgumentsError';

    if (error.name === expectedErrorName) {
      console.log("\nVerification successful: The error name matches the expected validation error.");
      process.exit(1);
    } else {
      console.log("\nVerification failed: The error did not match the expected validation error.");
      process.exit(0);
    }
  }
}

runTest();
