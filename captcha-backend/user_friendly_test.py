#!/usr/bin/env python3
"""
USER-FRIENDLY THRESHOLD TEST (4.0σ)
Testing that legitimate users are authorized without needing confidence override
"""

import os
import sys
import django
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'captcha.settings')
django.setup()

from user.views import BehavioralAnalyzer

def test_user_friendly_system():
    """Test that the 4.0σ threshold properly authorizes legitimate users"""
    print("🔧 USER-FRIENDLY THRESHOLD VALIDATION")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    analyzer = BehavioralAnalyzer()
    
    # Test cases
    test_cases = [
        {
            'name': 'LEGITIMATE_USER',
            'description': 'You using your own account (should be AUTHORIZED)',
            'current_data': {
                'cursor_movements': [{'x': i*10, 'y': i*5, 'timestamp': i*100} for i in range(26)],
                'key_press_times': [{'keypress_interval': 150 + i*10, 'key': f'key_{i}'} for i in range(17)],
                'click_timestamps': [{'timestamp': i*1000, 'x': i*50, 'y': i*25} for i in range(3)],
                'idle_time': 2500,
                'typing_speed': 55,
                'evasion_signals': {}
            },
            'baseline_data': {
                'cursor_movements': [{'x': i*12, 'y': i*6, 'timestamp': i*110} for i in range(25)],
                'key_press_times': [{'keypress_interval': 160 + i*15, 'key': f'key_{i}'} for i in range(18)],
                'click_timestamps': [{'timestamp': i*1100, 'x': i*55, 'y': i*30} for i in range(3)],
                'idle_time': 2600,
                'typing_speed': 52,
                'evasion_signals': {}
            },
            'expected': 'AUTHORIZED'
        },
        {
            'name': 'SIMILAR_FRIEND',
            'description': 'Friend with similar behavior (should be UNAUTHORIZED)',
            'current_data': {
                'cursor_movements': [{'x': i*15, 'y': i*8, 'timestamp': i*120} for i in range(35)],
                'key_press_times': [{'keypress_interval': 180 + i*20, 'key': f'key_{i}'} for i in range(16)],
                'click_timestamps': [{'timestamp': i*1200, 'x': i*60, 'y': i*35} for i in range(4)],
                'idle_time': 3000,
                'typing_speed': 45,
                'evasion_signals': {}
            },
            'baseline_data': {
                'cursor_movements': [{'x': i*12, 'y': i*6, 'timestamp': i*110} for i in range(25)],
                'key_press_times': [{'keypress_interval': 160 + i*15, 'key': f'key_{i}'} for i in range(18)],
                'click_timestamps': [{'timestamp': i*1100, 'x': i*55, 'y': i*30} for i in range(3)],
                'idle_time': 2600,
                'typing_speed': 52,
                'evasion_signals': {}
            },
            'expected': 'UNAUTHORIZED'
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"🔍 Testing {test_case['name']}:")
        print(f"   {test_case['description']}")
        
        try:
            # Run analysis
            result = analyzer.analyze_with_baseline_comparison(
                f"user_friendly_test_{test_case['name'].lower()}",
                test_case['current_data'],
                test_case['baseline_data']
            )
            
            # Extract results
            std_devs = result.get('standard_deviations', 0)
            threshold = result.get('behavioral_threshold', 0)
            confidence = result.get('confidence', 0)
            risk_score = result.get('risk_score', 0)
            is_authorized = result.get('is_authorized', False)
            auth_reason = result.get('authorization_reason', '')
            
            # Check if legitimate user needed confidence override
            needed_override = False
            if test_case['name'] == 'LEGITIMATE_USER':
                if std_devs > threshold and is_authorized and 'CONFIDENCE_EXCEEDS_RISK' in auth_reason:
                    needed_override = True
            
            print(f"  📊 Standard Deviations: {std_devs:.2f}σ")
            print(f"  🎯 Threshold: {threshold:.1f}σ")
            print(f"  📊 Confidence: {confidence:.3f}")
            print(f"  ⚠️  Risk Score: {risk_score:.3f}")
            print(f"  ✅ Authorized: {is_authorized}")
            if needed_override:
                print(f"  ⚠️ NEEDED OVERRIDE: Legitimate user required confidence > risk override!")
            print(f"  📋 Expected: {test_case['expected']}")
            
            # Validate result
            expected_auth = test_case['expected'] == 'AUTHORIZED'
            is_correct = is_authorized == expected_auth
            
            if is_correct:
                print(f"  ✅ CORRECT: {test_case['expected']} as expected")
            else:
                print(f"  ❌ INCORRECT: Expected {test_case['expected']}, got {'AUTHORIZED' if is_authorized else 'UNAUTHORIZED'}")
            
            results[test_case['name']] = {
                'expected': expected_auth,
                'actual': is_authorized,
                'correct': is_correct,
                'std_devs': std_devs,
                'threshold': threshold,
                'confidence': confidence,
                'risk_score': risk_score,
                'needed_override': needed_override
            }
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            results[test_case['name']] = {
                'expected': test_case['expected'] == 'AUTHORIZED',
                'actual': False,
                'correct': False,
                'error': str(e)
            }
        
        print()
    
    # Summary
    print("📈 USER-FRIENDLY ANALYSIS")
    print("=" * 60)
    
    correct_count = sum(1 for r in results.values() if r.get('correct', False))
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"Overall Accuracy: {correct_count}/{total_count} ({accuracy:.1f}%)")
    print()
    
    # Check if legitimate user needed override
    legitimate_needed_override = results.get('LEGITIMATE_USER', {}).get('needed_override', False)
    
    for name, result in results.items():
        status = "✅ CORRECT" if result.get('correct', False) else "❌ INCORRECT"
        print(f"{name}: {status}")
        if 'std_devs' in result:
            print(f"  Standard Deviations: {result['std_devs']:.2f}σ")
            print(f"  Threshold: {result['threshold']:.1f}σ")
            print(f"  Result: {'AUTHORIZED' if result['actual'] else 'UNAUTHORIZED'}")
            if result.get('needed_override'):
                print(f"  ⚠️ NEEDED OVERRIDE")
        print()
    
    print("🎯 THRESHOLD EFFECTIVENESS:")
    if 'LEGITIMATE_USER' in results and 'SIMILAR_FRIEND' in results:
        legit = results['LEGITIMATE_USER']
        friend = results['SIMILAR_FRIEND']
        
        if legit.get('std_devs', 0) <= legit.get('threshold', 0):
            print(f"✅ Legitimate user: {legit['std_devs']:.2f}σ ≤ {legit['threshold']:.1f}σ → AUTHORIZED")
        else:
            print(f"⚠️ Legitimate user: {legit['std_devs']:.2f}σ > {legit['threshold']:.1f}σ → NEEDED OVERRIDE")
            
        if friend.get('std_devs', 0) > friend.get('threshold', 0):
            print(f"✅ Similar friend: {friend['std_devs']:.2f}σ > {friend['threshold']:.1f}σ → BLOCKED")
        else:
            print(f"❌ Similar friend: {friend['std_devs']:.2f}σ ≤ {friend['threshold']:.1f}σ → NOT BLOCKED")
    
    print()
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if legitimate_needed_override:
        print("⚠️ THRESHOLD TOO STRICT: Legitimate users require confidence override")
        print("🔧 Consider increasing threshold to 4.5σ or 5.0σ")
    elif accuracy == 100:
        print("✅ OPTIMAL BALANCE: Current threshold working well")
        print("🎯 No adjustments needed")
        print("🛡️ System provides good security while allowing legitimate access")
    else:
        print("⚠️ MIXED RESULTS: Some issues detected")
        print("🔧 Review threshold and detection logic")

if __name__ == "__main__":
    test_user_friendly_system()
