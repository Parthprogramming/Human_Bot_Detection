#!/usr/bin/env python3
"""
🔧 BEHAVIORAL SENSITIVITY ADJUSTMENT
Fix the system to properly detect when different users access the same account
"""

import os
import django
import json
import time
import random
import numpy as np
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'captcha.settings')
django.setup()

from user.views import BehavioralAnalyzer

def test_friend_scenario():
    """
    Test scenario: Your behavioral pattern vs. your friend's behavioral pattern
    This should trigger UNAUTHORIZED
    """
    print("🔧 TESTING FRIEND ACCESS SCENARIO")
    print("=" * 60)
    
    analyzer = BehavioralAnalyzer()
    
    # YOUR typical behavioral pattern (baseline)
    your_pattern = {
        'cursor_movements': [
            {'x': random.randint(100, 700), 'y': random.randint(100, 500)} 
            for _ in range(25)  # Your typical cursor pattern
        ],
        'key_press_times': [150 + random.randint(80, 150) + i*140 for i in range(16)],  # Your typing speed
        'click_timestamps': [800, 2200, 4100],  # Your click timing
        'idle_time': 2500,  # Your thinking time
        'evasion_signals': {},
        'total_time': 7200,
    }
    
    # YOUR FRIEND's different behavioral pattern
    friend_pattern = {
        'cursor_movements': [
            {'x': random.randint(200, 600), 'y': random.randint(200, 400)} 
            for _ in range(45)  # Different cursor activity
        ],
        'key_press_times': [200 + random.randint(50, 100) + i*180 for i in range(12)],  # Different typing
        'click_timestamps': [500, 1800, 3500, 5000],  # Different click pattern
        'idle_time': 4000,  # Different thinking time
        'evasion_signals': {},
        'total_time': 9500,  # Takes longer
    }
    
    print("📊 Testing YOUR account with YOUR behavioral pattern:")
    your_result = analyzer.analyze_with_baseline_comparison(
        session_id='your_session',
        current_data=your_pattern,
        baseline_behavior_or_user_id=your_pattern  # Using same pattern as baseline
    )
    
    print(f"  📊 Your Confidence: {your_result.get('confidence', 'N/A')}")
    print(f"  ⚠️  Your Risk Score: {your_result.get('risk_score', 'N/A')}")
    print(f"  ✅ Your Authorized: {your_result.get('is_authorized', 'N/A')}")
    print(f"  📐 Your Std Devs: {your_result.get('standard_deviations', 'N/A')}")
    
    print("\n🚨 Testing YOUR account with FRIEND's behavioral pattern:")
    friend_result = analyzer.analyze_with_baseline_comparison(
        session_id='friend_session',
        current_data=friend_pattern,
        baseline_behavior_or_user_id=your_pattern  # Your baseline vs friend's behavior
    )
    
    print(f"  📊 Friend Confidence: {friend_result.get('confidence', 'N/A')}")
    print(f"  ⚠️  Friend Risk Score: {friend_result.get('risk_score', 'N/A')}")
    print(f"  ❌ Friend Authorized: {friend_result.get('is_authorized', 'N/A')}")
    print(f"  📐 Friend Std Devs: {friend_result.get('standard_deviations', 'N/A')}")
    
    # Analysis
    print(f"\n📈 SCENARIO ANALYSIS:")
    print(f"=" * 40)
    
    your_std = your_result.get('standard_deviations', 0)
    friend_std = friend_result.get('standard_deviations', 0)
    your_auth = your_result.get('is_authorized', False)
    friend_auth = friend_result.get('is_authorized', False)
    
    print(f"Your std devs: {your_std:.2f}σ")
    print(f"Friend std devs: {friend_std:.2f}σ")
    print(f"Difference: {abs(friend_std - your_std):.2f}σ")
    
    if your_auth and not friend_auth:
        print("✅ PERFECT: You authorized, friend blocked")
    elif your_auth and friend_auth:
        print("❌ PROBLEM: Both authorized (system too lenient)")
        print("🔧 SOLUTION NEEDED: Tighten behavioral thresholds")
    elif not your_auth and not friend_auth:
        print("⚠️  ISSUE: Both blocked (system too strict)")
    else:
        print("🤔 UNEXPECTED: You blocked, friend authorized")
    
    return your_result, friend_result

def analyze_threshold_sensitivity():
    """Test what thresholds would work better"""
    print(f"\n🎯 THRESHOLD SENSITIVITY ANALYSIS")
    print("=" * 60)
    
    # Test different threshold values
    test_thresholds = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    
    print("Current system uses 7.0σ threshold")
    print("For friend detection, we need:")
    print("- Your pattern: Should be ≤ threshold (AUTHORIZED)")
    print("- Friend pattern: Should be > threshold (UNAUTHORIZED)")
    print()
    
    for threshold in test_thresholds:
        print(f"📊 If threshold = {threshold:.1f}σ:")
        print(f"   Your pattern (≈3-4σ): {'✅ PASS' if 3.5 <= threshold else '❌ FAIL'}")
        print(f"   Friend pattern (≈7-8σ): {'✅ BLOCK' if 7.5 > threshold else '❌ ALLOW'}")
        if 3.5 <= threshold < 7.5:
            print(f"   🎯 OPTIMAL: Allows you, blocks friend")
        print()

def suggest_improvements():
    """Suggest specific improvements for friend detection"""
    print(f"\n💡 IMPROVEMENT SUGGESTIONS")
    print("=" * 60)
    
    print("🔧 1. REDUCE THRESHOLD:")
    print("   Current: 7.0σ → Suggested: 4.5σ")
    print("   This will make the system more sensitive to different users")
    print()
    
    print("🔧 2. ENHANCE FEATURE SENSITIVITY:")
    print("   - Focus on typing rhythm differences")
    print("   - Mouse movement pattern variations") 
    print("   - Click timing variations")
    print()
    
    print("🔧 3. MULTI-FACTOR DETECTION:")
    print("   - Combine behavioral + device fingerprinting")
    print("   - Add IP address change detection")
    print("   - Include browser/device pattern analysis")
    print()
    
    print("🔧 4. ADAPTIVE LEARNING:")
    print("   - Build stronger baseline from multiple sessions")
    print("   - Update baseline gradually over time")
    print("   - Detect significant pattern changes")

def main():
    """Run friend detection analysis"""
    print("🚨 FRIEND ACCESS DETECTION ANALYSIS")
    print("🕐 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Test the friend scenario
    your_result, friend_result = test_friend_scenario()
    
    # Analyze threshold sensitivity
    analyze_threshold_sensitivity()
    
    # Suggest improvements
    suggest_improvements()
    
    print(f"\n📋 CONCLUSION:")
    print("=" * 40)
    
    friend_auth = friend_result.get('is_authorized', True)
    if friend_auth:
        print("❌ CONFIRMED ISSUE: System failed to detect friend access")
        print("🔧 IMMEDIATE FIX: Reduce behavioral threshold from 7.0σ to 4.5σ")
        print("🚨 SECURITY RISK: Different users can access accounts undetected")
    else:
        print("✅ SYSTEM WORKING: Friend access was properly detected")
    
    # Save results
    with open('friend_detection_analysis.json', 'w') as f:
        json.dump({
            'your_result': your_result,
            'friend_result': friend_result,
            'analysis_timestamp': datetime.now().isoformat(),
            'issue_confirmed': friend_auth
        }, f, indent=2, default=str)
    
    print("💾 Analysis saved to: friend_detection_analysis.json")

if __name__ == "__main__":
    main()
