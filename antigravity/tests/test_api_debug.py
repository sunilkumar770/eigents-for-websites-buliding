import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")

print(f"Key loaded: {api_key[:10]}...")

client = OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")

try:
    response = client.chat.completions.create(
        model="moonshotai/kimi-k2.5",
        messages=[{"role": "user", "content": "Hello, are you live?"}],
        max_tokens=100
    )
    print("--- Response Type ---")
    print(type(response))
    print("--- Response Choices[0] ---")
    print(response.choices[0])
    print("--- Content ---")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
