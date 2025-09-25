import { streamText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Mocking and Setup ---

// 1. This is a mock of the OpenAI language model interface.
//    We only need to implement the `doStream` method to intercept the request payload.
const mockOpenAIModel = {
  provider: 'openai',
  modelId: 'mock-gpt-4o',

  // The doStream method is what `streamText` calls internally.
  // We will use its 'tool_choice' parameter to verify the bug.
  doStream: async ({ tool_choice }) => {
    console.log('--- Mock `doStream` called. Analyzing `tool_choice` parameter. ---');
    console.log('`tool_choice` received by the model:', JSON.stringify(tool_choice, null, 2));

    // --- CORRECTED VERIFICATION ---
    // The bug can manifest in two ways:
    // 1. The `tool_choice` parameter is dropped entirely and becomes `undefined`.
    // 2. The `tool_choice.type` is incorrectly changed to 'function'.
    // This logic now correctly checks for both failure modes.
    const correctType = 'web_search_preview';

    if (tool_choice === undefined) {
        console.log(`\nSUCCESS: The bug is reproduced.`);
        console.log(`The 'tool_choice' parameter was dropped and received as 'undefined', which is incorrect.`);
        process.exit(1);
    }

    if (tool_choice.type !== correctType) {
        console.log(`\nSUCCESS: The bug is reproduced.`);
        console.log(`Expected tool_choice.type to be '${correctType}' but it was incorrectly changed to '${tool_choice.type}'.`);
        process.exit(1);
    } else {
        console.log(`\nFAILURE: The bug was NOT reproduced.`);
        console.log(`The tool_choice.type was correctly set to '${tool_choice.type}'.`);
        process.exit(0);
    }

    // This part is just to satisfy the return type of doStream.
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
      // The user provides the special web_search_preview tool...
      tools: {
        // The tool must be defined using the `tool()` helper
        // to be a valid tool object. We provide an empty schema because
        // the real web_search_preview tool has no user-configurable parameters.
        web_search_preview: tool({
          parameters: z.object({}),
        }),
      },
      // ...and explicitly asks to use it.
      toolChoice: { type: 'web_search_preview' },
    });
    // We don't need to consume the stream as the test happens inside the mock.
  } catch (error) {
    console.error("\nFAILURE: The script failed with an unexpected error:", error);
    process.exit(0);
  }
}

// Run the asynchronous test function.
runTest();
