#!/usr/bin/env python3
"""
🧪 SIMPLE BEHAVIORAL ANALYSIS TEST - WITHOUT REQUESTS
Test if the behavioral analysis can distinguish between different user types
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

def generate_behavioral_pattern(user_type):
    """Generate distinct behavioral patterns for different user types"""
    
    if user_type == "fast_typer":
        return {
            'cursor_movements': [{'x': x*10, 'y': y*5} for x, y in zip(range(50), range(50))],
            'key_press_times': [100 + i*80 for i in range(20)],  # Fast typing
            'click_timestamps': [500, 1500, 3000],
            'idle_time': 1000,
            'evasion_signals': {},
            'total_time': 5000,
        }
        
    elif user_type == "slow_typer":
        return {
            'cursor_movements': [{'x': x*3, 'y': y*2} for x, y in zip(range(20), range(20))],
            'key_press_times': [200 + i*300 for i in range(15)],  # Slow typing
            'click_timestamps': [800, 2000, 4000],
            'idle_time': 5000,
            'evasion_signals': {},
            'total_time': 10000,
        }
        
    elif user_type == "bot_like":
        return {
            'cursor_movements': [{'x': x*20, 'y': 0} for x in range(10)],
            'key_press_times': [50 + i*50 for i in range(30)],  # Very regular
            'click_timestamps': [100, 200, 300, 400],
            'idle_time': 0,
            'evasion_signals': {
                'is_automated_browser': True,
                'paste_detected': True,
                'unusual_timing': True
            },
            'total_time': 2000,
        }
        
    else:  # normal_user
        return {
            'cursor_movements': [{'x': random.randint(0, 800), 'y': random.randint(0, 600)} for _ in range(30)],
            'key_press_times': [150 + random.randint(50, 200) + i*150 for i in range(18)],
            'click_timestamps': [600, 1800, 3200],
            'idle_time': 3000,
            'evasion_signals': {},
            'total_time': 8000,
        }

def test_behavioral_analysis():
    """Test the behavioral analyzer with different user patterns"""
    print("🧪 TESTING BEHAVIORAL ANALYSIS SYSTEM")
    print("=" * 60)
    
    analyzer = BehavioralAnalyzer()
    user_types = ["fast_typer", "slow_typer", "bot_like", "normal_user"]
    results = {}
    
    # Generate a baseline user
    baseline = generate_behavioral_pattern("normal_user")
    print("📊 Using normal_user as baseline")
    
    for user_type in user_types:
        print(f"\n🔍 Testing {user_type.upper()}:")
        
        # Generate user behavior
        current_data = generate_behavioral_pattern(user_type)
        
        try:
            # Analyze behavior
            result = analyzer.analyze_with_baseline_comparison(
                session_id=f'test_{user_type}_{int(time.time())}',
                current_data=current_data,
                baseline_behavior_or_user_id=baseline
            )
            
            confidence = result.get('confidence', 'N/A')
            risk_score = result.get('risk_score', 'N/A')
            is_authorized = result.get('is_authorized', 'N/A')
            mahalanobis = result.get('mahalanobis_distance', 'N/A')
            std_devs = result.get('standard_deviations', 'N/A')
            
            print(f"  📊 Confidence: {confidence}")
            print(f"  ⚠️  Risk Score: {risk_score}")
            print(f"  ✅ Authorized: {is_authorized}")
            print(f"  📏 Mahalanobis: {mahalanobis}")
            print(f"  📐 Std Devs: {std_devs}")
            
            # Check for constant values
            if confidence == 0.718 and risk_score == 0.315:
                print("  🚨 PROBLEM: Getting exact constant values!")
            elif isinstance(confidence, (int, float)) and isinstance(risk_score, (int, float)):
                if abs(confidence - 0.718) < 0.01 and abs(risk_score - 0.315) < 0.01:
                    print("  ⚠️  WARNING: Very close to constant values")
                else:
                    print("  ✅ GOOD: Values are varying")
            
            results[user_type] = {
                'confidence': confidence,
                'risk_score': risk_score,
                'is_authorized': is_authorized,
                'mahalanobis_distance': mahalanobis,
                'standard_deviations': std_devs
            }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[user_type] = {'error': str(e)}
    
    return results

def analyze_results(results):
    """Analyze if the system is working correctly"""
    print("\n\n📈 RESULTS ANALYSIS")
    print("=" * 60)
    
    valid_results = {}
    for user_type, result in results.items():
        if 'error' not in result and isinstance(result.get('confidence'), (int, float)):
            valid_results[user_type] = result
    
    if len(valid_results) > 1:
        confidences = [r['confidence'] for r in valid_results.values()]
        risk_scores = [r['risk_score'] for r in valid_results.values()]
        
        conf_min, conf_max = min(confidences), max(confidences)
        risk_min, risk_max = min(risk_scores), max(risk_scores)
        
        conf_std = np.std(confidences) if len(confidences) > 1 else 0
        risk_std = np.std(risk_scores) if len(risk_scores) > 1 else 0
        
        print(f"📊 CONFIDENCE ANALYSIS:")
        print(f"  Values: {confidences}")
        print(f"  Range: {conf_min:.3f} - {conf_max:.3f}")
        print(f"  Std Dev: {conf_std:.3f}")
        print(f"  Status: {'✅ VARYING' if conf_std > 0.01 else '❌ CONSTANT'}")
        
        print(f"\n⚠️  RISK SCORE ANALYSIS:")
        print(f"  Values: {risk_scores}")
        print(f"  Range: {risk_min:.3f} - {risk_max:.3f}")
        print(f"  Std Dev: {risk_std:.3f}")
        print(f"  Status: {'✅ VARYING' if risk_std > 0.01 else '❌ CONSTANT'}")
        
        print(f"\n🎯 OVERALL SYSTEM STATUS:")
        if conf_std > 0.01 and risk_std > 0.01:
            print("  ✅ SYSTEM WORKING: Can distinguish between users")
        elif conf_std < 0.01 and risk_std < 0.01:
            print("  ❌ SYSTEM BROKEN: Producing constant scores")
            print("  🔧 ISSUE: Input data not varying or calculation problem")
        else:
            print("  ⚠️  PARTIAL WORKING: Some variation but not optimal")
            
        # Check for the specific problematic values
        if 0.718 in confidences and 0.315 in risk_scores:
            print("  🚨 CONFIRMED: System is stuck on 0.718/0.315 values")
            
    else:
        print("❌ Insufficient valid results for analysis")

def test_extreme_cases():
    """Test with extreme cases to see if we can break the constant pattern"""
    print("\n\n🎯 EXTREME CASES TEST")
    print("=" * 60)
    
    analyzer = BehavioralAnalyzer()
    baseline = generate_behavioral_pattern("normal_user")
    
    extreme_cases = {
        "empty_data": {
            'cursor_movements': [],
            'key_press_times': [],
            'click_timestamps': [],
            'idle_time': 0,
            'evasion_signals': {},
            'total_time': 0,
        },
        "huge_bot": {
            'cursor_movements': [{'x': 0, 'y': 0}] * 1000,
            'key_press_times': [10*i for i in range(100)],
            'click_timestamps': [50*i for i in range(20)],
            'idle_time': 0,
            'evasion_signals': {
                'is_automated_browser': True,
                'paste_detected': True,
                'unusual_timing': True,
                'suspicious_patterns': True,
                'evasion_detected': True
            },
            'total_time': 1000,
        }
    }
    
    for case_name, test_data in extreme_cases.items():
        print(f"\n🔍 Testing {case_name}:")
        try:
            result = analyzer.analyze_with_baseline_comparison(
                session_id=f'extreme_{case_name}',
                current_data=test_data,
                baseline_behavior_or_user_id=baseline
            )
            
            confidence = result.get('confidence', 'N/A')
            risk_score = result.get('risk_score', 'N/A')
            
            print(f"  📊 Confidence: {confidence}")
            print(f"  ⚠️  Risk Score: {risk_score}")
            
            if confidence == 0.718 and risk_score == 0.315:
                print("  🚨 STILL CONSTANT VALUES!")
            else:
                print("  ✅ Different values - system responding to input")
                
        except Exception as e:
            print(f"  ℹ️  Expected behavior: {e}")

def main():
    """Run the complete test"""
    print("🚀 BEHAVIORAL SYSTEM DIAGNOSTIC TEST")
    print("🕐 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Run main test
    results = test_behavioral_analysis()
    
    # Analyze results
    analyze_results(results)
    
    # Test extreme cases
    test_extreme_cases()
    
    print("\n📋 DIAGNOSTIC COMPLETE")
    print("=" * 60)
    
    # Save results
    with open('diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("💾 Results saved to: diagnostic_results.json")

if __name__ == "__main__":
    main()
