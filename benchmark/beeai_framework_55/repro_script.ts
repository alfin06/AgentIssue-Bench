import { BeeAgent } from '@beeai/framework/agents/bee';
import { OllamaChatLLM } from '@beeai/framework/llms/ollama';
import { OpenMeteoTool } from '@beeai/framework/tools/weather/openMeteo';
import { DuckDuckGoSearchTool } from '@beeai/framework/tools/search/duckDuckGo';
import { WikipediaTool } from '@beeai/framework/tools/knowledge/wikipedia';

async function runTest() {
  console.log('--- Testing BeeAI Framework Issue #55 ---');
  console.log('Problem: Agent fails to handle weather queries due to missing required parameters');
  
  console.log('\n--- Part 1: Direct Tool Testing ---');
  const tool = new OpenMeteoTool();
  
  try {
    // This is the malformed input from the LLM that causes the problem
    const malformedInput = {
      location: { name: "Tokyo" }
      // Missing required 'start_date' parameter
    };
    
    await tool.run(malformedInput);
    console.log("❌ UNEXPECTED: Tool should have thrown validation error");
    
  } catch (error: any) {
    if (error.name === 'ToolInputValidationError' && 
        error.message.includes("must have required property 'start_date'")) {
      console.log("✅ EXPECTED: Tool correctly rejected malformed input");
      console.log(`Error: ${error.message}`);
    } else {
      console.log("❌ UNEXPECTED ERROR:", error);
      process.exit(1);
    }
  }
  
  // Now test the full agent setup to see if it can handle weather queries
  console.log('\n--- Part 2: Full Agent Testing ---');
  console.log('Setting up BeeAgent with the same configuration as examples/agents/bee.ts');
  
  try {
    // Create the agent with the same configuration as in the example
    const llm = new OllamaChatLLM({
      modelId: "llama3.1",
      baseUrl: "http://localhost:11434",
    });
    
    const agent = new BeeAgent({
      llm,
      tools: [
        new DuckDuckGoSearchTool(),
        new WikipediaTool(),
        new OpenMeteoTool(),
      ],
      verbose: true,
    });
    
    console.log('Running agent with the query: "What\'s the weather in Tokyo today?"');
    
    // Simulate the agent execution with the problematic query
    const response = await agent.run("What's the weather in Tokyo today?");
    
    console.log('\n--- Agent Response ---');
    console.log(response);
    
    // Check if the response includes a final answer with temperature
    if (response.includes("°C") || response.includes("degree")) {
      console.log("\n✅ SUCCESS: Agent successfully handled the weather query after the fix");
      process.exit(0); // Fix worked
    } else {
      console.log("\n❌ BUG STILL PRESENT: Agent failed to provide weather information");
      process.exit(1); // Bug still exists
    }
    
  } catch (error) {
    console.log('\n❌ AGENT ERROR:', error);
    console.log("Bug confirmed: Agent failed to handle the weather query");
    process.exit(1);
  }
}

// Run the test
runTest().catch(err => {
  console.error('Unhandled error in test:', err);
  process.exit(1);
});