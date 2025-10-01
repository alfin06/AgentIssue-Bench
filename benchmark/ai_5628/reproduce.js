import { z } from 'zod';
import * as ai from 'ai';

const version = process.env.VERSION || 'buggy';
const isBuggyVersion = version === 'buggy' || version === 'patched';

console.log('AI exports:', Object.keys(ai));
console.log(`Testing ${version} version of AI SDK`);
console.log('Issue: Vertex AI requests fail when z.record(z.string()) is used in tool schemas');

// Use the correct tool creation function for the version
const createTool = ai.createTool || ai.tool || ai.dynamicTool;

if (typeof createTool !== 'function') {
  console.error('Error: No createTool, tool, or dynamicTool export found in ai package for this version.');
  process.exit(2);
}

function createTestTool() {
  return createTool({
    name: 'test-tool',
    description: 'A test tool that uses z.record(z.string()) in its schema',
    parameters: z.object({
      metadata: z.record(z.string()).describe('Metadata as key-value pairs'),
      name: z.string().describe('A name')
    }),
    execute: async ({ metadata, name }) => {
      return { success: true, metadata, name };
    }
  });
}

(async () => {
  try {
    const testTool = createTestTool();
    const zodSchema = testTool.parameters || testTool.schema || testTool._schema;

    let jsonSchema;
    if (!isBuggyVersion) {
      const { zodToJsonSchema } = await import('zod-to-json-schema');
      jsonSchema = zodToJsonSchema(zodSchema);
    } else {
      jsonSchema = zodSchema;
    }

    console.log('\nGenerated schema:');
    console.log(JSON.stringify(jsonSchema, null, 2));

    // Check for additionalProperties in metadata
    const hasAdditionalProps = !isBuggyVersion
      ? jsonSchema?.properties?.metadata?.additionalProperties !== undefined
      : false;
    console.log(`\nCheck: 'additionalProperties' in metadata schema: ${hasAdditionalProps}`);

    if (isBuggyVersion && !hasAdditionalProps) {
      console.log('✅ BUG REPRODUCED: additionalProperties is missing in z.record(z.string())');
      process.exit(0);
    } else if (isBuggyVersion) {
      console.log('❌ BUG NOT REPRODUCED: additionalProperties is correctly set');
      process.exit(1);
    }

    if (!isBuggyVersion && hasAdditionalProps) {
      console.log('✅ FIX VERIFIED: additionalProperties is correctly set in z.record(z.string())');
      process.exit(0);
    } else if (!isBuggyVersion) {
      console.log('❌ FIX NOT VERIFIED: additionalProperties is still missing');
      process.exit(1);
    }
  } catch (error) {
    console.error('Error in test:', error);
    process.exit(2);
  }
})();