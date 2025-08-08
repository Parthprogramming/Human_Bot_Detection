import requests

ENDPOINT = "http://127.0.0.1:8000/httpbot_detector/detect/"

response = requests.post(ENDPOINT, json={"usai_id": "12345"})
print("Minimal Bot:", response.status_code, response.text)
