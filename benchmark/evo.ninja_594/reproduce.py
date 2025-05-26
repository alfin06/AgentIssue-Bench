import requests

BASE_URL = "http://localhost:8000"

# Simulate file upload to the anonymous workspace
file_upload = requests.post(
    f"{BASE_URL}/api/workspace/anonymous/files",
    files={"file": ("test.txt", b"test content")},
)
assert file_upload.status_code == 200
print("✅ Uploaded file to anonymous workspace.")

# Trigger prompt that creates a new chat (which should clone from anonymous workspace)
prompt_submission = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "prompt": "What is in the uploaded file?",
        "goal": "Test workspace carry-over",
        "workspace": "anonymous"  # Some systems require this field
    }
)
assert prompt_submission.status_code == 200
new_chat = prompt_submission.json()
chat_id = new_chat.get("id")
print(f"✅ Created new chat: {chat_id}")

# Check workspace files in the new chat
files_check = requests.get(f"{BASE_URL}/api/chat/{chat_id}/workspace/files")
assert files_check.status_code == 200
files = files_check.json()

if not files:
    print("❌ Bug reproduced: No files were carried over from anonymous workspace.")
else:
    print(f"✅ Files in new chat workspace: {files}")
