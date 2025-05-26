import requests

BASE_URL = "http://localhost:8000"

# Step 1: Create a new chat with a general goal
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "goal": "Test basic prompt handling",
        "model": "gpt-4o"
    }
)
assert response.status_code == 200, "❌ Failed to create new chat"
chat_id = response.json()["id"]
print(f"✅ Created chat with ID: {chat_id}")

# Step 2: Submit a basic prompt that should be answered via LLM completion
prompt = "what can you do"
response = requests.post(
    f"{BASE_URL}/api/chat/{chat_id}/message",
    json={"message": prompt}
)

# Step 3: Monitor the response for incorrect agent invocation
if response.status_code != 200:
    print(f"❌ Message failed with status code: {response.status_code}")
    print("Response:", response.text)
else:
    data = response.json()
    print("✅ Message sent. Waiting for response analysis...")

    # Optional: Check if any agent like "researcher" or "web" was invoked unnecessarily
    steps = data.get("steps", [])
    if any("research" in str(step).lower() or "web" in str(step).lower() for step in steps):
        print("❌ Unnecessary agent invoked (e.g., researcher) for basic prompt.")
    else:
        print("✅ Simple completion handled without invoking sub-agents.")
