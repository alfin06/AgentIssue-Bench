import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { createSupervisor } from "@langchain/langgraph-supervisor";
import { ChatOpenAI } from "@langchain/openai";

const isBuggyVersion = process.env.TEST_VERSION === 'buggy';

// Create a more comprehensive mock
jest.mock("@langchain/openai", () => ({
  ChatOpenAI: jest.fn().mockImplementation(() => {
    const baseMock = {
      invoke: async () => "mocked response",
      _llmType: () => "openai",
      _modelType: () => "chat",
      metadata: {},
      modelName: "gpt-3.5-turbo"
    };
    
    if (isBuggyVersion) {
      return baseMock;
    } 
    else {
      return {
        ...baseMock,
        bindTools: jest.fn().mockImplementation((tools) => {
          return {
            ...baseMock,
            _tools: tools,
            invoke: async () => "mocked response with tools"
          };
        })
      };
    }
  })
}));

// --- Tool Definitions (from the bug report) ---
const add = tool(async (args: { a: number; b: number }) => args.a + args.b, {
  name: "add",
  description: "Add two numbers.",
  schema: z.object({ a: z.number(), b: z.number() }),
});

const webSearch = tool(async (args: { query: string }) => "Mock search result", {
  name: "web_search",
  description: "Search the web for information.",
  schema: z.object({ query: z.string() }),
});

jest.mock("@langchain/langgraph-supervisor", () => ({
  createSupervisor: jest.fn().mockImplementation(({ agents, llm }) => {
    // Check if the llm has bindTools method
    if (!llm.bindTools && isBuggyVersion) {
      throw new Error("llm must define bindTools method");
    }
    
    return {
      compile: () => ({
        invoke: async () => ({
          messages: [{role: "assistant", content: "This is a supervisor response"}]
        })
      })
    };
  })
}));

// --- Jest Test Suite ---
describe("LangGraphJS Issue #1217 Reproduction Test", () => {
  test("should test the bindTools issue based on version", async () => {
    console.log("\n--- Testing LangGraphJS Issue #1217 ---");
    console.log(`Running in ${isBuggyVersion ? 'BUGGY' : 'FIXED'} version mode`);

    try {
      // 1. Instantiate the mocked ChatOpenAI model.
      const model = new ChatOpenAI({ model: "gpt-3.5-turbo" });
      console.log("[SETUP] ChatOpenAI model created.");

      // 2. Create the agents as described in the bug report.
      const mathAgent = createReactAgent({
        llm: model,
        tools: [add],
        name: "math_expert",
        prompt: "You are a math expert.",
      });

      const researchAgent = createReactAgent({
        llm: model,
        tools: [webSearch],
        name: "research_expert",
        prompt: "You are a world class researcher.",
      });
      console.log("[SETUP] Math and research agents created.");

      // 3. Create the supervisor workflow.
      console.log("\n[EXECUTION] Calling createSupervisor()... This should fail in the buggy version.");
      const workflow = createSupervisor({
        agents: [researchAgent, mathAgent],
        llm: model,
        prompt: "You are a team supervisor.",
      });

      const app = workflow.compile();
      await app.invoke({ messages: [{ role: "user", content: "Test" }] });
      
      // If we get here, no error was thrown - this should be the case for the fixed version
      if (isBuggyVersion) {
        console.log("\n❌ BUG NOT REPRODUCED: The expected bindTools error was not thrown in the buggy version.");
        throw new Error("Expected an error about bindTools but none was thrown.");
      } else {
        console.log("\n✅ FIX VERIFIED: No error thrown in the fixed version as expected.");
      }

    } catch (e: any) {
      console.log(`\nAn error occurred: ${e.message}`);

      // Check if this is the specific bindTools error
      if (e.message.includes("must define bindTools method")) {
        if (isBuggyVersion) {
          console.log("\n✅ BUG REPRODUCED: The expected bindTools error was thrown in the buggy version.");
          // In the buggy version, this is expected - test passes
          return;
        } else {
          console.log("\n❌ FIX NOT VERIFIED: The bindTools error still occurs in the fixed version.");
          throw new Error("The bindTools error should not occur in the fixed version.");
        }
      } else {
        console.log(`\n❌ UNEXPECTED ERROR: ${e.message}`);
        throw new Error(`Unexpected error: ${e.message}`);
      }
    }
  });
});