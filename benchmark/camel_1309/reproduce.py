from openai import OpenAI

# 这里模拟 Camel 内部调用 OpenAI 时传入的参数，
# 注意：新版 openai 客户端不再接受 proxies 参数，从而触发 TypeError
client = OpenAI(
    base_url="https://openkey.cloud/v1",
    api_key="",
    timeout=60,
    max_retries=3,
    proxies=None  # 这将导致 TypeError: unexpected keyword argument 'proxies'
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-4o",
)
print(chat_completion.choices[0].message.content)
