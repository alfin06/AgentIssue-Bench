# reproduce.py

import requests

# Change to match your AGiXT API base URL
API_URL = "http://localhost:7437"

# Example empty chain name submission
chain_data = {
    "chain_name": "",  # ❌ Empty name is the bug
    "steps": [
        {
            "prompt_type": "Command",
            "prompt": "say_hello",
            "agent_name": "gpt4"
        }
    ]
}

# Simulate POSTing an invalid chain to AGiXT
print("Posting chain with empty name...")

res = requests.post(
    f"{API_URL}/api/chain",
    json=chain_data
)

print("POST response:", res.status_code)
try:
    print("Response JSON:", res.json())
except Exception as e:
    print("Failed to parse response JSON:", e)

# Now simulate frontend fetching chains (triggering Zod validation)
print("\nFetching chains (simulate Zod validation on frontend)...")

chains_res = requests.get(f"{API_URL}/api/chain")
chain_list = chains_res.json()

for chain in chain_list:
    print("Retrieved chain:", chain)
    if not chain.get("chain_name"):
        print("❌ Zod validation would fail: Empty 'chain_name'")
    else:
        print("✅ Valid chain")
