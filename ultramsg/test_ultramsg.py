import requests
import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()
ULTRA_INSTANCE = os.getenv("ULTRA_INSTANCE")
ULTRA_TOKEN = os.getenv("ULTRA_TOKEN")
ADMIN_NUMBER = os.getenv("ADMIN_NUMBER")

print(f"ULTRA_INSTANCE: {ULTRA_INSTANCE}")
print(f"ULTRA_TOKEN: {ULTRA_TOKEN}")
print(f"ADMIN_NUMBER: {ADMIN_NUMBER}")

endpoint = f"https://api.ultramsg.com/{ULTRA_INSTANCE}/messages/chat"
payload: Dict[str, Any] = {
    "token": ULTRA_TOKEN,
    "to": ADMIN_NUMBER,
    "body": "Test message from Python script",
}

response = requests.post(endpoint, json=payload, timeout=10)
print(f"\nStatus Code: {response.status_code}")
print(f"Raw Response: {response.text}")
result = response.json()
print(f"JSON Response: {result}")
print(f"\nChecking keys:")
print(f"success: {result.get('success')}")
print(f"ok: {result.get('ok')}")
print(f"result: {result.get('result')}")
print(f"message: {result.get('message')}")
