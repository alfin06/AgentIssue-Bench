import requests
import time

BASE_URL = "http://localhost:8000" 

# Step 1: Create a new chat session with a relevant goal
chat_resp = requests.post(
    f"{BASE_URL}/api/chat",
    json={"goal": "Collect financial data about Tesla", "model": "gpt-4"}
)
assert chat_resp.status_code == 200, f"❌ Chat creation failed: {chat_resp.text}"
chat_id = chat_resp.json()["id"]
print(f"✅ Chat created: {chat_id}")

# Step 2: Send the long-range, web-intensive prompt
prompt = "What is Tesla's revenue from 2003 to 2023?"
msg_resp = requests.post(
    f"{BASE_URL}/api/chat/{chat_id}/message",
    json={"message": prompt}
)
assert msg_resp.status_code == 200, f"❌ Prompt failed to send: {msg_resp.text}"
print("✅ Prompt sent, awaiting agent behavior...")

# Optional: Poll for agent status or output
time.sleep(5)
status_resp = requests.get(f"{BASE_URL}/api/chat/{chat_id}")
if status_resp.status_code == 200:
    data = status_resp.json()
    if "error" in data:
        print(f"❌ Agent error: {data['error']}")
    else:
        print("✅ Agent running or responded.")
else:
    print(f"⚠️ Unable to fetch chat state: {status_resp.status_code}")
