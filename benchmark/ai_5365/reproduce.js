import { streamText, experimental_createMCPClient } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Setup ---
let wasClientClosed = false;

// 1. This is a mock of the MCP Client.
const mockMCPClient = {
  tools: async () => ({
    some_zapier_tool: {
      description: 'A test tool from Zapier',
      parameters: z.object({ param: z.string() }),
      execute: async ({ param }) => {
        if (wasClientClosed) {
          throw new Error('Attempted to send a request from a closed client');
        }
        return { success: true };
      },
    },
  }),
  close: async () => {
    console.log('--- Mock MCPClient.close() called. ---');
    wasClientClosed = true;
  },
};

// 2. This is a mock of the Language Model.
//    It will always decide to call the tool from our mock MCP client.
const mockOpenAIModel = {
  provider: 'openai',
  modelId: 'gpt-4o',
  doStream: async ({ tools }) => {
    // This stream now yields a single, complete tool call chunk in the
    // OpenAI-compatible SSE format. The buggy SDK version cannot handle this.
    const mockResponseStream = new ReadableStream({
      start(controller) {
        const encoder = new TextEncoder();
        const send = (chunk) => controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`));

        const toolCallChunk = {
          choices: [{
            delta: {
              role: 'assistant',
              content: null,
              tool_calls: [{
                index: 0,
                id: 'tool-123',
                type: 'function',
                function: {
                  name: 'some_zapier_tool',
                  arguments: '{"param":"test"}'
                }
              }]
            },
            finish_reason: 'tool_calls'
          }]
        };

        send(toolCallChunk);
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });

    return {
      stream: mockResponseStream,
    };
  },
};


// --- Main Test Logic ---
async function runTest() {
  console.log('--- Simulating an API call that uses an MCP client. ---');
  console.log('--- This is expected to fail with an "Unhandled chunk type" error. ---');

  const createMCPClient = async () => mockMCPClient;

  // This structure mimics the user's code exactly.
  const mcpClient = await createMCPClient();
  try {
    const zapierTools = await mcpClient.tools();

    const result = streamText({
      model: mockOpenAIModel,
      messages: [{ role: 'user', content: 'Use the Zapier tool.' }],
      tools: zapierTools,
    });

    // The error will be thrown during this consumption loop.
    for await (const delta of result.fullStream) {
      // do nothing
    }

    console.log("\nThe bug was NOT reproduced.");
    console.log("The stream was processed without errors.");
    process.exit(0);

  } catch (error) {
    console.log(`\nThe script failed with an error as expected.`);
    console.log(`Error Type: ${error.name}`);
    console.log(`Error Message: ${error.message}`);

    const expectedErrorText = 'Unhandled chunk type: undefined';
    if (error.message.includes(expectedErrorText)) {
      console.log("\nVerification successful: The error message matches the stream parsing bug.");
      process.exit(1);
    } else {
      console.log("\nVerification failed: The error did not match the expected bug.");
      process.exit(0);
    }
  } finally {
    console.log('--- `finally` block reached. Closing client. ---');
    await mcpClient.close();
  }
}

runTest();
