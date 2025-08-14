#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE BEHAVIORAL ANALYSIS TESTING SYSTEM
Test whether the behavioral analysis can distinguish between different users
"""

import os
import django
import json
import requests
import time
import random
import numpy as np
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'captcha.settings')
django.setup()

from user.views import BehavioralAnalyzer
from user.models import UserBaselineBehavior

class BehavioralSystemTester:
    def __init__(self):
        self.analyzer = BehavioralAnalyzer()
        self.base_url = "http://localhost:8000"
        
    def generate_user_behavioral_pattern(self, user_type):
        """Generate distinct behavioral patterns for different user types"""
        
        if user_type == "fast_typer":
            return {
                'cursor_movements': [{'x': x*10, 'y': y*5} for x, y in zip(range(50), range(50))],
                'key_press_times': [100 + i*80 for i in range(20)],  # Fast typing (80ms intervals)
                'click_timestamps': [500, 1500, 3000],
                'idle_time': 1000,  # Short idle time
                'evasion_signals': {},
                'total_time': 5000,
                'cursor_speeds': [random.uniform(200, 400) for _ in range(10)],  # Fast cursor
                'typing_speed': 120,  # Fast typing
                'session_id': f'fast_typer_{int(time.time())}'
            }
            
        elif user_type == "slow_typer":
            return {
                'cursor_movements': [{'x': x*3, 'y': y*2} for x, y in zip(range(20), range(20))],
                'key_press_times': [200 + i*300 for i in range(15)],  # Slow typing (300ms intervals)
                'click_timestamps': [800, 2000, 4000],
                'idle_time': 5000,  # Long idle time
                'evasion_signals': {},
                'total_time': 10000,
                'cursor_speeds': [random.uniform(50, 150) for _ in range(8)],  # Slow cursor
                'typing_speed': 40,  # Slow typing
                'session_id': f'slow_typer_{int(time.time())}'
            }
            
        elif user_type == "bot_like":
            return {
                'cursor_movements': [{'x': x*20, 'y': 0} for x in range(10)],  # Linear movement
                'key_press_times': [50 + i*50 for i in range(30)],  # Very regular intervals
                'click_timestamps': [100, 200, 300, 400],  # Very regular clicks
                'idle_time': 0,  # No idle time
                'evasion_signals': {
                    'is_automated_browser': True,
                    'paste_detected': True,
                    'unusual_timing': True
                },
                'total_time': 2000,
                'cursor_speeds': [200, 200, 200, 200, 200],  # Constant speed
                'typing_speed': 200,  # Unrealistic typing speed
                'session_id': f'bot_like_{int(time.time())}'
            }
            
        elif user_type == "normal_user":
            return {
                'cursor_movements': [{'x': random.randint(0, 800), 'y': random.randint(0, 600)} for _ in range(30)],
                'key_press_times': [150 + random.randint(50, 200) + i*150 for i in range(18)],  # Variable intervals
                'click_timestamps': [600, 1800, 3200],
                'idle_time': 3000,  # Moderate idle time
                'evasion_signals': {},
                'total_time': 8000,
                'cursor_speeds': [random.uniform(100, 250) for _ in range(12)],  # Variable speed
                'typing_speed': 80,  # Normal typing
                'session_id': f'normal_user_{int(time.time())}'
            }
            
        else:  # erratic_user
            return {
                'cursor_movements': [{'x': random.randint(0, 1200), 'y': random.randint(0, 800)} for _ in range(100)],
                'key_press_times': [random.randint(50, 500) + i*random.randint(100, 400) for i in range(25)],
                'click_timestamps': [random.randint(100, 1000) for _ in range(8)],
                'idle_time': random.randint(2000, 8000),
                'evasion_signals': {},
                'total_time': 15000,
                'cursor_speeds': [random.uniform(20, 500) for _ in range(20)],  # Very variable
                'typing_speed': random.randint(30, 150),
                'session_id': f'erratic_user_{int(time.time())}'
            }

    def test_direct_analysis(self):
        """Test the behavioral analyzer directly with different user patterns"""
        print("🧪 TESTING DIRECT BEHAVIORAL ANALYSIS")
        print("=" * 60)
        
        user_types = ["fast_typer", "slow_typer", "bot_like", "normal_user", "erratic_user"]
        results = {}
        
        # Generate baseline for comparison
        baseline = self.generate_user_behavioral_pattern("normal_user")
        
        for user_type in user_types:
            print(f"\n🔍 Testing {user_type.upper()}:")
            
            # Generate user behavior
            current_data = self.generate_user_behavioral_pattern(user_type)
            
            # Analyze behavior
            try:
                result = self.analyzer.analyze_with_baseline_comparison(
                    session_id=current_data['session_id'],
                    current_data=current_data,
                    baseline_behavior_or_user_id=baseline
                )
                
                confidence = result.get('confidence', 'N/A')
                risk_score = result.get('risk_score', 'N/A')
                is_authorized = result.get('is_authorized', 'N/A')
                reason = result.get('authorization_reason', 'N/A')
                
                print(f"  📊 Confidence: {confidence}")
                print(f"  ⚠️  Risk Score: {risk_score}")
                print(f"  ✅ Authorized: {is_authorized}")
                print(f"  📝 Reason: {reason[:80]}...")
                
                results[user_type] = {
                    'confidence': confidence,
                    'risk_score': risk_score,
                    'is_authorized': is_authorized,
                    'reason': reason
                }
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                results[user_type] = {'error': str(e)}
        
        return results

    def test_api_endpoint(self):
        """Test the actual API endpoint with different behavioral patterns"""
        print("\n\n🌐 TESTING API ENDPOINT")
        print("=" * 60)
        
        user_types = ["fast_typer", "slow_typer", "bot_like", "normal_user", "erratic_user"]
        api_results = {}
        
        baseline = self.generate_user_behavioral_pattern("normal_user")
        
        for user_type in user_types:
            print(f"\n🔍 API Testing {user_type.upper()}:")
            
            current_data = self.generate_user_behavioral_pattern(user_type)
            
            # Prepare API request
            payload = {
                'session_id': current_data['session_id'],
                'current_data': current_data,
                'baseline_data': baseline
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/user/analyze-behavior/",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    confidence = result.get('confidence', 'N/A')
                    risk_score = result.get('risk_score', 'N/A')
                    is_authorized = result.get('is_authorized', 'N/A')
                    
                    print(f"  📊 API Confidence: {confidence}")
                    print(f"  ⚠️  API Risk Score: {risk_score}")
                    print(f"  ✅ API Authorized: {is_authorized}")
                    
                    api_results[user_type] = {
                        'confidence': confidence,
                        'risk_score': risk_score,
                        'is_authorized': is_authorized
                    }
                else:
                    print(f"  ❌ API Error: {response.status_code} - {response.text}")
                    api_results[user_type] = {'error': f"HTTP {response.status_code}"}
                    
            except Exception as e:
                print(f"  ❌ Request Error: {e}")
                api_results[user_type] = {'error': str(e)}
                
        return api_results

    def analyze_variation(self, results):
        """Analyze if the system is producing varied results"""
        print("\n\n📈 VARIATION ANALYSIS")
        print("=" * 60)
        
        confidence_values = []
        risk_values = []
        
        for user_type, result in results.items():
            if 'error' not in result and result.get('confidence') != 'N/A':
                try:
                    confidence_values.append(float(result['confidence']))
                    risk_values.append(float(result['risk_score']))
                except (ValueError, TypeError):
                    continue
        
        if len(confidence_values) > 1:
            conf_min = min(confidence_values)
            conf_max = max(confidence_values)
            conf_std = np.std(confidence_values)
            
            risk_min = min(risk_values)
            risk_max = max(risk_values)
            risk_std = np.std(risk_values)
            
            print(f"📊 CONFIDENCE SCORES:")
            print(f"  Range: {conf_min:.3f} - {conf_max:.3f}")
            print(f"  Standard Deviation: {conf_std:.3f}")
            print(f"  Variation: {'GOOD' if conf_std > 0.05 else 'POOR - CONSTANT VALUES!'}")
            
            print(f"\n⚠️  RISK SCORES:")
            print(f"  Range: {risk_min:.3f} - {risk_max:.3f}")
            print(f"  Standard Deviation: {risk_std:.3f}")
            print(f"  Variation: {'GOOD' if risk_std > 0.05 else 'POOR - CONSTANT VALUES!'}")
            
            print(f"\n🎯 SYSTEM STATUS:")
            if conf_std > 0.05 and risk_std > 0.05:
                print("  ✅ WORKING CORRECTLY - System distinguishes between users")
            else:
                print("  ❌ NOT WORKING - System produces constant scores")
                print("  🔧 SOLUTION NEEDED: Input data diversity or calculation logic")
                
        else:
            print("❌ Insufficient data for variation analysis")

    def test_specific_values(self):
        """Test if the system is stuck on 0.718/0.315 values"""
        print("\n\n🎯 SPECIFIC VALUES TEST (0.718 / 0.315)")
        print("=" * 60)
        
        # Test with extremely different inputs
        extreme_tests = {
            "minimal_data": {
                'cursor_movements': [{'x': 0, 'y': 0}],
                'key_press_times': [100],
                'click_timestamps': [50],
                'idle_time': 100,
                'evasion_signals': {},
                'total_time': 1000
            },
            "massive_data": {
                'cursor_movements': [{'x': i*100, 'y': i*50} for i in range(200)],
                'key_press_times': list(range(50, 10000, 50)),
                'click_timestamps': list(range(100, 5000, 100)),
                'idle_time': 10000,
                'evasion_signals': {},
                'total_time': 30000
            },
            "bot_obvious": {
                'cursor_movements': [{'x': 100, 'y': 100}] * 10,
                'key_press_times': [50 * i for i in range(50)],
                'click_timestamps': [100 * i for i in range(10)],
                'idle_time': 0,
                'evasion_signals': {
                    'is_automated_browser': True,
                    'paste_detected': True,
                    'unusual_timing': True,
                    'suspicious_patterns': True,
                    'evasion_detected': True
                },
                'total_time': 2000
            }
        }
        
        baseline = self.generate_user_behavioral_pattern("normal_user")
        
        for test_name, test_data in extreme_tests.items():
            print(f"\n🔍 Testing {test_name}:")
            try:
                result = self.analyzer.analyze_with_baseline_comparison(
                    session_id=f'test_{test_name}',
                    current_data=test_data,
                    baseline_behavior_or_user_id=baseline
                )
                
                confidence = result.get('confidence', 'N/A')
                risk_score = result.get('risk_score', 'N/A')
                
                print(f"  📊 Confidence: {confidence}")
                print(f"  ⚠️  Risk Score: {risk_score}")
                
                # Check if we're getting the problematic constant values
                if confidence == 0.718 and risk_score == 0.315:
                    print("  🚨 PROBLEM: Getting constant values 0.718/0.315!")
                elif abs(float(confidence) - 0.718) < 0.001 and abs(float(risk_score) - 0.315) < 0.001:
                    print("  🚨 PROBLEM: Very close to constant values!")
                else:
                    print("  ✅ Good: Different values from constants")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")

    def run_complete_test(self):
        """Run the complete test suite"""
        print("🚀 STARTING COMPREHENSIVE BEHAVIORAL SYSTEM TEST")
        print("=" * 80)
        print(f"⏰ Test started at: {datetime.now()}")
        
        # Test 1: Direct Analysis
        direct_results = self.test_direct_analysis()
        
        # Test 2: API Endpoint
        api_results = self.test_api_endpoint()
        
        # Test 3: Variation Analysis
        self.analyze_variation(direct_results)
        
        # Test 4: Specific Values Test
        self.test_specific_values()
        
        print("\n\n📋 FINAL SUMMARY")
        print("=" * 60)
        print("✅ Tests completed successfully")
        print("📊 Check the variation analysis above for system status")
        print("🔧 If showing 'POOR - CONSTANT VALUES', the system needs fixes")
        
        return {
            'direct_results': direct_results,
            'api_results': api_results,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Main testing function"""
    tester = BehavioralSystemTester()
    results = tester.run_complete_test()
    
    # Save results to file
    with open('behavioral_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: behavioral_test_results.json")

if __name__ == "__main__":
    main()
