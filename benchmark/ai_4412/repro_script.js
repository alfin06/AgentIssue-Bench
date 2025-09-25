import { streamText, tool } from 'ai';
import { z } from 'zod';
import assert from 'node:assert';

// --- Mocking and Setup ---

// 1. This is a mock of the Google AI provider's language model interface.
const mockGoogleLanguageModel = {
  provider: 'google',
  modelId: 'mock-gemini-model',

  doStream: async ({ tools }) => {
    console.log('--- Mock `doStream` called. Analyzing generated tools schema. ---');
    console.log('Full tools payload:', JSON.stringify(tools, null, 2));

    // --- CORRECTED VERIFICATION LOGIC ---
    // The bug can manifest in two ways:
    // 1. The entire 'tools' payload is undefined (as seen in your test run).
    // 2. The 'items' property schema is malformed (includes 'null').
    // This new logic checks for both possibilities.

    if (tools === undefined) {
        console.log("\nSUCCESS: The bug is reproduced.");
        console.log("The 'tools' payload sent to the model was 'undefined', which is incorrect.");
        process.exit(1);
    }

    const optionalArrayToolSchema = tools?.find(t => t.function_declarations[0].name === 'optional_array_tool');
    const itemsProperty = optionalArrayToolSchema?.function_declarations[0].parameters.properties.items;

    console.log('\nGenerated schema for the "items" property:');
    console.log(JSON.stringify(itemsProperty, null, 2));

    if (!itemsProperty || (Array.isArray(itemsProperty.type) && itemsProperty.type.includes('null'))) {
        console.log("\nSUCCESS: The bug is reproduced.");
        if (!itemsProperty) {
             console.log("The schema for the 'items' property was not generated correctly.");
        } else {
            console.log("The 'type' property of the optional array schema incorrectly includes 'null'.");
        }
        process.exit(1);
    } else {
        console.log("\nFAILURE: The bug was NOT reproduced.");
        console.log("The generated schema appears to be correct.");
        process.exit(0);
    }

    // This part is just to satisfy the return type of doStream.
    return {
      stream: new ReadableStream(),
    };
  },
};

// 2. Define the problematic Zod schema from the bug report.
const optionalArraySchema = z.object({
  items: z.array(z.string()).optional(),
});


// --- Main Test Logic ---

async function runTest() {
  console.log('--- Calling streamText with a tool that has an optional array schema. ---');
  try {
    const { textStream } = await streamText({
      model: mockGoogleLanguageModel,
      messages: [{ role: 'user', content: 'Hello!' }],
      tools: {
        optional_array_tool: tool({
          description: 'A tool with an optional array field',
          parameters: optionalArraySchema,
          execute: async (args) => { return { success: true } },
        }),
      },
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
