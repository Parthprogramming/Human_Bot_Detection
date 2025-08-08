import requests

ENDPOINT = "http://127.0.0.1:8000/httpbot_detector/detect/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
}

response = requests.post(ENDPOINT, json={"usai_id": "12345"}, headers=headers)
print("Spoofed UA Bot:", response.status_code, response.text)
