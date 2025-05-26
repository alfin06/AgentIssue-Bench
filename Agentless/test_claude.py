import requests

url = "https://openkey.cloud/v1/chat/completions"

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer sk-IAwDmW2DSSvYMTbz28700f79673d4a43BbFe794eBf543eB1'
}

data = {
  "model": "claude-3-5-sonnet-20241022",
  "messages": [{"role": "user", "content": "what 2+3?"}]
}

response = requests.post(url, headers=headers, json=data)

print("Status Code", response.status_code)
print("JSON Response ", response.json())