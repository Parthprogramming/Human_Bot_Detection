#!/usr/bin/env python3
"""
🔧 BALANCED THRESHOLD VALIDATION
Test both legitimate users and similar users with the new balanced threshold
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

def test_balanced_system():
    """
    Test the balanced system with:
    1. Legitimate user (should be AUTHORIZED)
    2. Similar friend (should be UNAUTHORIZED)  
    3. Very different user (should be UNAUTHORIZED)
    """
    print("🔧 BALANCED THRESHOLD VALIDATION")
    print("=" * 60)
    
    analyzer = BehavioralAnalyzer()
    
    # YOUR baseline pattern
    baseline = {
        'cursor_movements': [
            {'x': 300 + random.randint(-20, 20), 'y': 400 + random.randint(-20, 20)} 
            for _ in range(25)
        ],
        'key_press_times': [150 + random.randint(10, 20) + i*140 for i in range(18)],
        'click_timestamps': [800, 2200, 4100],
        'idle_time': 2500,
        'evasion_signals': {},
        'total_time': 7200,
    }
    
    # Test cases
    test_cases = [
        {
            'name': 'LEGITIMATE_USER',
            'description': 'You using your own account (should be AUTHORIZED)',
            'data': {
                'cursor_movements': [
                    {'x': 298 + random.randint(-15, 25), 'y': 402 + random.randint(-15, 25)} 
                    for _ in range(26)  # Very similar to baseline
                ],
                'key_press_times': [152 + random.randint(8, 22) + i*138 for i in range(17)],
                'click_timestamps': [810, 2190, 4110],
                'idle_time': 2520,
                'evasion_signals': {},
                'total_time': 7180,
            },
            'expected': 'AUTHORIZED'
        },
        {
            'name': 'SIMILAR_FRIEND', 
            'description': 'Friend with similar behavior (should be UNAUTHORIZED)',
            'data': {
                'cursor_movements': [
                    {'x': 320 + random.randint(-30, 40), 'y': 380 + random.randint(-30, 40)} 
                    for _ in range(35)  # Different pattern
                ],
                'key_press_times': [160 + random.randint(5, 25) + i*135 for i in range(16)],
                'click_timestamps': [750, 2100, 4200, 5800],
                'idle_time': 2800,
                'evasion_signals': {},
                'total_time': 7500,
            },
            'expected': 'UNAUTHORIZED'
        },
        {
            'name': 'VERY_DIFFERENT_USER',
            'description': 'Very different user (should be UNAUTHORIZED)',
            'data': {
                'cursor_movements': [
                    {'x': random.randint(100, 600), 'y': random.randint(100, 500)} 
                    for _ in range(50)  # Very different pattern
                ],
                'key_press_times': [100 + random.randint(20, 80) + i*200 for i in range(12)],
                'click_timestamps': [400, 1500, 3000, 4500, 6000],
                'idle_time': 4000,
                'evasion_signals': {},
                'total_time': 10000,
            },
            'expected': 'UNAUTHORIZED'
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n🔍 Testing {test_case['name']}:")
        print(f"   {test_case['description']}")
        
        result = analyzer.analyze_with_baseline_comparison(
            session_id=f"balanced_test_{test_case['name'].lower()}",
            current_data=test_case['data'],
            baseline_behavior_or_user_id=baseline
        )
        
        is_authorized = result.get('is_authorized', False)
        std_devs = result.get('standard_deviations', 0)
        threshold = result.get('behavioral_threshold', 3.0)
        confidence = result.get('confidence', 0)
        risk_score = result.get('risk_score', 0)
        
        print(f"  📊 Standard Deviations: {std_devs:.2f}σ")
        print(f"  🎯 Threshold: {threshold:.1f}σ")
        print(f"  📊 Confidence: {confidence:.3f}")
        print(f"  ⚠️  Risk Score: {risk_score:.3f}")
        print(f"  ✅ Authorized: {is_authorized}")
        print(f"  📋 Expected: {test_case['expected']}")
        
        # Check if result matches expectation
        expected_auth = test_case['expected'] == 'AUTHORIZED'
        if is_authorized == expected_auth:
            print(f"  ✅ CORRECT: {test_case['expected']} as expected")
        else:
            print(f"  ❌ WRONG: Expected {test_case['expected']}, got {'AUTHORIZED' if is_authorized else 'UNAUTHORIZED'}")
        
        results[test_case['name']] = {
            'authorized': is_authorized,
            'expected': expected_auth,
            'correct': is_authorized == expected_auth,
            'std_devs': std_devs,
            'threshold': threshold,
            'confidence': confidence,
            'risk_score': risk_score
        }
    
    return results

def analyze_balance(results):
    """Analyze if the threshold balance is correct"""
    print(f"\n📈 BALANCE ANALYSIS")
    print("=" * 60)
    
    correct_count = sum(1 for r in results.values() if r['correct'])
    total_count = len(results)
    
    print(f"Overall Accuracy: {correct_count}/{total_count} ({100*correct_count/total_count:.1f}%)")
    print()
    
    for name, result in results.items():
        status = "✅ CORRECT" if result['correct'] else "❌ INCORRECT"
        print(f"{name}: {status}")
        print(f"  Standard Deviations: {result['std_devs']:.2f}σ")
        print(f"  Threshold: {result['threshold']:.1f}σ")
        print(f"  Result: {'AUTHORIZED' if result['authorized'] else 'UNAUTHORIZED'}")
        print()
    
    # Specific analysis
    legitimate = results.get('LEGITIMATE_USER', {})
    similar_friend = results.get('SIMILAR_FRIEND', {})
    very_different = results.get('VERY_DIFFERENT_USER', {})
    
    print("🎯 THRESHOLD EFFECTIVENESS:")
    if legitimate.get('correct'):
        print(f"✅ Legitimate user: {legitimate.get('std_devs', 0):.2f}σ ≤ {legitimate.get('threshold', 0):.1f}σ → AUTHORIZED")
    else:
        print(f"❌ Legitimate user: {legitimate.get('std_devs', 0):.2f}σ vs {legitimate.get('threshold', 0):.1f}σ → PROBLEM")
    
    if similar_friend.get('correct'):
        print(f"✅ Similar friend: {similar_friend.get('std_devs', 0):.2f}σ > {similar_friend.get('threshold', 0):.1f}σ → BLOCKED")
    else:
        print(f"❌ Similar friend: {similar_friend.get('std_devs', 0):.2f}σ vs {similar_friend.get('threshold', 0):.1f}σ → PROBLEM")
    
    if very_different.get('correct'):
        print(f"✅ Very different: {very_different.get('std_devs', 0):.2f}σ > {very_different.get('threshold', 0):.1f}σ → BLOCKED")
    else:
        print(f"❌ Very different: {very_different.get('std_devs', 0):.2f}σ vs {very_different.get('threshold', 0):.1f}σ → PROBLEM")

def recommend_adjustments(results):
    """Recommend threshold adjustments if needed"""
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 60)
    
    legitimate = results.get('LEGITIMATE_USER', {})
    similar_friend = results.get('SIMILAR_FRIEND', {})
    
    all_correct = all(r['correct'] for r in results.values())
    
    if all_correct:
        print("✅ PERFECT BALANCE: Current threshold (3.0σ) is working optimally")
        print("🎯 No adjustments needed")
        print("🛡️ System provides good security while allowing legitimate access")
    else:
        print("🔧 ADJUSTMENTS NEEDED:")
        
        if not legitimate.get('correct') and not legitimate.get('authorized'):
            leg_std = legitimate.get('std_devs', 0)
            print(f"❌ Legitimate user blocked ({leg_std:.2f}σ)")
            print(f"🔧 Increase threshold to: {leg_std * 1.5:.1f}σ")
        
        if not similar_friend.get('correct') and similar_friend.get('authorized'):
            friend_std = similar_friend.get('std_devs', 0)
            print(f"❌ Similar friend allowed ({friend_std:.2f}σ)")
            print(f"🔧 Decrease threshold to: {friend_std * 0.8:.1f}σ")

def main():
    """Run balanced threshold validation"""
    print("🔧 BALANCED THRESHOLD VALIDATION")
    print("🕐 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Test the balanced system
    results = test_balanced_system()
    
    # Analyze the balance
    analyze_balance(results)
    
    # Recommend adjustments
    recommend_adjustments(results)
    
    # Save results
    with open('balanced_threshold_validation.json', 'w') as f:
        json.dump({
            'results': results,
            'analysis_timestamp': datetime.now().isoformat(),
            'threshold_setting': 3.0,
            'all_correct': all(r['correct'] for r in results.values())
        }, f, indent=2, default=str)
    
    print("💾 Validation saved to: balanced_threshold_validation.json")

if __name__ == "__main__":
    main()
