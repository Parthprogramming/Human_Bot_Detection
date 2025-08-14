#!/usr/bin/env python3
"""
CONTEXTUAL AUTHORIZATION TEST
Testing a sophisticated multi-factor approach that considers:
1. Standard deviations with large tolerance for real users
2. Behavioral consistency for different user detection
3. Risk patterns for automation detection
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

def test_contextual_authorization():
    """Test contextual authorization approach"""
    print("🎯 CONTEXTUAL AUTHORIZATION VALIDATION")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    analyzer = BehavioralAnalyzer()
    
    # Test cases with different scenarios
    test_cases = [
        {
            'name': 'LEGITIMATE_USER_HIGH_VARIATION',
            'description': 'You with high behavioral variation (should be AUTHORIZED)',
            'expected_std_dev': '6-8σ',
            'expected': 'AUTHORIZED'
        },
        {
            'name': 'SIMILAR_FRIEND',
            'description': 'Friend with similar behavior (should be UNAUTHORIZED)',
            'expected_std_dev': '7-8σ',
            'expected': 'UNAUTHORIZED'
        },
        {
            'name': 'VERY_DIFFERENT_USER',
            'description': 'Very different user (should be UNAUTHORIZED)',
            'expected_std_dev': '7-8σ',
            'expected': 'UNAUTHORIZED'
        }
    ]
    
    # Use the existing test data from balanced_threshold_test.py
    current_data_legitimate = {
        'cursorMovements': [
            {'x': 100 + i*10, 'y': 50 + i*5, 'timestamp': 1000 + i*100}
            for i in range(26)
        ],
        'keyPressTimes': [
            {'keypress_interval': 150 + i*10, 'key': f'key_{i}'}
            for i in range(17)
        ],
        'clickTimestamps': [
            {'timestamp': 1000 + i*1000, 'x': 200 + i*50, 'y': 100 + i*25}
            for i in range(3)
        ],
        'idle_time': 2500,
        'typing_speed': 55,
        'evasion_signals': {}
    }
    
    current_data_friend = {
        'cursorMovements': [
            {'x': 120 + i*15, 'y': 60 + i*8, 'timestamp': 1200 + i*120}
            for i in range(35)
        ],
        'keyPressTimes': [
            {'keypress_interval': 180 + i*20, 'key': f'key_{i}'}
            for i in range(16)
        ],
        'clickTimestamps': [
            {'timestamp': 1200 + i*1200, 'x': 240 + i*60, 'y': 120 + i*35}
            for i in range(4)
        ],
        'idle_time': 3000,
        'typing_speed': 45,
        'evasion_signals': {}
    }
    
    current_data_different = {
        'cursorMovements': [
            {'x': 200 + i*20, 'y': 100 + i*15, 'timestamp': 800 + i*80}
            for i in range(50)
        ],
        'keyPressTimes': [
            {'keypress_interval': 80 + i*5, 'key': f'key_{i}'}
            for i in range(12)
        ],
        'clickTimestamps': [
            {'timestamp': 800 + i*800, 'x': 400 + i*100, 'y': 200 + i*50}
            for i in range(5)
        ],
        'idle_time': 500,
        'typing_speed': 85,
        'evasion_signals': {}
    }
    
    baseline_data = {
        'cursorMovements': [
            {'x': 110 + i*12, 'y': 55 + i*6, 'timestamp': 1100 + i*110}
            for i in range(25)
        ],
        'keyPressTimes': [
            {'keypress_interval': 160 + i*15, 'key': f'key_{i}'}
            for i in range(18)
        ],
        'clickTimestamps': [
            {'timestamp': 1100 + i*1100, 'x': 220 + i*55, 'y': 110 + i*30}
            for i in range(3)
        ],
        'idle_time': 2600,
        'typing_speed': 52,
        'evasion_signals': {}
    }
    
    test_data = [
        current_data_legitimate,
        current_data_friend,
        current_data_different
    ]
    
    results = {}
    
    for i, test_case in enumerate(test_cases):
        print(f"🔍 Testing {test_case['name']}:")
        print(f"   {test_case['description']}")
        print(f"   Expected std dev: {test_case['expected_std_dev']}")
        
        try:
            # Run analysis
            result = analyzer.analyze_with_baseline_comparison(
                f"contextual_test_{test_case['name'].lower()}",
                test_data[i],
                baseline_data
            )
            
            # Extract results
            std_devs = result.get('standard_deviations', 0)
            threshold = result.get('behavioral_threshold', 0)
            confidence = result.get('confidence', 0)
            risk_score = result.get('risk_score', 0)
            is_authorized = result.get('is_authorized', False)
            auth_reason = result.get('authorization_reason', '')
            consistency_score = result.get('consistency_score', 0)
            
            print(f"  📊 Standard Deviations: {std_devs:.2f}σ")
            print(f"  🎯 Threshold: {threshold:.1f}σ")
            print(f"  🔄 Consistency: {consistency_score:.3f}")
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
                'consistency': consistency_score,
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
    
    # Analysis
    print("📈 CONTEXTUAL ANALYSIS")
    print("=" * 60)
    
    correct_count = sum(1 for r in results.values() if r.get('correct', False))
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"Overall Accuracy: {correct_count}/{total_count} ({accuracy:.1f}%)")
    print()
    
    # Check if we can differentiate based on consistency
    print("🔍 CONSISTENCY ANALYSIS:")
    for name, result in results.items():
        if 'consistency' in result:
            status = "✅" if result.get('correct', False) else "❌"
            consistency = result['consistency']
            std_devs = result['std_devs']
            print(f"{status} {name}: {std_devs:.2f}σ, consistency: {consistency:.3f}")
    
    print()
    print("💡 CONTEXTUAL RECOMMENDATIONS")
    print("=" * 60)
    
    # Analyze patterns
    if 'LEGITIMATE_USER_HIGH_VARIATION' in results and 'SIMILAR_FRIEND' in results:
        legit = results['LEGITIMATE_USER_HIGH_VARIATION']
        friend = results['SIMILAR_FRIEND']
        
        if 'consistency' in legit and 'consistency' in friend:
            legit_consistency = legit['consistency']
            friend_consistency = friend['consistency']
            
            print(f"📊 Legitimate user consistency: {legit_consistency:.3f}")
            print(f"📊 Similar friend consistency: {friend_consistency:.3f}")
            
            if legit_consistency > friend_consistency + 0.2:
                print("✅ Consistency can differentiate: Use consistency-based detection")
                print(f"🎯 Suggested consistency threshold: {(legit_consistency + friend_consistency) / 2:.3f}")
            else:
                print("⚠️ Consistency alone insufficient for differentiation")
                print("🔧 Need multi-factor approach combining std dev + consistency + risk")
    
    if accuracy >= 67:
        print("✅ Contextual approach shows promise")
    else:
        print("⚠️ Need further refinement of contextual factors")

if __name__ == "__main__":
    test_contextual_authorization()
