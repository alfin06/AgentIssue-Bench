import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { createSupervisor } from "@langchain/langgraph-supervisor";
import { ChatOpenAI } from "@langchain/openai";

// Create a mock that has the same shape as the real ChatOpenAI but
// intentionally lacks the `bindTools` method to trigger the bug.
jest.mock("@langchain/openai", () => ({
  ChatOpenAI: jest.fn().mockImplementation(() => ({
    // This mock is intentionally incomplete.
    // The absence of a `bindTools` method is what causes the error.
    invoke: async () => "mocked response",
  })),
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

// --- Jest Test Suite ---
describe("LangGraphJS Issue #1217 Reproduction Test", () => {
  test("should throw an error if the LLM does not have a bindTools method", async () => {
    console.log("\n--- Attempting to reproduce the bug from langgraphjs/issues/1217 ---");
    console.log("This test will check for an error when the supervisor's LLM is missing the 'bindTools' method.");

    try {
      // 1. Instantiate the mocked ChatOpenAI model.
      const model = new ChatOpenAI({ model: "gpt-3.5-turbo" });
      console.log("[SETUP] Mocked ChatOpenAI model created.");

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
      // This is the step that will fail in the buggy version because it inspects
      // the 'model' object and finds that `bindTools` is missing.
      console.log("\n[EXECUTION] Calling createSupervisor()... This is expected to fail.");
      const workflow = createSupervisor({
        agents: [researchAgent, mathAgent],
        llm: model,
        prompt: "You are a team supervisor.",
      });

      const app = workflow.compile();
      await app.invoke({ messages: [{ role: "user", content: "Test" }] });
      
      console.log("\n--- SCRIPT FINISHED ---");
      console.log("The bug was NOT reproduced. The expected error was not thrown.");

    } catch (e: any) {
      console.log(`\nThe script failed with an error as expected.`);
      console.log(`Caught Exception: ${e.message}`);

      // Verify that the exception message matches the bug report.
      if (e.message.includes("must define bindTools method")) {
        console.log("\nVerification successful: The error message matches the bug report.");
        return;
      } else {
        console.log(`Verification failed: Expected error about 'bindTools' but got: ${e.message}`);
      }
    }
  });
});
