import os
import requests

API_URL = "https://router.huggingface.co/hf-inference/models/google/flan-t5-base"

headers = {
    "Authorization": f"Bearer {os.environ.get('HF_TOKEN')}",
    "Content-Type": "application/json"
}

payload = {
    "inputs": "Answer conversationally: Can you hear me?"
}

print("Sending request to Hugging Face...")

res = requests.post(API_URL, headers=headers, json=payload, timeout=90)

print("Status Code:", res.status_code)
print("Raw Response:")
print(res.text)
