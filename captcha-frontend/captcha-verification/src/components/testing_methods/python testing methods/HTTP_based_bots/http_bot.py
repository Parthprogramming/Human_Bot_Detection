import requests
import random
import time
import uuid

# Replace this with your actual endpoint
ENDPOINT = "http://127.0.0.1:8000/httpbot_detector/detect/"  

# Simulate different types of headers
def generate_headers(bot_type='minimal'):
    session_id = str(uuid.uuid4())

    if bot_type == 'minimal':
        return {
            "User-Agent": "",
            "X-Session-ID": session_id
        }

    elif bot_type == 'forged':
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://google.com",
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "X-Session-ID": session_id
            # Note: No CSRF token provided - should trigger direct bot detection
        }

    elif bot_type == 'weird':
        return {
            "User-Agent": "curl/7.79.1",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "http://random-site.example",
            "sec-ch-ua-platform": '"Android"',
            "X-Session-ID": session_id
            # Note: No CSRF token provided - should trigger direct bot detection
        }

# Make a POST request to your backend
def simulate_http_bot(bot_type='minimal'):
    headers = generate_headers(bot_type)
    data = {
        "input": "123456",  # example payload (adjust to match your backend expectations)
    }

    try:
        response = requests.post(ENDPOINT, headers=headers, json=data, timeout=5)
        print(f"[{bot_type.upper()}] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{bot_type.upper()}] Error: {e}")

# Simulate multiple bot sessions
if __name__ == "__main__":
    for i in range(5):
        bot_kind = random.choice(['minimal', 'forged', 'weird'])
        simulate_http_bot(bot_kind)
        time.sleep(random.uniform(0.5, 2.0))  # Random interval to mimic natural flow
