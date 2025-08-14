#!/usr/bin/env python3
"""
REAL-WORLD THRESHOLD TEST (7.0σ)
Testing with realistic human behavioral variations that occur in real-world usage
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

def test_real_world_system():
    """Test with realistic human behavioral variations"""
    print("🌍 REAL-WORLD THRESHOLD VALIDATION")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    analyzer = BehavioralAnalyzer()
    
    # Test cases with realistic human variation
    test_cases = [
        {
            'name': 'NORMAL_USER_SESSION_1',
            'description': 'You in a normal session (should be AUTHORIZED)',
            'current_data': {
                'cursor_movements': [{'x': i*12 + (i%3)*5, 'y': i*7 + (i%2)*3, 'timestamp': i*120 + (i%5)*20} for i in range(28)],
                'key_press_times': [{'keypress_interval': 160 + (i%4)*30, 'key': f'key_{i}'} for i in range(19)],
                'click_timestamps': [{'timestamp': i*1200 + (i%3)*200, 'x': i*60 + (i%2)*15, 'y': i*35 + (i%3)*10} for i in range(4)],
                'idle_time': 2800,
                'typing_speed': 58,
                'evasion_signals': {}
            },
            'baseline_data': {
                'cursor_movements': [{'x': i*10, 'y': i*5, 'timestamp': i*100} for i in range(25)],
                'key_press_times': [{'keypress_interval': 150, 'key': f'key_{i}'} for i in range(18)],
                'click_timestamps': [{'timestamp': i*1000, 'x': i*50, 'y': i*25} for i in range(3)],
                'idle_time': 2500,
                'typing_speed': 55,
                'evasion_signals': {}
            },
            'expected': 'AUTHORIZED'
        },
        {
            'name': 'TIRED_USER_SESSION',
            'description': 'You when tired - slower, less precise (should be AUTHORIZED)',
            'current_data': {
                'cursor_movements': [{'x': i*8 + (i%5)*12, 'y': i*4 + (i%4)*8, 'timestamp': i*180 + (i%6)*40} for i in range(35)],
                'key_press_times': [{'keypress_interval': 250 + (i%6)*60, 'key': f'key_{i}'} for i in range(15)],
                'click_timestamps': [{'timestamp': i*1800 + (i%4)*300, 'x': i*45 + (i%5)*20, 'y': i*28 + (i%4)*15} for i in range(5)],
                'idle_time': 4200,
                'typing_speed': 35,
                'evasion_signals': {}
            },
            'baseline_data': {
                'cursor_movements': [{'x': i*10, 'y': i*5, 'timestamp': i*100} for i in range(25)],
                'key_press_times': [{'keypress_interval': 150, 'key': f'key_{i}'} for i in range(18)],
                'click_timestamps': [{'timestamp': i*1000, 'x': i*50, 'y': i*25} for i in range(3)],
                'idle_time': 2500,
                'typing_speed': 55,
                'evasion_signals': {}
            },
            'expected': 'AUTHORIZED'
        },
        {
            'name': 'FOCUSED_USER_SESSION',
            'description': 'You when focused - faster, more precise (should be AUTHORIZED)',
            'current_data': {
                'cursor_movements': [{'x': i*15 + (i%2)*3, 'y': i*9 + (i%2)*2, 'timestamp': i*80 + (i%3)*10} for i in range(22)],
                'key_press_times': [{'keypress_interval': 100 + (i%3)*15, 'key': f'key_{i}'} for i in range(24)],
                'click_timestamps': [{'timestamp': i*800 + (i%2)*50, 'x': i*65 + (i%2)*5, 'y': i*40 + (i%2)*3} for i in range(2)],
                'idle_time': 1800,
                'typing_speed': 75,
                'evasion_signals': {}
            },
            'baseline_data': {
                'cursor_movements': [{'x': i*10, 'y': i*5, 'timestamp': i*100} for i in range(25)],
                'key_press_times': [{'keypress_interval': 150, 'key': f'key_{i}'} for i in range(18)],
                'click_timestamps': [{'timestamp': i*1000, 'x': i*50, 'y': i*25} for i in range(3)],
                'idle_time': 2500,
                'typing_speed': 55,
                'evasion_signals': {}
            },
            'expected': 'AUTHORIZED'
        },
        {
            'name': 'AUTOMATION_BOT',
            'description': 'Clear automation/bot behavior (should be UNAUTHORIZED)',
            'current_data': {
                'cursor_movements': [{'x': i*20, 'y': i*20, 'timestamp': i*50} for i in range(100)],  # Too perfect
                'key_press_times': [{'keypress_interval': 100, 'key': f'key_{i}'} for i in range(50)],  # Too consistent
                'click_timestamps': [{'timestamp': i*500, 'x': i*100, 'y': i*100} for i in range(10)],  # Too regular
                'idle_time': 0,  # No idle time
                'typing_speed': 120,  # Too fast
                'evasion_signals': {}
            },
            'baseline_data': {
                'cursor_movements': [{'x': i*10, 'y': i*5, 'timestamp': i*100} for i in range(25)],
                'key_press_times': [{'keypress_interval': 150, 'key': f'key_{i}'} for i in range(18)],
                'click_timestamps': [{'timestamp': i*1000, 'x': i*50, 'y': i*25} for i in range(3)],
                'idle_time': 2500,
                'typing_speed': 55,
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
                f"real_world_test_{test_case['name'].lower()}",
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
            
            print(f"  📊 Standard Deviations: {std_devs:.2f}σ")
            print(f"  🎯 Threshold: {threshold:.1f}σ")
            print(f"  📊 Confidence: {confidence:.3f}")
            print(f"  ⚠️  Risk Score: {risk_score:.3f}")
            print(f"  ✅ Authorized: {is_authorized}")
            print(f"  📋 Expected: {test_case['expected']}")
            
            # Validate result
            expected_auth = test_case['expected'] == 'AUTHORIZED'
            is_correct = is_authorized == expected_auth
            
            if is_correct:
                print(f"  ✅ CORRECT: {test_case['expected']} as expected")
            else:
                print(f"  ❌ INCORRECT: Expected {test_case['expected']}, got {'AUTHORIZED' if is_authorized else 'UNAUTHORIZED'}")
                print(f"  📝 Reason: {auth_reason}")
            
            results[test_case['name']] = {
                'expected': expected_auth,
                'actual': is_authorized,
                'correct': is_correct,
                'std_devs': std_devs,
                'threshold': threshold,
                'confidence': confidence,
                'risk_score': risk_score,
                'auth_reason': auth_reason
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
    print("📈 REAL-WORLD ANALYSIS")
    print("=" * 60)
    
    correct_count = sum(1 for r in results.values() if r.get('correct', False))
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"Overall Accuracy: {correct_count}/{total_count} ({accuracy:.1f}%)")
    print()
    
    # Detailed results
    for name, result in results.items():
        status = "✅ CORRECT" if result.get('correct', False) else "❌ INCORRECT"
        print(f"{name}: {status}")
        if 'std_devs' in result:
            print(f"  Standard Deviations: {result['std_devs']:.2f}σ")
            print(f"  Threshold: {result['threshold']:.1f}σ")
            print(f"  Result: {'AUTHORIZED' if result['actual'] else 'UNAUTHORIZED'}")
            if not result.get('correct', False):
                print(f"  Issue: {result.get('auth_reason', 'Unknown')}")
        print()
    
    print("🎯 REAL-WORLD THRESHOLD EFFECTIVENESS:")
    user_sessions = [name for name in results.keys() if 'USER' in name and 'AUTOMATION' not in name]
    for session in user_sessions:
        result = results[session]
        if 'std_devs' in result:
            if result['std_devs'] <= result['threshold']:
                print(f"✅ {session}: {result['std_devs']:.2f}σ ≤ {result['threshold']:.1f}σ → AUTHORIZED")
            else:
                status = "AUTHORIZED (override)" if result['actual'] else "BLOCKED"
                print(f"⚠️ {session}: {result['std_devs']:.2f}σ > {result['threshold']:.1f}σ → {status}")
    
    # Check automation detection
    if 'AUTOMATION_BOT' in results:
        bot_result = results['AUTOMATION_BOT']
        if 'std_devs' in bot_result:
            if not bot_result['actual']:
                print(f"✅ AUTOMATION_BOT: {bot_result['std_devs']:.2f}σ > {bot_result['threshold']:.1f}σ → BLOCKED")
            else:
                print(f"❌ AUTOMATION_BOT: {bot_result['std_devs']:.2f}σ → NOT BLOCKED (Issue!)")
    
    print()
    print("💡 REAL-WORLD RECOMMENDATIONS")
    print("=" * 60)
    
    if accuracy >= 75:
        print("✅ GOOD REAL-WORLD PERFORMANCE: System handles natural human variation well")
        if accuracy == 100:
            print("🎯 PERFECT: All test cases passed")
    else:
        print("⚠️ NEEDS ADJUSTMENT: Some real-world scenarios failing")
        
    if any(not r.get('correct', False) and r.get('expected', False) for r in results.values()):
        print("🔧 Consider increasing threshold further for better real-world acceptance")
    
    if any(not r.get('correct', False) and not r.get('expected', False) for r in results.values()):
        print("🛡️ Check automation detection - may be too lenient")

if __name__ == "__main__":
    test_real_world_system()
