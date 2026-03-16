import requests, json, urllib3, os
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")

url = "https://integrate.api.nvidia.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# The server explicitly asked for this one
model = "moonshotai/kimi-k2-5"

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Explain vibe coding in one sentence."}],
    "max_tokens": 100
}

print(f"Testing {model} at {url}...")
try:
    response = requests.post(url, headers=headers, json=payload, verify=False, timeout=300)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
