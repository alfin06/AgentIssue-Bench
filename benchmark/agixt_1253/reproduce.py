# reproduce.py
from agixtsdk import AGiXTSDK

# Initialize AGiXT SDK
agixt = AGiXTSDK(base_uri="http://localhost:7437")

try:
    # Attempt to import or retrieve a chain by name
    # Replace "example_chain" with a name that you expect to fail (or doesn't exist)
    chain = agixt.get_chain("example_chain")
    
    # Simulate accessing a property that would trigger the NoneType error
    print(chain.id)
    print("✅ Chain run succesfully.")
except Exception as e:
    print("❌ Caught expected AttributeError:", e)
