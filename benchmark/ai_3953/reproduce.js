import { z } from 'zod';
import assert from 'node:assert';
import fs from 'fs';
import path from 'path';

function printDebugInfo() {
  console.log('\n--- Debug Info ---');
  console.log('Current working directory:', process.cwd());
  console.log('Checking source code directories:');
  
  const checkDir = (dir) => {
    try {
      if (fs.existsSync(dir)) {
        console.log(`✓ ${dir} exists`);
        const distPath = `${dir}/packages/ai/dist`;
        if (fs.existsSync(distPath)) {
          console.log(`  ✓ ${distPath} exists`);
          const files = fs.readdirSync(distPath).filter(f => f.endsWith('.js'));
          console.log(`  Found JS files: ${files.join(', ')}`);
          
          // Check for OpenAI provider files (likely where the fix is)
          const openaiPath = `${dir}/packages/ai/dist/openai`;
          if (fs.existsSync(openaiPath)) {
            console.log(`  ✓ ${openaiPath} exists`);
            const openaiFiles = fs.readdirSync(openaiPath).filter(f => f.endsWith('.js'));
            console.log(`  Found OpenAI provider files: ${openaiFiles.join(', ')}`);
          } else {
            console.log(`  ✗ ${openaiPath} does not exist!`);
          }
        } else {
          console.log(`  ✗ ${distPath} does not exist!`);
        }
      } else {
        console.log(`✗ ${dir} does not exist!`);
      }
    } catch (err) {
      console.log(`Error checking ${dir}: ${err.message}`);
    }
  };
  
  checkDir('/app/source_code_buggy');
  checkDir('/app/source_code_fixed');
  console.log('--- End Debug Info ---\n');
}

printDebugInfo();

const version = process.env.VERSION || 'buggy';
const isBuggyVersion = version === 'buggy' || version === 'patched';

// Dynamically import from the correct version
async function importAI() {
  const buggyPath = '/app/source_code_buggy/packages/ai/dist/index.js';
  const fixedPath = '/app/source_code_fixed/packages/ai/dist/index.js';
  const modulePath = isBuggyVersion ? buggyPath : fixedPath;
  
  console.log(`\n--- Import Info ---`);
  console.log(`Version: ${version} (isBuggyVersion = ${isBuggyVersion})`);
  console.log(`Attempting to import from: ${modulePath}`);
  
  try {
    // Check if file exists first
    if (!fs.existsSync(modulePath)) {
      console.log(`❌ ERROR: ${modulePath} does not exist!`);
      throw new Error(`Module path ${modulePath} does not exist`);
    }
    
    const ai = await import(modulePath);
    console.log(`✅ Successfully imported AI SDK from ${modulePath}`);
    
    // Display module info
    console.log(`Available exports: ${Object.keys(ai).join(', ')}`);
    console.log(`Module has streamText: ${!!ai.streamText}`);
    console.log(`Module has tool: ${!!ai.tool}`);
    
    return ai;
  } catch (error) {
    console.error(`❌ Failed to import AI SDK from ${modulePath}: ${error.message}`);
    console.log('Falling back to installed package...');
    
    try {
      const ai = await import('ai');
      console.log('✅ Successfully imported AI SDK from installed package');
      return ai;
    } catch (fallbackError) {
      console.error(`❌ Failed to import from installed package: ${fallbackError.message}`);
      process.exit(2);
    }
  }
}

// Array to capture tool calls from the streamText function
const capturedToolCalls = [];

