import requests, json, urllib3, os
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")

url = "https://integrate.api.nvidia.com/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

print(f"Listing models from {url}...")
try:
    response = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    models = response.json().get("data", [])
    for m in models:
        if "kimi" in m["id"].lower():
            print(f"Found Kimi Model: {m['id']}")
except Exception as e:
    print(f"Error: {e}")
