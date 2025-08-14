"""
HYBRID AUTHENTICATION SYSTEM RECOMMENDATION
===========================================

After extensive testing of behavioral analysis approaches, we've determined that
behavioral biometrics alone are insufficient for reliable user authentication.

RECOMMENDED SOLUTION: Multi-Factor Behavioral + Traditional Security
"""

class HybridAuthenticationSystem:
    """
    Combines behavioral analysis with traditional security measures
    for robust user authentication
    """
    
    def __init__(self):
        self.behavioral_weight = 0.3  # Reduced reliance on behavioral data
        self.traditional_weight = 0.7  # Higher reliance on proven methods
    
    def authenticate_user(self, behavioral_data, session_data, user_context):
        """
        Multi-factor authentication combining:
        1. Behavioral patterns (30% weight)
        2. Session security (40% weight) 
        3. Context verification (30% weight)
        """
        
        # Factor 1: Behavioral Analysis (Simplified)
        behavioral_score = self.analyze_behavioral_patterns(behavioral_data)
        
        # Factor 2: Session Security
        session_score = self.analyze_session_security(session_data)
        
        # Factor 3: Context Verification
        context_score = self.analyze_user_context(user_context)
        
        # Combined score
        total_score = (
            behavioral_score * 0.3 +
            session_score * 0.4 +
            context_score * 0.3
        )
        
        # Decision logic
        if total_score >= 0.8:
            return {"authorized": True, "confidence": "high", "reason": "Multi-factor authentication passed"}
        elif total_score >= 0.6:
            return {"authorized": True, "confidence": "medium", "reason": "Sufficient multi-factor score", "recommend_2fa": True}
        else:
            return {"authorized": False, "confidence": "low", "reason": "Multi-factor authentication failed"}
    
    def analyze_behavioral_patterns(self, data):
        """
        Simplified behavioral analysis focusing on basic patterns
        """
        # Basic checks for human-like behavior
        has_variation = len(set(data.get('key_press_times', []))) > 1
        reasonable_speed = self.check_reasonable_typing_speed(data)
        mouse_activity = len(data.get('cursor_movements', [])) > 0
        
        score = 0.0
        if has_variation: score += 0.4
        if reasonable_speed: score += 0.4
        if mouse_activity: score += 0.2
        
        return score
    
    def analyze_session_security(self, session_data):
        """
        Analyze session-based security factors
        """
        score = 0.0
        
        # Check session continuity
        if session_data.get('session_duration', 0) > 30:  # Active for >30 seconds
            score += 0.3
        
        # Check for session hijacking indicators
        if session_data.get('ip_consistency', True):
            score += 0.3
        
        # Check user agent consistency
        if session_data.get('user_agent_consistent', True):
            score += 0.2
        
        # Check for rapid successive attempts (bot indicator)
        if session_data.get('attempt_interval', 1000) > 500:  # >500ms between attempts
            score += 0.2
        
        return score
    
    def analyze_user_context(self, context):
        """
        Analyze contextual factors
        """
        score = 0.0
        
        # Time-based checks
        if self.is_reasonable_login_time(context.get('login_time')):
            score += 0.3
        
        # Device consistency
        if context.get('known_device', False):
            score += 0.4
        
        # Geographic consistency
        if context.get('expected_location', False):
            score += 0.3
        
        return score
    
    def check_reasonable_typing_speed(self, data):
        """Check if typing speed is within human range"""
        key_times = data.get('key_press_times', [])
        if len(key_times) < 2:
            return True
        
        intervals = [key_times[i] - key_times[i-1] for i in range(1, len(key_times))]
        avg_interval = sum(intervals) / len(intervals)
        
        # Human typing: 50-500ms between keystrokes typically
        return 50 <= avg_interval <= 1000
    
    def is_reasonable_login_time(self, login_time):
        """Check if login time is reasonable for the user"""
        # This would check against user's historical login patterns
        # For now, just check if it's during reasonable hours
        hour = login_time.hour if login_time else 12
        return 6 <= hour <= 23  # 6 AM to 11 PM

# PRACTICAL IMPLEMENTATION RECOMMENDATIONS:

