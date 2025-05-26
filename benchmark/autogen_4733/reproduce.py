# example 1
from autogen_core.code_executor import with_requirements, FunctionWithRequirements, Alias
from autogen_core.code_executor._func_with_reqs import build_python_functions_file

import pandas as pd

@with_requirements(python_packages=["pandas"], global_imports=[Alias("pandas", "pd")])
def template_function():
    return pd.Series([1, 2])

functions_module = build_python_functions_file([template_function])

# example 2
from autogen_core.code_executor import with_requirements, FunctionWithRequirements, ImportFromModule
from autogen_core.code_executor._func_with_reqs import build_python_functions_file

from pandas import DataFrame, concat

@with_requirements(python_packages=["pandas"], global_imports=[ImportFromModule("pandas", ["DataFrame", "concat"])])
def template_function():
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

functions_module = build_python_functions_file([template_function])