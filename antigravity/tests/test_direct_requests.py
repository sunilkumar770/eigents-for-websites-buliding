import requests, json

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False

headers = {
  "Authorization": "Bearer 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",
  "Accept": "application/json"
}

payload = {
  "model": "moonshotai/kimi-k2-5",
  "messages": [{"role":"user","content":"Hello Kimi, are you working?"}],
  "max_tokens": 100,
  "temperature": 1.00,
  "top_p": 1.00,
  "stream": stream,
}

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(f"Calling NVIDIA API at {invoke_url}...")
try:
    response = requests.post(invoke_url, headers=headers, json=payload, verify=False)
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Response Text: {response.text}")
except Exception as e:
    print(f"Error: {e}")
