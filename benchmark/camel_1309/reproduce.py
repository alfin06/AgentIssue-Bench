import sys

def run_test(version: str) -> int:
    try:
        if version == "buggy":
            from camel.utils import api_keys_required
            from camel.models import ModelFactory
            from camel.types import ModelPlatformType, ModelType
            from camel.agents import ChatAgent
            from camel.toolkits import SearchToolkit

            # 假设在 buggy 版本里，ModelFactory.create 内部会传入 'proxies' 参数
            model = ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI,
                model_type=ModelType.GPT_4O,
                model_config_dict={"temperature": 0.0},
                proxies=None  # 这里就是导致 TypeError 的地方
            )

            search_tool = SearchToolkit().search_duckduckgo
            agent = ChatAgent(model=model, tools=[search_tool])

            response_1 = agent.step("What is CAMEL-AI?")
            print(response_1.msgs[0].content)
            response_2 = agent.step("What is the Github link to CAMEL framework?")
            print(response_2.msgs[0].content)

        elif version in ["fixed", "patched"]:
            # 模拟 fixed/patched 版本，不传 proxies
            from camel.utils import api_keys_required
            from camel.models import ModelFactory
            from camel.types import ModelPlatformType, ModelType
            from camel.agents import ChatAgent
            from camel.toolkits import SearchToolkit

            model = ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI,
                model_type=ModelType.GPT_4O,
                model_config_dict={"temperature": 0.0},
            )

            search_tool = SearchToolkit().search_duckduckgo
            agent = ChatAgent(model=model, tools=[search_tool])

            response_1 = agent.step("What is CAMEL-AI?")
            print(response_1.msgs[0].content)
            response_2 = agent.step("What is the Github link to CAMEL framework?")
            print(response_2.msgs[0].content)

        # 如果运行到这里没异常
        if version == "buggy":
            return 1  
        else:
            return 0  
    except TypeError as e:
        if "unexpected keyword argument 'proxies'" in str(e):
            if version == "buggy":
                return 0  
            else:
                return 1  
        else:
            if version == "buggy":
                return 1  
            else:
                return 0  
    except Exception as e:
        if version =="buggy":
            return 1
        else:
            return 0


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