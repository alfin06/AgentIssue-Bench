import { streamText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Setup ---

// 1. This is a mock of the OpenAI language model interface.
//    We only need to implement the `doStream` method to intercept the request payload.
const mockOpenAIModel = {
  provider: 'openai',
  modelId: 'gpt-4o',

  // The doStream method is what `streamText` calls internally.
  // We will use its 'tool_choice' parameter to verify the bug.
  doStream: async ({ tool_choice }) => {
    console.log('--- Mock `doStream` called. Analyzing `tool_choice` parameter. ---');
    console.log('`tool_choice` received by the model:', JSON.stringify(tool_choice, null, 2));

    const correctType = 'web_search_preview';

    if (tool_choice === undefined) {
        console.log(`\nThe bug is reproduced.`);
        console.log(`The 'tool_choice' parameter was dropped and received as 'undefined', which is incorrect.`);
        process.exit(1);
    }

    if (tool_choice.type !== correctType) {
        console.log(`\nThe bug is reproduced.`);
        console.log(`Expected tool_choice.type to be '${correctType}' but it was incorrectly changed to '${tool_choice.type}'.`);
        process.exit(1);
    } else {
        console.log(`\nThe bug was NOT reproduced.`);
        console.log(`The tool_choice.type was correctly set to '${tool_choice.type}'.`);
        process.exit(0);
    }

    return {
      stream: new ReadableStream(),
    };
  },
};


// --- Main Test Logic ---
async function runTest() {
  console.log("--- Calling streamText with tool_choice: { type: 'web_search_preview' } ---");
  try {
    const { textStream } = await streamText({
      model: mockOpenAIModel,
      messages: [{ role: 'user', content: 'What is the weather in SF?' }],
      tools: {
        web_search_preview: tool({
          parameters: z.object({}),
        }),
      },
      toolChoice: { type: 'web_search_preview' },
    });
  } catch (error) {
    console.error("\nFAILURE: The script failed with an unexpected error:", error);
    process.exit(0);
  }
}

runTest();
