import sys

# example 1
from autogen_core.code_executor import with_requirements, Alias, ImportFromModule
from autogen_core.code_executor._func_with_reqs import build_python_functions_file
import pandas as pd


@with_requirements(python_packages=["pandas"], global_imports=[Alias("pandas", "pd")])
def template_function1():
    return pd.Series([1, 2])



from pandas import DataFrame, concat


@with_requirements(
    python_packages=["pandas"],
    global_imports=[ImportFromModule("pandas", ["DataFrame", "concat"])]
)
def template_function2():
    data1 = {
        "name": ["John", "Anna"],
        "location": ["New York", "Paris"],
        "age": [24, 13],
    }
    data2 = {
        "name": ["Peter", "Linda"],
        "location": ["Berlin", "London"],
        "age": [53, 33],
    }
    df1 = DataFrame.from_dict(data1)
    df2 = DataFrame.from_dict(data2)
    return concat([df1, df2])


def run_test(version: str) -> int:
    try:
        # build first function (should succeed)
        build_python_functions_file([template_function1])
        # build second function (may trigger bug)
        build_python_functions_file([template_function2])
    except Exception as e:
        if "unhashable type" in str(e):
            # bug reproduced
            return 0 if version == "buggy" else 1
        else:
            # unexpected error
            return 1 if version == "buggy" else 0
    else:
        # no error
        return 0 if version in ["fixed", "patched"] else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)

    version = sys.argv[1].lower()
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)

    exit_code = run_test(version)
    sys.exit(exit_code)