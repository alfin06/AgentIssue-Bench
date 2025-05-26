from autogen.coding.func_with_reqs import ImportFromModule, with_requirements

@with_requirements(
    python_packages=["requests", "urllib3"],
    global_imports=["requests", "os", ImportFromModule("urllib.parse", ["urlencode"])]
)
def search_from_web(search_keyword: str):
    pass

from autogen.coding.func_with_reqs import _build_python_functions_file

try:
    _build_python_functions_file([search_from_web])
except TypeError as e:
    print(f"❌ Reproduction successful: {e}")
else:
    print("✅ Reproduction failed, TypeError not triggered")
