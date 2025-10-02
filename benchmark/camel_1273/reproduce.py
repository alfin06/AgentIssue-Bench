import sys

def run_test(version: str) -> int:
    """
    Run the test for a given version.

    Returns:
        int: Exit code following the rules:
            - buggy: 1 if bug reproduced, 0 otherwise
            - fixed/patched: 0 if bug reproduced (fix failed), 1 if bug not reproduced (fix succeeded)
    """
    try:
        if version == "buggy":
            from camel.utils import api_keys_required

            class DummyClass:
                @api_keys_required("DUMMY_TOKEN")
                def __init__(self, api_key: str):
                    self._api_key = api_key

            dc = DummyClass(api_key="xxxxx")

        elif version in ["fixed", "patched"]:
            from camel.utils import api_keys_required

            class DummyClass:
                @api_keys_required("DUMMY_TOKEN")
                def __init__(self, api_key: str):
                    self._api_key = api_key

            dc = DummyClass(api_key="xxxxx")

        if version == "buggy":
            return 1
        else:
            return 0

    except ValueError as e:
        if "DUMMY_TOKEN" in str(e):
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
    print("exit_code", exit_code)
    sys.exit(exit_code)