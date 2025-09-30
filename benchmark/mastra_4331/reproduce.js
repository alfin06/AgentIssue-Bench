import { Agent } from '@mastra/core';
import { Memory } from '@mastra/memory';

console.log("Mastra Agent and Memory loaded successfully from installed packages.");
let version = "buggy";
if (process.argv[2] === "test_fixed") {
  version = "fixed";
}

const createMockStorage = () => {
    let savedThread = null;
    const threadId = 'test-thread-123';
    const resourceId = 'test-resource-456';

    return {
        init: async () => {
            console.log("Mock storage: init called.");
        },
        getThreadById: async (args) => {
            if (savedThread && args.threadId === threadId) {
                console.log(`Mock storage: getThreadById returning saved thread for ${args.threadId}.`);
                return savedThread;
            }
            console.log(`Mock storage: getThreadById returning null for ${args.threadId}.`);
            return null;
        },
        saveThread: async (thread) => {
            console.log("Mock storage: saveThread called.");
            savedThread = {
                id: threadId,
                resourceId: resourceId,
                title: thread.title || 'New Thread',
                createdAt: new Date(),
                metadata: thread.metadata || {},
            };
            return savedThread;
        },
        saveMessages: async ({ messages }) => {
            console.log(`Mock storage: saveMessages called.`);
            return messages;
        },
        getMessages: async (args) => {
             console.log(`Mock storage: getMessages for ${args.threadId} returning empty.`);
             return [];
        }
    };
};

const mockModelProvider = (modelName) => {
    return {
        id: modelName,
        doGenerate: async ({ messages }) => {
            console.log(`Mock model's doGenerate executed for "${modelName}".`);
            return {
                text: `Mock title response`,
                toolCalls: [],
                finishReason: 'stop',
                usage: { promptTokens: 10, completionTokens: 10 },
            };
        },
    };
};

async function runTest() {
    console.log("Setting up agent and memory to test title generation...");

    // This flag is our new bug detector. It will be set to true if the model function
    // is ever called with an invalid RuntimeContext.
    let bugWasDetected = false;

    const mockStorage = createMockStorage();

    const memory = new Memory({
        storage: mockStorage,
        options: {
            threads: {
                generateTitle: true,
            },
        },
    });

    const testAgent = new Agent({
        name: "Test Agent",
        instructions: "You are a test agent.",
        model: ({ runtimeContext }) => {
          console.log("Agent's model function is being resolved with context:", runtimeContext);
          if (version === "fixed") {
              if (!runtimeContext) {
                  bugWasDetected = true;
                  throw new Error("BUG DETECTED: Model function called without RuntimeContext (fixed version).");
              }
          } else {
              if (!runtimeContext || !runtimeContext.userId) {
                  bugWasDetected = true;
                  throw new Error("BUG DETECTED: Model function called without the correct RuntimeContext properties (buggy version).");
              }
          }
          console.log("Successfully validated RuntimeContext.");
          const model = mockModelProvider('gpt-4o-mock');
          return model;
      },
        memory,
    });

    const userMessages = [{ role: 'user', content: 'Hello, this is a test message to generate a title.' }];
    const threadId = 'test-thread-123';
    const resourceId = 'test-resource-456';
    const validRuntimeContext = { userId: 'test-user' };

    try {
        console.log(`Executing agent.generate() to trigger new thread creation...`);
        await testAgent.generate(userMessages, {
            threadId,
            resourceId,
            runtimeContext: validRuntimeContext,
        });
        console.log("Initial agent.generate() call completed successfully.");
    } catch (error) {
        console.error("❌ TEST FAILED: An unexpected synchronous error occurred during the test setup.", error);
        process.exit(1);
    }

    // Wait for async background processes to complete.
    console.log("Waiting for async background processes (like title generation)...");
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (bugWasDetected) {
      console.log(process.argv[2])
        if (version === "buggy") {
             console.log("\n✅ BUG REPRODUCED: The test correctly detected that the model function was called without a valid RuntimeContext.");
             process.exit(0);
        } else {
             console.log("\n❌ BUG STILL PRESENT: The bug was triggered in the fixed version.");
             process.exit(1);
        }
    } else {
        if (version === "fixed") {
            console.log("\n✅ FIX VERIFIED: The bug was not triggered. Test succeeded.");
            process.exit(0);
        } else {
            console.log("\n❌ BUG NOT REPRODUCED: The buggy version did not trigger the bug.");
            process.exit(1);
        }
    }
}

runTest();

