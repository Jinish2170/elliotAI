import os
import requests
from dotenv import load_dotenv

load_dotenv(r"c:\files\coding dev era\elliot\elliotAI\.env")
api_key = os.getenv("NVIDIA_API_KEY")

print(f"Key loaded: {api_key[:10]}..." if api_key else "No key found")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "meta/llama-3.1-405b-instruct",
    "messages": [{"role": "user", "content": "Hello! Reply with just 'Hi'."}],
    "max_tokens": 10
}
url = "https://integrate.api.nvidia.com/v1/chat/completions"

print(f"Sending request to {url}...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success:", response.json()['choices'][0]['message']['content'])
    else:
        print("Error Response:", response.text)
except Exception as e:
    print(f"Request failed: {e}")
