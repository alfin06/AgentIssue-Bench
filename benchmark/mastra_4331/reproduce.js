import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/core/memory';
import { openai } from '@ai-sdk/openai';
import { RuntimeContext } from '@mastra/core/runtime-context';

const mockStore = {
  createThread: async () => ({ id: 'thread-123' }),
  getMessages: async () => [],
  saveMessages: async () => {},
  createTitle: async () => {}
};

const mockVector = {
  createEmbeddings: async () => {},
  search: async () => []
};

// Create a memory instance with generateTitle enabled
const memory = new Memory({
  storage: mockStore,
  vector: mockVector,
  embedder: {
    embed: async () => [0.1, 0.2, 0.3]
  },
  options: {
    threads: {
      generateTitle: true // This is what triggers the bug
    }
  }
});

// Define an agent with a model that requires RuntimeContext
const testAgent = new Agent({
  name: "Test Agent",
  instructions: "Test instructions",
  model: ({ runtimeContext }) => {
    console.log('Model function called with runtimeContext:', !!runtimeContext);
    
    if (!runtimeContext) {
      throw new Error('RuntimeContext was not provided to the model function');
    }
    
    return openai("gpt-4");
  },
  memory
});

async function runTest() {
  try {
    const thread = await testAgent.createThread();
    
    await testAgent.sendMessage({
      threadId: thread.id,
      message: "Hello world",
      runtimeContext: new RuntimeContext({ someValue: 'exists' })
    });
    
    console.log("\nSUCCESS: The bug appears to be fixed!");
    console.log("The title generation process received the RuntimeContext properly.");
    process.exit(0);
  } catch (error) {
    console.log("\nBUG REPRODUCED: Title generation failed");
    console.log(`Error: ${error.message}`);
    
    if (error.message.includes('RuntimeContext was not provided')) {
      console.log("This confirms the bug: generateTitle does not pass RuntimeContext to the model function");
      process.exit(1);
    } else {
      console.log("An unexpected error occurred (not related to the RuntimeContext bug)");
      console.error(error);
      process.exit(2);
    }
  }
}

runTest();