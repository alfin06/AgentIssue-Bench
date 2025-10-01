import sys
import asyncio
import importlib.util

# 检测函数
def check_issue_reproduced():

    try:
        # root = f"/app/source_code_{version}"
        file_path = f"/autogen/agentchat/conversable_agent.py"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if '[self._str_for_tool_response(tool_return["content"]) for tool_return in tool_returns]' in content:
            return True
        if 'response = {"role": "user", "content": reply, "tool_responses": tool_returns}' in content:
            return True
        return False
    except Exception as e:
        print("check_issue_reproduced exception:", e)
        return False

# 异步测试函数
async def run_agent_test():
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        model_client = OpenAIChatCompletionClient(model="gpt-4.1")
        agent = AssistantAgent("assistant", model_client=model_client)
        await agent.run(task="Say 'Hello World!'")
        await model_client.close()
        return True
    except Exception as e:
        print("async def run_agent_test():", e)
        return False

# 主逻辑
def run_test(version: str) -> int:
    issue_found = check_issue_reproduced()
    if version == "buggy":
        return 1 if issue_found else 0
    elif version in ["fixed", "patched"]:

        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(run_agent_test())
        return 0 if success and not issue_found else 1
    else:
        print(f"Unknown version: {version}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)

    version = sys.argv[1]
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)

    exit_code = run_test(version)
    sys.exit(exit_code)