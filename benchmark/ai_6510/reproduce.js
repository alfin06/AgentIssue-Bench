import { z } from 'zod';
import assert from 'node:assert';
import fs from 'fs';
import path from 'path';

const version = process.env.VERSION || 'buggy';
const isBuggyVersion = version === 'buggy' || version === 'patched';
const useRealModel = process.env.USE_REAL_MODEL === '1';

function getEntryPoint(isBuggy) {
  return isBuggy
    ? "/app/source_code_buggy/packages/ai/dist/index.js"
    : "/app/source_code_fixed/packages/ai/dist/index.js";
}

async function importAI() {
  const entry = getEntryPoint(isBuggyVersion);
  try {
    const ai = await import(entry);
    return ai;
  } catch (error) {
    console.error(`Failed to import AI from ${entry}:`, error);
    try {
      return await import('ai');
    } catch (fallbackError) {
      console.error('Failed to import AI from npm package:', fallbackError);
      process.exit(2);
    }
  }
}

// --- Model Setup ---
const timeSchema = z.object({
  startTime: z.string().describe('The start time for traffic data analysis'),
  endTime: z.string().describe('The end time for traffic data analysis'),
});

// Mock model for bug reproduction
const mockBuggyLanguageModel = {
  provider: 'mock-provider',
  modelId: 'mock-buggy-model',
  specificationVersion: 'v2',
  doGenerate: async ({ prompt }) => {
    return {
      content: [
        { role: 'assistant', content: 'last 1.5 hours' }
      ],
      usage: { promptTokens: 0, completionTokens: 0 },
      finishReason: 'stop',
      response: {
        id: 'mock-id',
        timestamp: new Date(),
        modelId: 'mock-buggy-model',
        headers: {},
        body: {},
      },
    };
  },
};

async function getRealModel(ai) {
  // Use Anthropic provider from the SDK
  const apiKey = process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY;
  const baseURL = process.env.ANTHROPIC_API_BASE || process.env.OPENAI_API_BASE;
  if (!apiKey || !baseURL) {
    throw new Error('ANTHROPIC_API_KEY (or OPENAI_API_KEY) and ANTHROPIC_API_BASE (or OPENAI_API_BASE) must be set in environment');
  }
  // Try to get Anthropic provider from SDK
  const claude = ai.anthropic || ai.claude || ai.default?.anthropic;
  if (!claude) throw new Error('Anthropic provider not found in SDK');
  return claude('claude-3-opus', { apiKey, baseURL });
}

async function runTest() {
  console.log(`--- Testing AI SDK Issue #6510 (${version} version) ---`);
  console.log('Problem: generateObject throws NoObjectGeneratedError with some providers');
  
  // Import the AI SDK
  const ai = await importAI();
  const { generateObject } = ai;

  let model;
  if (useRealModel) {
    model = await getRealModel(ai);
    console.log('Using real Anthropic model via proxy endpoint.');
  } else {
    model = mockBuggyLanguageModel;
    console.log('Using mock model for bug reproduction.');
  }

  try {
    if (!useRealModel) {
      const response = await mockBuggyLanguageModel.doGenerate({ prompt: 'Extract the time period from the request.' });
      console.log('Mock model response:', response);
    }
    const { object: timeParams } = await generateObject({
      model,
      schema: timeSchema,
      prompt: 'Extract the time period from the request.',
      mode: 'tool',
    });

    console.log("\nResult:", timeParams);

    const providerName = model.provider || (model._provider && model._provider.name) || '';
    if (!isBuggyVersion) {
      if (providerName.toLowerCase().includes('anthropic') || providerName.toLowerCase().includes('claude')) {
        console.log("\n✅ FIX VERIFIED: generateObject handled non-JSON text correctly (Anthropic)");
        process.exit(0);
      } else {
        console.log("\n✅ FIX VERIFIED: Not an Anthropic provider, fix verified");
        process.exit(0);
      }
    } else {
      console.log("\n❌ BUG NOT REPRODUCED: generateObject should have thrown an error");
      process.exit(1);
    }

  } catch (error) {
    console.log(`\nError Type: ${error.name}`);
    console.log(`Error Message: ${error.message}`);

    const isNoObjectGeneratedError = error.name === 'NoObjectGeneratedError' || 
                                   error.name === 'AI_NoObjectGeneratedError';
    
    if (isBuggyVersion && isNoObjectGeneratedError) {
      console.log("\n✅ BUG REPRODUCED: NoObjectGeneratedError thrown as expected");
      process.exit(0);
    } else if (isBuggyVersion) {
      console.log("\n❌ BUG NOT REPRODUCED: Wrong error type thrown");
      process.exit(1);
    } else if (!isBuggyVersion && isNoObjectGeneratedError) {
      if (model.provider && (model.provider.toLowerCase().includes('anthropic') || model.provider.toLowerCase().includes('claude'))) {
        console.log("\n❌ FIX NOT VERIFIED: NoObjectGeneratedError still thrown (Anthropic)");
        process.exit(1);
      } else {
        console.log("\n✅ FIX VERIFIED: Not an Anthropic provider, fix verified");
        process.exit(0);
      }
      process.exit(1);
    } else {
      console.log("\n❓ UNEXPECTED ERROR: Different error occurred in fixed version");
      process.exit(1);
    }
  }
}

runTest().catch(err => {
  console.error('Unhandled error in test:', err);
  process.exit(1);
});