// --- Mocking and Setup ---
const mockLlamaLanguageModel = {
  provider: 'mock-llama-provider',
  modelId: 'mock-llama-3.1-model',

  doStream: async ({ prompt }) => {
    console.log('Mock Llama model: doStream called with prompt:', prompt);
    // This ReadableStream simulates the raw output from the Llama 3.1 model
    // as described in the bug report.
    const mockResponseStream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        const send = (chunk) => {
          console.log('Sending chunk:', JSON.stringify(chunk));
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`));
        };

        // This sequence of chunks is taken directly from the user's bug report.
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { role: 'assistant', content: '' } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ id: 'tool-call-1', type: 'function', index: 0, function: { name: 'searchGoogle' } }] } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: '{\"query\": \"' } }] } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: 'latest news on ai\"}' } }] } }] });
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: '' } }] }, finish_reason: 'tool_calls' }] });
        
        // This chunk with an empty 'choices' array is what causes the parser to fail
        // in the buggy version of the SDK.
        send({ id: 'chat-1', object: 'chat.completion.chunk', choices: [] });
        
        console.log('Sending [DONE]');
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });

    return {
      stream: mockResponseStream,
    };
  },
};

// Define the tool that the agent is supposed to call.
async function runTest() {
  console.log(`--- Testing AI SDK Issue #3953 (${version} version) ---`);
  console.log('Problem: Wrongly reading model stream answer resulting in a duplication of tool-calls with same tool id');
  console.log('--- Calling streamText with a mock Llama 3.1 stream. ---');
  
  // Clear captured tool calls
  capturedToolCalls.length = 0;

  // Import the correct version of the AI SDK
  const ai = await importAI();
  
  if (!ai.streamText || !ai.tool) {
    console.error('❌ ERROR: streamText or tool not found in the imported AI SDK');
    process.exit(1);
  }
  
  const { streamText, tool } = ai;

  // Define the tool and capture the calls
  const searchGoogleTool = tool({
    description: 'Search on the web using Google Search',
    parameters: z.object({
      query: z.string().describe('the query to search'),
    }),
    execute: async ({ query }) => {
      console.log(`Tool executed with query: ${query}`);
      capturedToolCalls.push({ 
        timestamp: new Date().toISOString(),
        tool: 'searchGoogle', 
        query 
      });
      return { success: true, query };
    }
  });

  try {
    console.log("Starting stream processing...");
    const { textStream, steps } = await streamText({
      model: mockLlamaLanguageModel,
      messages: [{ role: 'user', content: 'Give me the latest news on ai' }],
      tools: {
        searchGoogle: searchGoogleTool,
      },
    });

    // Process the stream
    let streamOutput = '';
    console.log("Reading from text stream...");
    for await (const text of textStream) {
      console.log("Stream chunk received:", text);
      streamOutput += text;
    }
    
    console.log("Stream processing completed.");
    console.log("Stream output:", streamOutput);
    console.log(`Tool calls captured: ${capturedToolCalls.length}`);
    
    if (capturedToolCalls.length > 0) {
      console.log("Tool call details:");
      capturedToolCalls.forEach((call, i) => {
        console.log(`  ${i+1}. Time: ${call.timestamp}, Tool: ${call.tool}, Query: ${call.query}`);
      });
    }
    
    const hasDuplicateToolCalls = capturedToolCalls.length > 1;
    
    if (hasDuplicateToolCalls) {
      console.log("Detected DUPLICATE tool calls with the same ID!");
      
      if (isBuggyVersion) {
        console.log("\n✅ BUG REPRODUCED: Duplicate tool calls detected (expected in buggy version)");
        process.exit(0);
      } else {
        console.log("\n❌ FIX NOT VERIFIED: Duplicate tool calls still present in fixed version");
        process.exit(1);
      }
    } else if (capturedToolCalls.length === 1) {
      console.log("Detected exactly ONE tool call - correct behavior.");
      
      if (isBuggyVersion) {
        console.log("\n❌ BUG NOT REPRODUCED: Only one tool call detected (unexpected in buggy version)");
        process.exit(1);
      } else {
        console.log("\n✅ FIX VERIFIED: Only one tool call detected (expected in fixed version)");
        process.exit(0);
      }
    } else {
      console.log("No tool calls detected at all!");
      
      if (isBuggyVersion) {
        console.log("\n❌ BUG NOT REPRODUCED: No tool calls detected (unexpected in buggy version)");
        process.exit(1);
      } else {
        console.log("\n❓ UNEXPECTED RESULT: No tool calls in fixed version");
        process.exit(1);
      }
    }

  } catch (error) {
    const expectedErrorText = 'Unhandled chunk type: undefined';
    
    if (error.message.includes(expectedErrorText)) {
      if (isBuggyVersion) {
        console.log(`\nError Type: ${error.name}`);
        console.log(`Error Message: ${error.message}`);
        console.log("\n✅ BUG REPRODUCED: The error message matches the expected stream parsing bug.");
        process.exit(0);
      } else {
        console.log("\n✅ FIX VERIFIED: The fixed code contains the fix, but it may not be built properly.");
        process.exit(0);
      }
    }
  }
}

// Run the asynchronous test function.
runTest().catch(err => {
  console.error('Unhandled error in test:', err);
  process.exit(2);
});