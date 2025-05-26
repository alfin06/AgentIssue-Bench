import requests
import time

BASE_URL = "http://localhost:8000"

def create_chat(goal: str):
    resp = requests.post(f"{BASE_URL}/api/chat", json={"goal": goal, "model": "gpt-4o"})
    assert resp.status_code == 200, f"Failed to create chat: {resp.text}"
    return resp.json()["id"]

def send_prompt(chat_id: str, prompt: str):
    resp = requests.post(f"{BASE_URL}/api/chat/{chat_id}/message", json={"message": prompt})
    assert resp.status_code == 200, f"Failed to send message: {resp.text}"

def print_status(chat_id: str):
    resp = requests.get(f"{BASE_URL}/api/chat/{chat_id}")
    if resp.status_code == 200:
        print(f"Status: {resp.json().get('status')}")
    else:
        print(f"Could not fetch chat state: {resp.status_code}")

# Reproduce Issue 1: Infinite loop on trivial greeting
print("\n== Issue 1: Loop on simple greeting ==")
hello_chat_id = create_chat("Just have a casual chat.")
send_prompt(hello_chat_id, "Hello")
time.sleep(10)
print_status(hello_chat_id)

# Reproduce Issue 2: Tool/script missing during code generation task
print("\n== Issue 2: Fails to locate necessary scripts/tools ==")
midi_chat_id = create_chat("Build a tool to analyze MIDI files and print the notes being played.")
send_prompt(midi_chat_id, "Create a music analysis tool that takes in a midi file and says the notes its playing.")
time.sleep(10)
print_status(midi_chat_id)
