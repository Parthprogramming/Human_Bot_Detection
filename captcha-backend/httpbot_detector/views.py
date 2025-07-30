import json
import time
import hashlib
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.cache import cache
from django.db import models
from .models import HttpBotDetection
import os

logger = logging.getLogger(__name__)

class HttpBotDetector:
    def __init__(self):
        self.suspicious_user_agents = [
            'phantomjs', 'headlesschrome', 'selenium', 'puppeteer', 'playwright', 
            'cypress', 'webdriver', 'chromedriver', 'geckodriver',
            'python-requests', 'urllib', 'curl', 'wget', 'scrapy',
            'bot', 'crawler', 'spider', 'scraper', 'postman'
        ]
        
        # Common legitimate browser patterns to exclude
        self.legitimate_browsers = [
            'chrome', 'firefox', 'safari', 'edge', 'opera', 'mozilla'
        ]
        
        self.automation_headers = [
            'webdriver', 'selenium', 'phantomjs', 'headless-chrome',
            'automation', 'test-framework'
        ]
    
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def calculate_request_interval(self, ip_address):
        """Calculate time interval between requests from same IP"""
        cache_key = f"last_request_{ip_address}"
        last_request_time = cache.get(cache_key)
        current_time = time.time()
        
        if last_request_time:
            interval = current_time - last_request_time
        else:
            interval = None
        
        # Store current request time
        cache.set(cache_key, current_time, timeout=3600)  # 1 hour
        return interval
    
    def detect_suspicious_headers(self, request):
        """Detect suspicious headers that indicate automation"""
        suspicious = []
        headers = request.META
        
        # Check for automation-related headers
        for header_key, header_value in headers.items():
            if isinstance(header_value, str):
                header_value_lower = header_value.lower()
                for automation_indicator in self.automation_headers:
                    if automation_indicator in header_value_lower:
                        suspicious.append(f"{header_key}: {header_value}")
        
        # Check for missing common headers
        common_headers = ['HTTP_ACCEPT', 'HTTP_ACCEPT_LANGUAGE', 'HTTP_ACCEPT_ENCODING']
        missing_headers = [h for h in common_headers if h not in headers]
        if len(missing_headers) > 1:
            suspicious.append(f"Missing headers: {missing_headers}")
        
        return suspicious
    
    def is_headless_browser(self, user_agent):
        """Detect if request comes from headless browser"""
        user_agent_lower = user_agent.lower()
        headless_indicators = ['headless', 'phantomjs', 'htmlunit']
        return any(indicator in user_agent_lower for indicator in headless_indicators)
    
    def is_automation_tool(self, user_agent):
        """Detect if request comes from automation tool"""
        if not user_agent:
            return True  # Empty user agent is suspicious
            
        user_agent_lower = user_agent.lower()
        
        # Check if it's a legitimate browser first
        has_legitimate_browser = any(browser in user_agent_lower for browser in self.legitimate_browsers)
        
        # If it has legitimate browser indicators, be more careful
        if has_legitimate_browser:
            # Only flag if it explicitly contains automation keywords
            return any(f" {tool} " in f" {user_agent_lower} " or 
                      user_agent_lower.startswith(tool) or 
                      user_agent_lower.endswith(tool) 
                      for tool in ['selenium', 'webdriver', 'phantomjs', 'headless'])
        
        # If no legitimate browser indicators, check for automation tools
        return any(tool in user_agent_lower for tool in self.suspicious_user_agents)
    
    def generate_request_fingerprint(self, request):
        """Generate unique fingerprint for the request"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept = request.META.get('HTTP_ACCEPT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        fingerprint_string = f"{user_agent}|{accept}|{accept_language}|{accept_encoding}"
        return hashlib.md5(fingerprint_string.encode()).hexdigest()
    
    def extract_features_for_ml(self, request_data):
        """Extract features for ML model prediction"""
        try:
            features = {
                'request_interval': request_data.get('request_interval', 0) or 0,
                'user_agent_length': len(request_data.get('user_agent', '')),
                'has_cookies': 1 if request_data.get('cookies_present') else 0,
                'suspicious_headers_count': len(request_data.get('suspicious_headers', [])),
                'is_headless': 1 if request_data.get('is_headless_browser') else 0,
                'is_automation': 1 if request_data.get('automation_detected') else 0,
                'hour_of_day': datetime.now().hour,
                'is_weekend': 1 if datetime.now().weekday() >= 5 else 0,
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    def predict_bot_probability(self, features):
        """Predict if request is from bot using rule-based analysis"""
        try:
            # Rule-based scoring for bot probability - more conservative approach
            rule_based_score = 0.0
            bot_indicators = 0
            
            # Strong indicators of automation (high weight)
            if features.get('is_automation', 0):
                rule_based_score += 0.5
                bot_indicators += 1
            
            if features.get('is_headless', 0):
                rule_based_score += 0.4
                bot_indicators += 1
            
            # Medium indicators (moderate weight)
            if features.get('suspicious_headers_count', 0) > 2:  # Only if multiple suspicious headers
                rule_based_score += 0.3
                bot_indicators += 1
            
            # Check for very rapid requests (less than 0.5 seconds)
            if features.get('request_interval', 0) < 0.5 and features.get('request_interval', 0) > 0:
                rule_based_score += 0.2
                bot_indicators += 1
            
            # Weak indicators (low weight) - only add if we already have strong indicators
            if bot_indicators > 0:
                # Missing cookies is only suspicious if other bot indicators are present
                if not features.get('has_cookies', 0):
                    rule_based_score += 0.1
                
                # Unusual timing patterns (only if other indicators present)
                hour = features.get('hour_of_day', 12)
                if hour < 4 or hour > 23:  # Very unusual hours
                    rule_based_score += 0.05
            
            # Require multiple indicators for high confidence bot detection
            if bot_indicators < 2:
                rule_based_score = min(rule_based_score, 0.3)  # Cap at 30% if less than 2 indicators
            
            return min(rule_based_score, 1.0)
        
        except Exception as e:
            logger.error(f"Error in rule-based prediction: {e}")
            return 0.1  # Default to low bot probability on error

detector = HttpBotDetector()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def detect_http_bot(request):
    """Main endpoint for HTTP bot detection"""
    try:
        # Extract request information
        ip_address = detector.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        endpoint = request.path
        method = request.method
        timestamp = timezone.now()
        
        # Calculate request interval
        request_interval = detector.calculate_request_interval(ip_address)
        
        # Analyze request
        cookies_present = bool(request.COOKIES)
        suspicious_headers = detector.detect_suspicious_headers(request)
        is_headless = detector.is_headless_browser(user_agent)
        is_automation = detector.is_automation_tool(user_agent)
        request_fingerprint = detector.generate_request_fingerprint(request)
        
        # Validate payload schema (for POST requests)
        payload_schema_valid = True
        if method == 'POST':
            try:
                if request.content_type == 'application/json':
                    json.loads(request.body)
            except json.JSONDecodeError:
                payload_schema_valid = False
        
        # Check rate limiting
        rate_limit_key = f"rate_limit_{ip_address}"
        request_count = cache.get(rate_limit_key, 0)
        rate_limit_exceeded = request_count > 100  # More than 100 requests per hour
        cache.set(rate_limit_key, request_count + 1, timeout=3600)
        
        # Prepare data for ML model
        request_data = {
            'request_interval': request_interval,
            'user_agent': user_agent,
            'cookies_present': cookies_present,
            'suspicious_headers': suspicious_headers,
            'is_headless_browser': is_headless,
            'automation_detected': is_automation,
        }
        
        # Extract features and predict
        features = detector.extract_features_for_ml(request_data)
        bot_probability = detector.predict_bot_probability(features)
        
        # Determine final classification - more conservative approach
        confidence = abs(bot_probability - 0.5) * 2  # Scale to 0-1
        is_bot = bot_probability > 0.6  # Raised threshold from 0.5 to 0.6
        classification = 'HTTP_Client_Bot' if is_bot else 'Human'
        
        # Generate session ID if not present
        session_id = request.session.session_key or request.META.get('HTTP_X_SESSION_ID', 'anonymous')
        
        # Save detection result
        detection_record = HttpBotDetection.objects.create(
            ip_address=ip_address,
            timestamp=timestamp,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            request_interval=request_interval,
            payload_schema_valid=payload_schema_valid,
            cookies_present=cookies_present,
            classification=classification,
            confidence=confidence,
            suspicious_headers=suspicious_headers,
            request_fingerprint=request_fingerprint,
            session_id=session_id,
            is_headless_browser=is_headless,
            automation_detected=is_automation,
            rate_limit_exceeded=rate_limit_exceeded
        )
        
        logger.info(f"HTTP Bot Detection - IP: {ip_address}, Prediction: {classification}, "
                   f"Confidence: {confidence:.2f}, Bot Probability: {bot_probability:.2f}")
        
        # Return response based on detection result - higher threshold for blocking
        if is_bot and confidence > 0.8:  # Raised from 0.7 to 0.8
            return JsonResponse({
                'status': 'blocked',
                'message': 'Automated request detected. Access denied.',
                'detection_id': detection_record.id,
                'classification': classification,
                'confidence': round(confidence * 100, 2),
                'reason': 'High probability of bot activity',
                'detected_indicators': {
                    'automation_tool': is_automation,
                    'headless_browser': is_headless,
                    'suspicious_headers': len(suspicious_headers) > 0,
                    'rate_limit_exceeded': rate_limit_exceeded,
                    'fast_requests': request_interval is not None and request_interval < 1.0
                }
            }, status=403)
        
        return JsonResponse({
            'status': 'allowed',
            'message': 'Request appears to be from human user.',
            'detection_id': detection_record.id,
            'classification': classification,
            'confidence': round(confidence * 100, 2),
            'session_info': {
                'session_id': session_id,
                'fingerprint': request_fingerprint[:8],  # First 8 chars only
                'timestamp': timestamp.isoformat()
            }
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error in HTTP bot detection: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error during bot detection',
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_detection_stats(request):
    """Get statistics about HTTP bot detection"""
    try:
        # Last 24 hours stats
        last_24h = timezone.now() - timedelta(hours=24)
        recent_detections = HttpBotDetection.objects.filter(timestamp__gte=last_24h)
        
        total_requests = recent_detections.count()
        bot_requests = recent_detections.filter(classification='HTTP_Client_Bot').count()
        human_requests = recent_detections.filter(classification='Human').count()
        
        # Top suspicious IPs
        suspicious_ips = recent_detections.filter(
            classification='HTTP_Client_Bot'
        ).values('ip_address').annotate(
            count=models.Count('ip_address')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'status': 'success',
            'stats': {
                'last_24h': {
                    'total_requests': total_requests,
                    'bot_requests': bot_requests,
                    'human_requests': human_requests,
                    'bot_percentage': round((bot_requests / total_requests * 100) if total_requests > 0 else 0, 2)
                },
                'suspicious_ips': list(suspicious_ips),
                'detection_method': 'rule-based'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting detection stats: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
