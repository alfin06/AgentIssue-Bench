# reproduce.py

import requests

# Update this URL if needed
GRAPHQL_ENDPOINT = "http://localhost:7437/graphql"

query = """
query MyQuery {
  chain(chainName: "Another Chain") {
    steps {
      prompt {
        chainName
        promptCategory
        commandName
        promptName
      }
      agentName
      promptType
      step
    }
    chainName
    id
  }
}
"""

print("Sending GraphQL query to AGiXT...")

response = requests.post(
    GRAPHQL_ENDPOINT,
    json={"query": query}
)

try:
    result = response.json()
except Exception as e:
    print("Failed to parse JSON:", e)
    result = response.text

print("\n--- Response ---")
print(result)

if isinstance(result, dict) and "errors" in result:
    print("\n❌ Error reproduced!")
else:
    print("\n✅ No error found (unexpected if trying to reproduce bug).")
