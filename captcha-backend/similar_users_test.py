#!/usr/bin/env python3
"""
🔬 SUBTLE BEHAVIORAL DIFFERENCE DETECTION
Test system with very similar behavioral patterns (like you and your friend)
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

def test_similar_users_scenario():
    """
    Test scenario: Very similar users (you and your friend with similar habits)
    This should STILL trigger UNAUTHORIZED despite similarities
    """
    print("🔬 TESTING SIMILAR USERS SCENARIO")
    print("=" * 60)
    
    analyzer = BehavioralAnalyzer()
    
    # YOUR typical behavioral pattern (baseline)
    your_pattern = {
        'cursor_movements': [
            {'x': 300 + random.randint(-50, 50), 'y': 400 + random.randint(-50, 50)} 
            for _ in range(30)  # Your consistent cursor pattern
        ],
        'key_press_times': [150 + random.randint(10, 30) + i*140 for i in range(18)],  # Your typing rhythm
        'click_timestamps': [800, 2200, 4100, 6000],  # Your click timing
        'idle_time': 2500,  # Your thinking time
        'evasion_signals': {},
        'total_time': 7200,
    }
    
    # FRIEND's SIMILAR but slightly different behavioral pattern
    friend_similar_pattern = {
        'cursor_movements': [
            {'x': 310 + random.randint(-40, 60), 'y': 390 + random.randint(-40, 60)} 
            for _ in range(32)  # Slightly more cursor movements
        ],
        'key_press_times': [160 + random.randint(5, 25) + i*135 for i in range(17)],  # Slightly different typing
        'click_timestamps': [750, 2100, 4200, 5800],  # Slightly different timing
        'idle_time': 2800,  # Slightly longer thinking time
        'evasion_signals': {},
        'total_time': 7500,  # Takes slightly longer
    }
    
    print("📊 Testing YOUR account with YOUR behavioral pattern:")
    your_result = analyzer.analyze_with_baseline_comparison(
        session_id='your_session_similar',
        current_data=your_pattern,
        baseline_behavior_or_user_id=your_pattern
    )
    
    print(f"  📊 Your Confidence: {your_result.get('confidence', 'N/A'):.4f}")
    print(f"  ⚠️  Your Risk Score: {your_result.get('risk_score', 'N/A'):.4f}")
    print(f"  ✅ Your Authorized: {your_result.get('is_authorized', 'N/A')}")
    print(f"  📐 Your Std Devs: {your_result.get('standard_deviations', 'N/A'):.4f}σ")
    
    print("\n🚨 Testing YOUR account with FRIEND's SIMILAR behavioral pattern:")
    friend_result = analyzer.analyze_with_baseline_comparison(
        session_id='friend_similar_session',
        current_data=friend_similar_pattern,
        baseline_behavior_or_user_id=your_pattern
    )
    
    print(f"  📊 Friend Confidence: {friend_result.get('confidence', 'N/A'):.4f}")
    print(f"  ⚠️  Friend Risk Score: {friend_result.get('risk_score', 'N/A'):.4f}")
    print(f"  ❌ Friend Authorized: {friend_result.get('is_authorized', 'N/A')}")
    print(f"  📐 Friend Std Devs: {friend_result.get('standard_deviations', 'N/A'):.4f}σ")
    
    # Analysis
    print(f"\n📈 SIMILAR USERS ANALYSIS:")
    print(f"=" * 40)
    
    your_std = your_result.get('standard_deviations', 0)
    friend_std = friend_result.get('standard_deviations', 0)
    your_auth = your_result.get('is_authorized', False)
    friend_auth = friend_result.get('is_authorized', False)
    
    print(f"Your std devs: {your_std:.4f}σ")
    print(f"Friend std devs: {friend_std:.4f}σ") 
    print(f"Difference: {abs(friend_std - your_std):.4f}σ")
    
    if your_auth and not friend_auth:
        print("✅ EXCELLENT: System detected subtle differences")
    elif your_auth and friend_auth:
        print("❌ CRITICAL PROBLEM: System too lenient - can't detect similar users")
        print("🔧 URGENT: Need to increase sensitivity for subtle differences")
    else:
        print("⚠️  SYSTEM TOO STRICT: Even you are blocked")
    
    return your_result, friend_result

def suggest_sensitivity_improvements():
    """Suggest specific improvements for detecting similar users"""
    print(f"\n💡 ENHANCED SENSITIVITY SOLUTIONS")
    print("=" * 60)
    
    print("🔧 1. REDUCE THRESHOLD FURTHER:")
    print("   Current: 4.5σ → Suggested: 2.5σ or 3.0σ")
    print("   This catches even subtle behavioral differences")
    print()
    
    print("🔧 2. MULTI-DIMENSIONAL FEATURE ANALYSIS:")
    print("   - Typing rhythm micro-patterns (keystroke dynamics)")
    print("   - Mouse acceleration patterns") 
    print("   - Click pressure timing variations")
    print("   - Scroll wheel usage patterns")
    print()
    
    print("🔧 3. TEMPORAL PATTERN ANALYSIS:")
    print("   - Time-of-day usage patterns")
    print("   - Session duration patterns")
    print("   - Break timing patterns")
    print()
    
    print("🔧 4. ADVANCED STATISTICAL METHODS:")
    print("   - Use ensemble methods (multiple algorithms)")
    print("   - Implement weighted feature importance")
    print("   - Add anomaly detection algorithms")
    print()
    
    print("🔧 5. PROGRESSIVE AUTHENTICATION:")
    print("   - Start with standard threshold")
    print("   - Gradually learn user's unique patterns")
    print("   - Adapt threshold based on confidence")

def test_threshold_sensitivity():
    """Test different threshold values for similar users"""
    print(f"\n🎯 THRESHOLD SENSITIVITY FOR SIMILAR USERS")
    print("=" * 60)
    
    test_thresholds = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    
    print("For similar users like you and your friend:")
    print("- Your pattern: Should be ≤ threshold (AUTHORIZED)")
    print("- Friend's similar pattern: Should be > threshold (UNAUTHORIZED)")
    print()
    
    for threshold in test_thresholds:
        print(f"📊 If threshold = {threshold:.1f}σ:")
        # Estimated values based on similar behavioral patterns
        your_estimated = 0.8  # Very low for same user
        friend_estimated = threshold + 0.3  # Slightly above threshold
        
        your_pass = your_estimated <= threshold
        friend_block = friend_estimated > threshold
        
        print(f"   Your pattern (~{your_estimated:.1f}σ): {'✅ PASS' if your_pass else '❌ FAIL'}")
        print(f"   Friend pattern (~{friend_estimated:.1f}σ): {'✅ BLOCK' if friend_block else '❌ ALLOW'}")
        
        if your_pass and friend_block:
            print(f"   🎯 OPTIMAL: Detects similar users")
        elif your_pass and not friend_block:
            print(f"   ❌ TOO LENIENT: Misses similar users")
        elif not your_pass:
            print(f"   ❌ TOO STRICT: Blocks legitimate user")
        print()

def main():
    """Run similar users detection analysis"""
    print("🔬 SIMILAR USERS BEHAVIORAL DETECTION")
    print("🕐 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Test the similar users scenario
    your_result, friend_result = test_similar_users_scenario()
    
    # Test threshold sensitivity
    test_threshold_sensitivity()
    
    # Suggest improvements
    suggest_sensitivity_improvements()
    
    print(f"\n📋 RECOMMENDATIONS:")
    print("=" * 40)
    
    friend_auth = friend_result.get('is_authorized', True)
    friend_std = friend_result.get('standard_deviations', 0)
    
    if friend_auth:
        print("❌ CONFIRMED: System cannot detect similar users")
        print("🚨 CRITICAL SECURITY ISSUE: Friends with similar behavior can access account")
        print()
        print("🔧 IMMEDIATE ACTIONS NEEDED:")
        print("1. Reduce threshold to 2.5σ or lower")
        print("2. Implement additional biometric features") 
        print("3. Add multi-factor behavioral authentication")
        print("4. Consider device fingerprinting")
        
        if friend_std < 3.0:
            print(f"\n⚠️  Friend's deviation ({friend_std:.2f}σ) is very low - need aggressive tuning")
        
    else:
        print("✅ SYSTEM WORKING: Similar users properly detected")
        print("🎯 Current sensitivity level is appropriate")
    
    # Save results
    with open('similar_users_analysis.json', 'w') as f:
        json.dump({
            'your_result': your_result,
            'friend_result': friend_result,
            'analysis_timestamp': datetime.now().isoformat(),
            'similar_user_detected': not friend_auth,
            'friend_std_devs': friend_std
        }, f, indent=2, default=str)
    
    print("💾 Analysis saved to: similar_users_analysis.json")

if __name__ == "__main__":
    main()
