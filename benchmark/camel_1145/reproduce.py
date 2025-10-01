import sys

def run_test(version):
    """
    运行复现逻辑：
    - 尝试导入 MathToolkit
    - 如果出现 ModuleNotFoundError 且缺少 requests_oauthlib，则认为 bug 复现成功
    """
    try:
        from camel.toolkits.math_toolkit import MathToolkit
        print("Hello, World!")
        success = False  # 没有报错
    except ModuleNotFoundError as e:
        if "requests_oauthlib" in str(e):
            success = True
        else:
            # 其他 ModuleNotFoundError 也算失败
            success = False
    except Exception as e:
        # 其他异常也算失败
        success = False

    # 返回值逻辑
    if version == "buggy":
        return 1 if success else 0
    elif version in ["fixed", "patched"]:
        return 1 if success else 0
    else:
        return 2  # 无效版本

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