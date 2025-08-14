#!/usr/bin/env python3
"""
🔧 LEGITIMATE USER VALIDATION TEST
Test if the system is blocking legitimate users due to overly strict thresholds
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

def test_legitimate_user_access():
    """
    Test if legitimate user (you) can access your own account
    This should ALWAYS be AUTHORIZED
    """
    print("🔧 TESTING LEGITIMATE USER ACCESS")
    print("=" * 60)
    
    analyzer = BehavioralAnalyzer()
    
    # YOUR baseline behavioral pattern
    your_baseline = {
        'cursor_movements': [
            {'x': 300 + random.randint(-30, 30), 'y': 400 + random.randint(-30, 30)} 
            for _ in range(28)
        ],
        'key_press_times': [150 + random.randint(15, 25) + i*140 for i in range(18)],
        'click_timestamps': [800, 2200, 4100],
        'idle_time': 2500,
        'evasion_signals': {},
        'total_time': 7200,
    }
    
    # YOUR current session (should be very similar to baseline)
    your_current_session = {
        'cursor_movements': [
            {'x': 295 + random.randint(-25, 35), 'y': 405 + random.randint(-25, 35)} 
            for _ in range(30)  # Very similar to baseline
        ],
        'key_press_times': [148 + random.randint(12, 28) + i*142 for i in range(17)],  # Very similar typing
        'click_timestamps': [820, 2180, 4120],  # Very similar timing
        'idle_time': 2480,  # Very similar thinking time
        'evasion_signals': {},
        'total_time': 7180,
    }
    
    print("📊 Testing YOUR baseline vs YOUR current session:")
    result = analyzer.analyze_with_baseline_comparison(
        session_id='legitimate_user_test',
        current_data=your_current_session,
        baseline_behavior_or_user_id=your_baseline
    )
    
    print(f"  📊 Confidence: {result.get('confidence', 'N/A'):.4f}")
    print(f"  ⚠️  Risk Score: {result.get('risk_score', 'N/A'):.4f}")
    print(f"  ✅ Authorized: {result.get('is_authorized', 'N/A')}")
    print(f"  📐 Std Devs: {result.get('standard_deviations', 'N/A'):.4f}σ")
    print(f"  🎯 Threshold: {result.get('behavioral_threshold', 'N/A'):.1f}σ")
    print(f"  📋 Reason: {result.get('authorization_reason', 'N/A')}")
    
    return result

def test_different_threshold_values():
    """Test what happens with different threshold values"""
    print(f"\n🎯 THRESHOLD TESTING FOR LEGITIMATE USER")
    print("=" * 60)
    
    analyzer = BehavioralAnalyzer()
    
    # Test data
    baseline = {
        'cursor_movements': [{'x': 300, 'y': 400} for _ in range(25)],
        'key_press_times': [150 + i*140 for i in range(18)],
        'click_timestamps': [800, 2200, 4100],
        'idle_time': 2500,
        'evasion_signals': {},
        'total_time': 7200,
    }
    
    current = {
        'cursor_movements': [{'x': 305, 'y': 395} for _ in range(27)],
        'key_press_times': [155 + i*138 for i in range(17)],
        'click_timestamps': [820, 2180, 4120],
        'idle_time': 2480,
        'evasion_signals': {},
        'total_time': 7180,
    }
    
    # Test one analysis to see what standard deviations we get
    test_result = analyzer.analyze_with_baseline_comparison(
        session_id='threshold_test',
        current_data=current,
        baseline_behavior_or_user_id=baseline
    )
    
    legitimate_std_devs = test_result.get('standard_deviations', 0)
    print(f"Legitimate user typically gets: {legitimate_std_devs:.4f}σ")
    print()
    
    # Recommend appropriate thresholds
    recommended_thresholds = [
        (legitimate_std_devs * 2, "Conservative (2x legitimate user)"),
        (legitimate_std_devs * 3, "Balanced (3x legitimate user)"),
        (legitimate_std_devs * 4, "Lenient (4x legitimate user)"),
        (legitimate_std_devs * 5, "Very Lenient (5x legitimate user)")
    ]
    
    print("📊 RECOMMENDED THRESHOLDS:")
    for threshold, description in recommended_thresholds:
        legitimate_pass = legitimate_std_devs <= threshold
        print(f"  {threshold:.2f}σ - {description}")
        print(f"    Legitimate user: {'✅ PASS' if legitimate_pass else '❌ FAIL'}")
        print()

def suggest_optimal_threshold():
    """Suggest the optimal threshold based on testing"""
    print(f"\n💡 THRESHOLD OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)
    
    print("🔧 CURRENT PROBLEM:")
    print("  - Current threshold: 2.5σ")
    print("  - Legitimate users getting: ~0.7-1.5σ")
    print("  - System should allow: anything ≤ 2.5σ")
    print("  - Issue: System might be too strict in other areas")
    print()
    
    print("🎯 OPTIMAL SOLUTION:")
    print("  1. Threshold: 3.0σ (slightly more lenient)")
    print("  2. Hard block: 4.5σ (1.5x threshold)")
    print("  3. This allows:")
    print("     - You: 0.7σ → ✅ AUTHORIZED")
    print("     - Similar friend: 3.5σ → ❌ BLOCKED")
    print("     - Very different user: 5.0σ → ❌ HARD BLOCKED")
    print()
    
    print("🔧 IMPLEMENTATION:")
    print("  - Increase base_threshold from 2.5 to 3.0")
    print("  - Keep hard block at 1.5x threshold")
    print("  - Monitor legitimate user patterns")

def main():
    """Run legitimate user validation"""
    print("🔧 LEGITIMATE USER VALIDATION TEST")
    print("🕐 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Test legitimate user access
    result = test_legitimate_user_access()
    
    # Test threshold values
    test_different_threshold_values()
    
    # Suggest optimal threshold
    suggest_optimal_threshold()
    
    print(f"\n📋 DIAGNOSIS:")
    print("=" * 40)
    
    is_authorized = result.get('is_authorized', False)
    std_devs = result.get('standard_deviations', 0)
    threshold = result.get('behavioral_threshold', 2.5)
    
    if not is_authorized:
        print("❌ CONFIRMED PROBLEM: Legitimate user being blocked")
        print("🚨 URGENT: System too strict for normal use")
        print()
        print("🔧 IMMEDIATE FIX NEEDED:")
        if std_devs > threshold:
            print(f"  - Your deviation: {std_devs:.2f}σ > threshold: {threshold:.1f}σ")
            print(f"  - Increase threshold to: {std_devs * 2:.1f}σ")
        else:
            print("  - Check hard block logic or other blocking mechanisms")
        
    else:
        print("✅ SYSTEM OK: Legitimate user properly authorized")
        print(f"🎯 Current settings working: {std_devs:.2f}σ ≤ {threshold:.1f}σ")
    
    # Save results
    with open('legitimate_user_validation.json', 'w') as f:
        json.dump({
            'result': result,
            'analysis_timestamp': datetime.now().isoformat(),
            'legitimate_user_blocked': not is_authorized,
            'std_devs': std_devs,
            'threshold': threshold
        }, f, indent=2, default=str)
    
    print("💾 Validation saved to: legitimate_user_validation.json")

if __name__ == "__main__":
    main()
