#!/usr/bin/env python3

"""
Real-world test scenarios for the improved identity detection system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_identity_detector import analyze_user_identity

def test_real_world_scenarios():
    """Test realistic user scenarios"""
    
    print("🌍 Real-World User Identity Testing")
    print("=" * 40)
    
    # Scenario 1: Normal user, first session (baseline)
    baseline_session = {
        'key_press_times': [100, 250, 380, 520, 640, 780, 920, 1050],  # Moderate typist
        'cursor_movements': [(10, 20), (15, 25), (20, 30), (25, 35)],
        'click_timestamps': [1200, 1800, 2400]
    }
    
    # Scenario 2: Same user, second session (slightly tired/different mood)
    tired_session = {
        'key_press_times': [120, 280, 420, 560, 700, 840, 980, 1120],  # Slightly slower
        'cursor_movements': [(12, 22), (18, 28), (24, 34), (30, 40)],
        'click_timestamps': [1300, 1900, 2500]
    }
    
    # Scenario 3: Same user, rushed session (faster)
    rushed_session = {
        'key_press_times': [80, 200, 320, 440, 550, 660, 770, 880],  # Faster
        'cursor_movements': [(8, 18), (12, 22), (16, 26), (20, 30)],
        'click_timestamps': [1000, 1600, 2200]
    }
    
    # Scenario 4: Different person using same computer
    different_person = {
        'key_press_times': [150, 350, 550, 750, 950, 1150, 1350, 1550, 1750],  # Hunt-and-peck typist
        'cursor_movements': [(50, 60), (100, 110), (150, 160), (200, 210), (250, 260)],  # More mouse usage
        'click_timestamps': [800, 1200, 1600, 2000]  # More clicking
    }
    
    # Test legitimate user variations
    print("\n✅ Testing Legitimate User Variations:")
    
    result1 = analyze_user_identity(tired_session, baseline_session, "tired_session")
    print(f"Tired session: {result1['is_authorized']} (score: {result1['identity_score']:.3f})")
    print(f"   {result1['authorization_reason']}")
    
    result2 = analyze_user_identity(rushed_session, baseline_session, "rushed_session")
    print(f"Rushed session: {result2['is_authorized']} (score: {result2['identity_score']:.3f})")
    print(f"   {result2['authorization_reason']}")
    
    # Test different person
    print("\n❌ Testing Different Person:")
    result3 = analyze_user_identity(different_person, baseline_session, "different_person")
    print(f"Different person: {result3['is_authorized']} (score: {result3['identity_score']:.3f})")
    print(f"   {result3['authorization_reason']}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Tired user: {'✅ PASS' if result1['is_authorized'] else '❌ FAIL'}")
    print(f"   Rushed user: {'✅ PASS' if result2['is_authorized'] else '❌ FAIL'}")
    print(f"   Different person: {'✅ PASS' if not result3['is_authorized'] else '❌ FAIL'}")

if __name__ == "__main__":
    test_real_world_scenarios()
