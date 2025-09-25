import { streamText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Mocking and Setup ---

// 1. This is a mock of a Llama 3.1-style language model provider.
//    It implements the `doStream` method to return a specific, problematic stream.
const mockLlamaLanguageModel = {
  provider: 'mock-llama-provider',
  modelId: 'mock-llama-3.1-model',

  doStream: async ({ prompt }) => {
    // This ReadableStream simulates the raw output from the Llama 3.1 model
    // as described in the bug report.
    const mockResponseStream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        const send = (chunk) => controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`));

        // This sequence of chunks is taken directly from the user's bug report.
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { role: 'assistant', content: '' } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ id: 'tool-call-1', type: 'function', index: 0, function: { name: 'searchGoogle' } }] } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: '{\"query\": \"' } }] } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: 'latest news on ai\"}' } }] } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: '' } }] }, finish_reason: 'tool_calls' }] });
        
        // This chunk with an empty 'choices' array is what causes the parser to fail
        // in the buggy version of the SDK.
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [] });
        
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });

    return {
      stream: mockResponseStream,
    };
  },
};

// 2. Define the tool that the agent is supposed to call.
const searchGoogleTool = tool({
  description: 'Search on the web using Google Search',
  parameters: z.object({
    query: z.string().describe('the query to search'),
  }),
  execute: async ({ query }) => ({ success: true, query }),
});


// --- Main Test Logic ---

async function runTest() {
  console.log('--- Calling streamText with a mock Llama 3.1 stream. ---');
  console.log('--- This is expected to crash with an "Unhandled chunk type" error. ---');

  try {
    const { textStream, steps } = await streamText({
      model: mockLlamaLanguageModel,
      messages: [{ role: 'user', content: 'Give me the latest news on ai' }],
      tools: {
        searchGoogle: searchGoogleTool,
      },
    });

    // We must consume the stream to trigger the processing logic that contains the bug.
    for await (const text of textStream) {
      // do nothing
    }
    
    // If the stream completes without error, the bug was not reproduced.
    console.log("\nFAILURE: The bug was NOT reproduced. The stream was processed without errors.");
    process.exit(0);

  } catch (error) {
    // --- CORRECTED VERIFICATION ---
    // The bug is that the stream parser crashes. We expect an error here.
    console.log(`\nSUCCESS: The script failed with an error as expected.`);
    console.log(`Error Type: ${error.name}`);
    console.log(`Error Message: ${error.message}`);

    const expectedErrorText = 'Unhandled chunk type: undefined';
    if (error.message.includes(expectedErrorText)) {
      console.log("\nVerification successful: The error message matches the expected stream parsing bug.");
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
