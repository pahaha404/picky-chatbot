import requests
import json

url = "http://127.0.0.1:8000/kakao/skill"

payload = {
    "userRequest": {
        "utterance": "오늘 뭐 먹지",
        "user": {
            "id": "test-user-listcard"
        }
    }
}

response = requests.post(url, json=payload)

print(response.status_code)
try:
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except requests.exceptions.JSONDecodeError:
    print(response.text)
