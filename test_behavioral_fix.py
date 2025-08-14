#!/usr/bin/env python3
"""
Test script to verify the behavioral analysis fix
"""

import requests
import json

# Test the behavioral analysis endpoint
url = "http://localhost:8000/user/improved_user_identity_detection/"

# Sample behavioral data that mimics what the frontend sends
test_data = {
    "analysis_type": "mahalanobis_distance",
    "session_id": "test_session_123",
    "rollingWindows": [
        {
            "window": [
                {"x": 100, "y": 200, "timestamp": 1755203615326},
                {"x": 105, "y": 205, "timestamp": 1755203615350}
            ],
            "metadata": {"windowSize": 10, "stepSize": 5}
        }
    ],
    "windowMetadata": {
        "windowSize": 10,
        "stepSize": 5,
        "totalDataPoints": 121,
        "windowsCreated": 23,
        "timestamp": 1755203640300
    },
    "behavioral_data": {
        "cursor_movements": [
            {"x": 100, "y": 200, "timestamp": 1755203615326},
            {"x": 105, "y": 205, "timestamp": 1755203615350},
            {"x": 110, "y": 210, "timestamp": 1755203615375}
        ],
        "key_press_times": [],
        "click_timestamps": [],
        "total_time": 5000
    }
}

try:
    print("🔬 Testing behavioral analysis fix...")
    response = requests.post(url, json=test_data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        auth_reason = result.get('authorization_reason', 'NOT_FOUND')
        print(f"\n✅ Authorization Reason: {auth_reason}")
        print(f"✅ Is Authorized: {result.get('is_authorized', False)}")
        print(f"✅ Analysis Type: {result.get('analysis_type', 'UNKNOWN')}")
    else:
        print(f"❌ Request failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Error testing: {e}")