def implement_practical_solution():
    """
    Practical recommendations for your current system
    """
    recommendations = {
        "immediate_actions": [
            "1. Reduce behavioral analysis weight to 30%",
            "2. Implement session security checks (IP, User-Agent, timing)",
            "3. Add device fingerprinting",
            "4. Implement rate limiting for login attempts",
            "5. Add geographic/time-based context checks"
        ],
        
        "behavioral_simplification": [
            "1. Use basic human vs bot detection (not user identification)",
            "2. Check for reasonable typing speeds (50-1000ms intervals)",
            "3. Verify mouse movement exists (any movement = likely human)",
            "4. Detect overly regular patterns (likely bot)",
            "5. Flag extremely fast or slow interactions"
        ],
        
        "additional_security": [
            "1. Implement CAPTCHA for suspicious sessions", 
            "2. Add email/SMS verification for new devices",
            "3. Use session tokens with short expiry",
            "4. Implement account lockout after multiple failures",
            "5. Add user behavior learning over time"
        ],
        
        "long_term_improvements": [
            "1. Collect more behavioral data over longer sessions",
            "2. Implement machine learning on larger datasets",
            "3. Add biometric options (fingerprint, face recognition)",
            "4. Implement adaptive risk scoring",
            "5. Add user-specific behavioral profiles over time"
        ]
    }
    
    return recommendations

# SIMPLIFIED BEHAVIORAL CHECKER FOR YOUR CURRENT SYSTEM:

def simple_human_detector(behavioral_data):
    """
    Simplified function to replace complex behavioral analysis
    Focus on basic human vs bot detection rather than user identification
    """
    
    score = 0.0
    checks = []
    
    # Check 1: Variable keystroke timing (humans aren't perfectly regular)
    key_times = behavioral_data.get('key_press_times', [])
    if len(key_times) > 2:
        intervals = [key_times[i] - key_times[i-1] for i in range(1, len(key_times))]
        if len(set(intervals)) > 1:  # Has variation
            score += 0.25
            checks.append("✅ Variable keystroke timing")
        else:
            checks.append("❌ Overly regular keystroke timing (bot-like)")
    
    # Check 2: Reasonable typing speed
    if key_times and len(key_times) > 1:
        avg_interval = sum(intervals) / len(intervals) if 'intervals' in locals() else 200
        if 50 <= avg_interval <= 1000:  # Human range
            score += 0.25
            checks.append("✅ Human-like typing speed")
        else:
            checks.append("❌ Unrealistic typing speed")
    
    # Check 3: Mouse movement exists
    mouse_movements = behavioral_data.get('cursor_movements', [])
    if len(mouse_movements) > 0:
        score += 0.25
        checks.append("✅ Mouse movement detected")
    else:
        checks.append("⚠️ No mouse movement (keyboard-only)")
    
    # Check 4: Interaction diversity
    total_interactions = len(key_times) + len(mouse_movements) + len(behavioral_data.get('click_timestamps', []))
    if total_interactions >= 5:
        score += 0.25
        checks.append("✅ Sufficient interaction volume")
    else:
        checks.append("⚠️ Limited interaction data")
    
    # Determine result
    if score >= 0.75:
        result = "LIKELY_HUMAN"
        confidence = "HIGH"
    elif score >= 0.5:
        result = "POSSIBLY_HUMAN" 
        confidence = "MEDIUM"
    else:
        result = "SUSPICIOUS"
        confidence = "LOW"
    
    return {
        'result': result,
        'confidence': confidence,
        'score': score,
        'checks': checks,
        'recommendation': 'ALLOW' if score >= 0.5 else 'BLOCK_OR_CAPTCHA'
    }

# Example usage for your current system:
def test_simple_detector():
    """Test the simplified human detection"""
    
    # Test data
    human_data = {
        'key_press_times': [100, 250, 420, 580, 760],
        'cursor_movements': [{'x': 100, 'y': 200}, {'x': 150, 'y': 220}],
        'click_timestamps': [300, 800]
    }
    
    bot_data = {
        'key_press_times': [100, 200, 300, 400, 500],  # Too regular
        'cursor_movements': [],  # No mouse movement
        'click_timestamps': [600, 700, 800]  # Too regular
    }
    
    print("SIMPLE HUMAN DETECTOR TEST:")
    print("=" * 50)
    
    print("\n🧑 HUMAN DATA:")
    human_result = simple_human_detector(human_data)
    print(f"Result: {human_result['result']}")
    print(f"Confidence: {human_result['confidence']}")
    print(f"Score: {human_result['score']:.2f}/1.00")
    print("Checks:")
    for check in human_result['checks']:
        print(f"  {check}")
    
    print("\n🤖 BOT DATA:")
    bot_result = simple_human_detector(bot_data)
    print(f"Result: {bot_result['result']}")
    print(f"Confidence: {bot_result['confidence']}")
    print(f"Score: {bot_result['score']:.2f}/1.00")
    print("Checks:")
    for check in bot_result['checks']:
        print(f"  {check}")

if __name__ == "__main__":
    print("HYBRID AUTHENTICATION SYSTEM RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = implement_practical_solution()
    
    for category, items in recommendations.items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        for item in items:
            print(f"  {item}")
    
    print("\n" + "=" * 60)
    test_simple_detector()
