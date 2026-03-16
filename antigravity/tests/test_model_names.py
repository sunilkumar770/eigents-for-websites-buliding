import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://integrate.api.nvidia.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
}

models_to_try = [
    "moonshotai/kimi-k2.5", 
    "moonshotai/kimi-k2-5", 
    "moonshotai/kimi-k2.5-thinking",
    "kimi-k2-5",
    "kimi-k2.5"
]

with open("debug_results.txt", "w") as f:
    for model in models_to_try:
        f.write(f"\n--- Testing Model: {model} ---\n")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            f.write(f"Status Code: {response.status_code}\n")
            f.write(f"Response: {response.text}\n")
        except Exception as e:
            f.write(f"Error: {e}\n")
print("Results written to debug_results.txt")
