#!/usr/bin/env python3

"""
Debug script to see what's happening with identity detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_identity_detector import ImprovedUserIdentityDetector

def debug_signatures():
    """Debug the signature extraction and comparison"""
    
    detector = ImprovedUserIdentityDetector()
    
    # Same user data
    baseline_data = {
        'key_press_times': [100, 220, 330, 460, 565, 690],  # ~120ms intervals
        'cursor_movements': [(10, 20), (15, 25), (20, 30)],
        'click_timestamps': [1000, 2000, 3000]
    }
    
    current_data = {
        'key_press_times': [95, 215, 335, 455, 570, 685],  # Similar ~120ms intervals
        'cursor_movements': [(12, 22), (17, 27), (22, 32)],
        'click_timestamps': [1100, 2100, 3100]
    }
    
    # Very different user - More realistic differences
    different_data = {
        'key_press_times': [100, 600, 1100, 1650, 2120, 2680, 3250, 3800],  # Much slower, 8 keys vs 6
        'cursor_movements': [(100, 150), (200, 250), (300, 350), (400, 450), (500, 550)],  # 5 moves vs 3
        'click_timestamps': [200, 500, 800, 1200, 1600]  # 5 clicks vs 3, much faster clicking
    }
    
    print("🔍 Debugging Identity Detection Signatures")
    print("=" * 50)
    
    # Extract signatures
    baseline_sig = detector.extract_user_identity_signature(baseline_data)
    current_sig = detector.extract_user_identity_signature(current_data)
    different_sig = detector.extract_user_identity_signature(different_data)
    
    print("\n📊 Baseline User Signature:")
    print(f"   Typing: {baseline_sig['typing_signature']}")
    print(f"   Timing: {baseline_sig['timing_patterns']}")
    print(f"   Style:  {baseline_sig['interaction_style']}")
    
    print("\n📊 Current User Signature (same user):")
    print(f"   Typing: {current_sig['typing_signature']}")
    print(f"   Timing: {current_sig['timing_patterns']}")
    print(f"   Style:  {current_sig['interaction_style']}")
    
    print("\n📊 Different User Signature:")
    print(f"   Typing: {different_sig['typing_signature']}")
    print(f"   Timing: {different_sig['timing_patterns']}")
    print(f"   Style:  {different_sig['interaction_style']}")
    
    # Compare same user
    same_result = detector.compare_user_identities(current_sig, baseline_sig)
    print(f"\n✅ Same User Comparison: Score = {same_result['identity_score']:.3f}")
    print(f"   Decision: {same_result['is_same_user']} - {same_result['authorization_reason']}")
    print(f"   Breakdown: {same_result['similarity_breakdown']}")
    
    # Compare different user
    diff_result = detector.compare_user_identities(different_sig, baseline_sig)
    print(f"\n❌ Different User Comparison: Score = {diff_result['identity_score']:.3f}")
    print(f"   Decision: {diff_result['is_same_user']} - {diff_result['authorization_reason']}")
    print(f"   Breakdown: {diff_result['similarity_breakdown']}")

if __name__ == "__main__":
    debug_signatures()
