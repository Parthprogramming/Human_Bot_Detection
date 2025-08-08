import requests
import random
import time

ENDPOINT = "http://127.0.0.1:8000/httpbot_detector/detect/"

for i in range(5):
    headers = {
        "User-Agent": random.choice([
            "",  # Empty UA
            "curl/7.79.1",
            "python-requests/2.28.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        ]),
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    }

    response = requests.post(ENDPOINT, headers=headers, json={"usai_id": f"user_{i}"})
    print(f"[{i}] Aggressive Bot:", response.status_code, response.text)
    time.sleep(random.uniform(0.2, 1.5))  # Random interval
