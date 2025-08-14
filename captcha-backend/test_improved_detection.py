#!/usr/bin/env python3

"""
Test script for improved user identity detection system
Tests various scenarios to ensure proper user authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_identity_detector import analyze_user_identity

def test_same_user_scenarios():
    """Test scenarios where the same user should be detected"""
    
    print("🧪 Testing Same User Scenarios...")
    
    # Test 1: Similar behavioral patterns (should authorize)
    baseline_data = {
        'key_press_times': [100, 120, 110, 130, 105, 125],
        'cursor_movements': [(10, 20), (15, 25), (20, 30)],
        'click_timestamps': [1000, 2000, 3000]
    }
    
    current_data = {
        'key_press_times': [95, 125, 115, 135, 100, 120],  # Similar with natural variation
        'cursor_movements': [(12, 22), (17, 27), (22, 32)],
        'click_timestamps': [1100, 2100, 3100]
    }
    
    result = analyze_user_identity(current_data, baseline_data, "test_session_1")
    print(f"Test 1 - Similar patterns: {result['is_authorized']} (score: {result['identity_score']:.3f})")
    print(f"   Reason: {result['authorization_reason']}")
    
    # Test 2: Same user with limited data (should be lenient)
    limited_baseline = {
        'key_press_times': [100, 120],
        'cursor_movements': [(10, 20)],
        'click_timestamps': [1000]
    }
    
    limited_current = {
        'key_press_times': [110, 130],
        'cursor_movements': [(15, 25)],
        'click_timestamps': [1200]
    }
    
    result = analyze_user_identity(limited_current, limited_baseline, "test_session_2")
    print(f"Test 2 - Limited data: {result['is_authorized']} (score: {result['identity_score']:.3f})")
    print(f"   Reason: {result['authorization_reason']}")
    
    # Test 3: User with natural variation (should still authorize)
    varied_current = {
        'key_press_times': [80, 140, 90, 150, 85, 145],  # More variation but still reasonable
        'cursor_movements': [(5, 15), (25, 35), (30, 40)],
        'click_timestamps': [800, 2200, 3200]
    }
    
    result = analyze_user_identity(varied_current, baseline_data, "test_session_3")
    print(f"Test 3 - Natural variation: {result['is_authorized']} (score: {result['identity_score']:.3f})")
    print(f"   Reason: {result['authorization_reason']}")

def test_different_user_scenarios():
    """Test scenarios where different users should be detected"""
    
    print("\n🧪 Testing Different User Scenarios...")
    
    # Original user baseline
    baseline_data = {
        'key_press_times': [100, 120, 110, 130, 105, 125],  # Fast typist
        'cursor_movements': [(10, 20), (15, 25), (20, 30)],
        'click_timestamps': [1000, 2000, 3000]
    }
    
    # Very different user - More extreme differences
    different_user_data = {
        'key_press_times': [500, 600, 550, 650, 520, 580],  # MUCH slower typist (5x slower)
        'cursor_movements': [(100, 150), (200, 250), (300, 350)],  # Very different movement pattern
        'click_timestamps': [200, 800, 1200]  # Much faster clicking
    }
    
    result = analyze_user_identity(different_user_data, baseline_data, "test_session_4")
    print(f"Test 4 - Very different user: {result['is_authorized']} (score: {result['identity_score']:.3f})")
    print(f"   Reason: {result['authorization_reason']}")

def test_edge_cases():
    """Test edge cases and error conditions"""
    
    print("\n🧪 Testing Edge Cases...")
    
    # Test empty data
    result = analyze_user_identity({}, {}, "test_session_5")
    print(f"Test 5 - Empty data: {result['is_authorized']} (score: {result.get('identity_score', 0):.3f})")
    print(f"   Reason: {result['authorization_reason']}")
    
    # Test missing baseline
    current_data = {
        'key_press_times': [100, 120, 110],
        'cursor_movements': [(10, 20)],
        'click_timestamps': [1000]
    }
    
    result = analyze_user_identity(current_data, None, "test_session_6")
    print(f"Test 6 - Missing baseline: {result['is_authorized']} (score: {result.get('identity_score', 0):.3f})")
    print(f"   Reason: {result['authorization_reason']}")

if __name__ == "__main__":
    print("🚀 Testing Improved User Identity Detection System")
    print("=" * 60)
    
    test_same_user_scenarios()
    test_different_user_scenarios() 
    test_edge_cases()
    
    print("\n✅ Testing completed!")
    print("💡 The system should now be more tolerant of natural behavioral variation")
    print("   while still detecting genuinely different users.")
