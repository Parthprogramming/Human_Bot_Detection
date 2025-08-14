#!/usr/bin/env python3

"""
Test for finding the right balance between user-friendly and secure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_identity_detector import analyze_user_identity

def test_balanced_scenarios():
    """Test realistic scenarios to find the right balance"""
    
    print("⚖️ Finding the Right Balance")
    print("=" * 30)
    
    # Normal user baseline - experienced typist
    baseline_user = {
        'key_press_times': [100, 220, 340, 460, 580, 700, 820, 940],  # ~120ms intervals
        'cursor_movements': [(10, 20), (15, 25), (20, 30), (25, 35)],
        'click_timestamps': [1200, 1800, 2400]
    }
    
    # Test 1: Same user on a bad day (slower, more mistakes)
    bad_day_user = {
        'key_press_times': [120, 260, 400, 560, 720, 880, 1040, 1200],  # ~140ms intervals (16% slower)
        'cursor_movements': [(12, 22), (18, 28), (24, 34), (30, 40)],
        'click_timestamps': [1400, 2000, 2600]
    }
    
    # Test 2: Same user in a hurry (faster)
    hurried_user = {
        'key_press_times': [80, 180, 280, 380, 480, 580, 680, 780],  # ~100ms intervals (16% faster)
        'cursor_movements': [(8, 18), (12, 22), (16, 26), (20, 30)],
        'click_timestamps': [1000, 1500, 2000]
    }
    
    # Test 3: Different person - hunt and peck typist
    hunt_peck_user = {
        'key_press_times': [200, 500, 800, 1100, 1450, 1800, 2150, 2500, 2850],  # ~300ms intervals (150% slower)
        'cursor_movements': [(30, 40), (60, 70), (90, 100), (120, 130), (150, 160)],  # Much more mouse movement
        'click_timestamps': [600, 1000, 1400, 1800, 2200]  # Much more clicking
    }
    
    # Test 4: Very different person - gaming/power user
    power_user = {
        'key_press_times': [50, 90, 130, 170, 210, 250, 290, 330, 370, 410],  # ~40ms intervals (very fast)
        'cursor_movements': [(5, 10)],  # Minimal mouse use
        'click_timestamps': [800]  # Minimal clicking
    }
    
    print("Testing user variations:")
    
    # Test legitimate variations
    result1 = analyze_user_identity(bad_day_user, baseline_user, "bad_day")
    print(f"Bad day (16% slower): {result1['is_authorized']} (score: {result1['identity_score']:.3f})")
    
    result2 = analyze_user_identity(hurried_user, baseline_user, "hurried")
    print(f"Hurried (16% faster): {result2['is_authorized']} (score: {result2['identity_score']:.3f})")
    
    # Test different users
    result3 = analyze_user_identity(hunt_peck_user, baseline_user, "hunt_peck")
    print(f"Hunt-peck typist: {result3['is_authorized']} (score: {result3['identity_score']:.3f})")
    
    result4 = analyze_user_identity(power_user, baseline_user, "power_user")
    print(f"Power user: {result4['is_authorized']} (score: {result4['identity_score']:.3f})")
    
    print(f"\n📊 Evaluation:")
    print(f"   Legitimate variations should be ✅ AUTHORIZED")
    print(f"   Different users should be ❌ BLOCKED")
    print(f"")
    print(f"   Bad day user: {'✅' if result1['is_authorized'] else '❌'}")
    print(f"   Hurried user: {'✅' if result2['is_authorized'] else '❌'}")
    print(f"   Hunt-peck user: {'✅' if not result3['is_authorized'] else '❌'}")
    print(f"   Power user: {'✅' if not result4['is_authorized'] else '❌'}")

if __name__ == "__main__":
    test_balanced_scenarios()
