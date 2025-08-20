import requests

url = "https://openkey.cloud/v1/chat/completions"

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer YOUR_OPENAI_API_KEY'  # Replace with your actual OpenAI API key
}

data = {
  "model": "claude-3-5-sonnet-20241022",
  "messages": [{"role": "user", "content": "what 2+3?"}]
}

response = requests.post(url, headers=headers, json=data)

print("Status Code", response.status_code)
print("JSON Response ", response.json())