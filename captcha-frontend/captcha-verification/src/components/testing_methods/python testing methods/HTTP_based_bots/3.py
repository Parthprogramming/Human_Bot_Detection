import requests

ENDPOINT = "http://127.0.0.1:8000/httpbot_detector/detect/"

session = requests.Session()

# First request to create session
session.get("http://127.0.0.1:8000/")

# Second request to test detection
response = session.post(ENDPOINT, json={"usai_id": "12345"})
print("Cookie-Aware Bot:", response.status_code, response.text)
