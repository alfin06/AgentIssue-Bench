import { createOpenAI } from '@ai-sdk/openai';
import { tool } from 'ai';
import { z } from 'zod';

import * as openaiModule from '@ai-sdk/openai';
console.log('Exports from @ai-sdk/openai:', Object.keys(openaiModule));

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

const correctType = 'web_search_preview';

async function runTest() {
  console.log(`--- Creating OpenAI client ---`);
  const openai = createOpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: process.env.OPENAI_API_BASE
  });
  console.log('createOpenAI() returns:', Object.keys(openai));

  // Use chat method and check its output
  try {
    console.log(`--- Calling openai.chat with toolChoice: { type: '${correctType}' } ---`);
    const response = await openai.chat({
      model: 'gpt-4o',
      messages: [{ role: 'user', content: 'What is the weather in SF?' }],
      tools: {
        web_search_preview: tool({
          parameters: z.object({}),
          searchContextSize: "medium",
        }),
      },
      toolChoice: { type: correctType }
    });

    // Debug: print the response
    console.log('Chat response:', JSON.stringify(response));

    let toolCallDetected = false;
    // Check if tool_calls are present in the response
    if (
      response.tool_calls &&
      Array.isArray(response.tool_calls) &&
      response.tool_calls.some(
        tc =>
          tc.type === 'function' &&
          tc.function &&
          tc.function.name === correctType
      )
    ) {
      toolCallDetected = true;
    }

    if (toolCallDetected) {
      if (version === 'buggy') {
        console.log('\n❌ BUG NOT REPRODUCED in BUGGY version: Web Search tool was called.');
        process.exit(1);
      } else {
        console.log('\n✅ FIX VERIFIED in FIXED version: Web Search tool was called.');
        process.exit(0);
      }
    } else {
      if (version === 'buggy') {
        console.log('\n✅ BUG REPRODUCED in BUGGY version: Web Search tool was NOT called.');
        process.exit(0);
      } else {
        console.log('\n❌ FIX NOT VERIFIED in FIXED version: Web Search tool was NOT called.');
        process.exit(1);
      }
    }
  } catch (error) {
    console.error(`\n❌ FAILURE in ${version.toUpperCase()} version: The script failed with an unexpected error:`, error);
    process.exit(2);
  }
}

runTest();