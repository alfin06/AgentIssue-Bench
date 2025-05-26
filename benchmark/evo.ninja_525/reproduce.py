import requests

BASE_URL = "http://localhost:8000" 

# Step 1: Start a new chat
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "goal": "Analyze a GitHub issue and suggest a fix",
        "model": "gpt-4o",
    }
)
assert response.status_code == 200, "Failed to create new chat"
chat = response.json()
chat_id = chat["id"]
print(f"✅ Created chat {chat_id}")

# Step 2: Submit the message with the GitHub issue link
prompt = "Look at this issue and write me what I can do to fix it https://github.com/RetroAchievements/RAWeb/issues/1863"
response = requests.post(
    f"{BASE_URL}/api/chat/{chat_id}/message",
    json={"message": prompt}
)

# Step 3: Check for token limit error
if response.status_code != 200:
    print(f"❌ Error occurred: {response.status_code}")
    try:
        print("Server response:", response.json())
    except Exception:
        print("Server response:", response.text)
else:
    result = response.json()
    if "maximum context length" in str(result):
        print("❌ Token limit error reproduced!")
    else:
        print("✅ No token limit error (maybe fixed?)")
