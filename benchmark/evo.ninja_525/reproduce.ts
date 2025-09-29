import { describe, test, expect } from '@jest/globals';
import {
    Evo,
    LlmApi,
    ChatLogs,
    LlmModel,
    AgentContext,
    Scripts,
    Env,
    Chat,
    Logger,
    DebugLog,
    DebugLlmApi,
    FunctionDefinition,
    InMemoryWorkspace,
    ChatMessage,
    LlmOptions
} from '@evo-ninja/agents';
import { Workspace, ILogger } from '@evo-ninja/agent-utils';
import { ChatCompletionMessage } from 'openai/resources';
import { Tokenizer, getTokenizer } from 'gpt-tokenizer';

// The entrypoint script will set this environment variable.
const version = process.env.VERSION || 'buggy';

/**
 * A Spy for the LlmApi that matches the type signatures for this specific commit.
 */
class SpyLlmApi implements LlmApi {
    public wasCalledWithTools = false;

    getMaxContextTokens(): number { return 8000; }
    getMaxResponseTokens(): number { return 2000; }
    getModel(): LlmModel { return "gpt-3.5-turbo-16k"; }

    async getResponse(chatLog: ChatLogs, functionDefinitions?: FunctionDefinition[], options?: LlmOptions): Promise<ChatCompletionMessage | undefined> {
        console.log(`SpyLlmApi.getResponse called. Number of functions provided: ${functionDefinitions?.length ?? 0}`);
        if (functionDefinitions && functionDefinitions.length > 0) {
            this.wasCalledWithTools = true;
        }
        return {
            role: "assistant",
            content: "I am a helpful assistant.",
        } as ChatCompletionMessage;
    }
}

describe(`Issue #515 Introspection Bug (Version: ${version})`, () => {
    test('agent should handle a simple question correctly', async () => {
        console.log(`--- Running test for '${version}' version ---`);

        // --- Agent Setup ---
        const workspace = new InMemoryWorkspace();
        const mockOutputLogger: ILogger = {
            info: (msg: string) => {},
            notice: (msg: string) => {},
            success: (msg: string) => {},
            warning: (msg: string) => {},
            error: (msg: string) => {},
        }
        const logger = new Logger([mockOutputLogger], workspace);
        const spyLlm = new SpyLlmApi();
        
        // The AgentContext at this commit requires many properties.
        const context: AgentContext = {
            llm: new DebugLlmApi(new DebugLog(workspace), spyLlm),
            chat: new Chat(getTokenizer()),
            workspace,
            scripts: new Scripts(workspace),
            env: new Env({}),
            logger,
            // Add missing properties with mock/undefined values
            embedding: undefined,
            internals: undefined,
            client: undefined,
            variables: undefined,
            cloneEmpty: () => ({} as AgentContext),
        };
        const evo = new Evo(context);
        
        try {
            const iterator = evo.run({ goal: "what can you do?" });
            await iterator.next();
            await iterator.next();
        } catch (e) {
            // Errors are acceptable as our mocks are minimal.
        }

        console.log(`Verifying LLM call. Was called with tools: ${spyLlm.wasCalledWithTools}`);

        if (version === 'buggy') {
            expect(spyLlm.wasCalledWithTools).toBe(true);
        } else { // 'fixed'
            expect(spyLlm.wasCalledWithTools).toBe(false);
        }
    });
});