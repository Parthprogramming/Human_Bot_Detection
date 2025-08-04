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
import os,re

logger = logging.getLogger(__name__)

class HttpBotDetector:
    def __init__(self):
        self.suspicious_user_agents = [
            'phantomjs', 'headlesschrome', 'selenium', 'puppeteer', 'playwright', 
            'cypress', 'webdriver', 'chromedriver', 'geckodriver', 'edgedriver',
            'python-requests', 'urllib', 'curl', 'wget', 'scrapy', 'httpie',
            'bot', 'crawler', 'spider', 'scraper', 'postman', 'insomnia',
            'requests', 'aiohttp', 'axios', 'fetch', 'node-fetch', 'got',
            'jsdom', 'zombie', 'nightmare', 'casper', 'splinter', 'mechanize',
            'beautifulsoup', 'lxml', 'cheerio', 'apache-httpclient', 'okhttp',
            'java', 'python', 'perl', 'ruby', 'go-http', 'libwww', 'lwp',
            'winhttp', 'urlgrabber', 'pycurl', 'tornado', 'twisted',
            'headless', 'automated', 'test', 'robot', 'script', 'tool'
        ]
        
        # Common legitimate browser patterns to exclude
        self.legitimate_browsers = [
            'chrome', 'firefox', 'safari', 'edge', 'opera', 'mozilla'
        ]
        
        # Enhanced automation detection patterns
        self.automation_headers = [
            'webdriver', 'selenium', 'phantomjs', 'headless-chrome',
            'automation', 'test-framework', 'robot', 'script',
            'crawler-commons', 'spider', 'bot-framework'
        ]
        
        # Suspicious header patterns
        self.suspicious_header_patterns = [
            'python', 'java', 'curl', 'wget', 'bot', 'crawler',
            'spider', 'scraper', 'test', 'automation', 'script'
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
        """Enhanced detection of suspicious headers that indicate automation"""
        suspicious = []
        headers = request.META
        
        # Check for automation-related headers
        for header_key, header_value in headers.items():
            if isinstance(header_value, str):
                header_value_lower = header_value.lower()
                for automation_indicator in self.automation_headers:
                    if automation_indicator in header_value_lower:
                        suspicious.append(f"{header_key}: {header_value}")
                
                # Check for suspicious patterns in any header
                for pattern in self.suspicious_header_patterns:
                    if pattern in header_value_lower:
                        suspicious.append(f"Suspicious pattern '{pattern}' in {header_key}")
        
        # Check for missing common browser headers (stronger indicator)
        required_headers = ['HTTP_ACCEPT', 'HTTP_ACCEPT_LANGUAGE', 'HTTP_ACCEPT_ENCODING', 'HTTP_USER_AGENT']
        missing_headers = [h for h in required_headers if h not in headers]
        if len(missing_headers) >= 2:  # More aggressive - 2 or more missing headers
            suspicious.append(f"Missing critical headers: {missing_headers}")
        
        # Check for unusual header combinations
        user_agent = headers.get('HTTP_USER_AGENT', '').lower()
        accept = headers.get('HTTP_ACCEPT', '').lower()
        
        # Bot-like header patterns
        if user_agent and not any(browser in user_agent for browser in self.legitimate_browsers):
            if not accept or '*/*' == accept.strip():
                suspicious.append("Non-browser user agent with generic accept header")
        
        # Check for programmatic request patterns
        if 'application/json' in accept and 'text/html' not in accept:
            suspicious.append("JSON-only accept header (API client pattern)")
        
        # Missing referer when it should be present (for non-root requests)
        if not headers.get('HTTP_REFERER') and request.path != '/':
            suspicious.append("Missing referer for non-root request")
        
        return suspicious
    
    def is_headless_browser(self, user_agent):
       
        user_agent_lower = user_agent.lower()
        headless_indicators = ['headless', 'phantomjs', 'htmlunit']
        return any(indicator in user_agent_lower for indicator in headless_indicators)
    
    def is_automation_tool(self, user_agent):
        """Enhanced detection of automation tools with more aggressive patterns"""
        if not user_agent:
            return True  # No user agent is highly suspicious
            
        user_agent_lower = user_agent.lower()
        
        # Check for explicit automation tool signatures
        for tool in self.suspicious_user_agents:
            if tool in user_agent_lower:
                return True
        
        # Enhanced patterns for sophisticated bots
        automation_patterns = [
            # Version patterns that indicate automation
            r'python/\d+\.\d+',  # python/3.9.1
            r'java/\d+\.\d+',    # java/11.0.1
            r'go-http-client',   # Go HTTP client
            r'node\.js',         # Node.js
            r'apache-httpclient',# Apache HTTP client
            r'okhttp',           # OkHttp client
            
            # Missing typical browser version patterns
            r'^[a-z]+-[a-z]+$',  # Simple tool names like 'http-client'
            
            # Suspicious version patterns
            r'\d+\.\d+\.\d+\.\d+',  # Too specific versions
        ]
        
        
        for pattern in automation_patterns:
            if re.search(pattern, user_agent_lower):
                return True
        
        # Check if it looks like a legitimate browser
        has_legitimate_browser = any(browser in user_agent_lower for browser in self.legitimate_browsers)
        
        if has_legitimate_browser:
            # Even with legitimate browser names, check for automation indicators
            automation_keywords = [
                'headless', 'selenium', 'webdriver', 'phantomjs', 
                'automation', 'test', 'robot', 'script',
                'crawler', 'spider', 'bot', 'scraper'
            ]
            
            # More aggressive detection - any automation keyword is suspicious
            for keyword in automation_keywords:
                if keyword in user_agent_lower:
                    return True
            
            # Check for malformed or unusual browser strings
            if 'mozilla' in user_agent_lower:
                # Real browsers have complex Mozilla strings
                if user_agent_lower.count('/') < 3:  # Too simple for real browser
                    return True
                if 'gecko' not in user_agent_lower and 'webkit' not in user_agent_lower:
                    return True  # Missing typical browser engine
        else:
            # No legitimate browser indicators - likely automation
            return True
        
        # Additional checks for sophisticated evasion
        suspicious_indicators = [
            len(user_agent) < 20,  # Too short for real browser
            len(user_agent) > 500,  # Unusually long (some bots add lots of info)
            user_agent.count(' ') < 3,  # Real browsers have multiple spaces
            not any(char.isdigit() for char in user_agent),  # No version numbers
        ]
        
        # If multiple suspicious indicators, flag as automation
        if sum(suspicious_indicators) >= 2:
            return True
            
        return False
    
    def generate_request_fingerprint(self, request):
        """Generate unique fingerprint for the request"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept = request.META.get('HTTP_ACCEPT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        fingerprint_string = f"{user_agent}|{accept}|{accept_language}|{accept_encoding}"
        return hashlib.md5(fingerprint_string.encode()).hexdigest()
    
    def extract_features_for_ml(self, request_data):
        """Extract comprehensive features for enhanced bot detection"""
        try:
            user_agent = request_data.get('user_agent', '')
            suspicious_headers = request_data.get('suspicious_headers', [])
            request_interval = request_data.get('request_interval', 0) or 0
            
            features = {
                'request_interval': request_interval,
                'user_agent_length': len(user_agent),
                'has_cookies': 1 if request_data.get('cookies_present') else 0,
                'suspicious_headers_count': len(suspicious_headers),
                'is_headless': 1 if request_data.get('is_headless_browser') else 0,
                'is_automation': 1 if request_data.get('automation_detected') else 0,
                'hour_of_day': datetime.now().hour,
                'is_weekend': 1 if datetime.now().weekday() >= 5 else 0,
                
                # NEW ENHANCED FEATURES
                'user_agent_has_version': 1 if any(char.isdigit() for char in user_agent) else 0,
                'user_agent_word_count': len(user_agent.split()) if user_agent else 0,
                'user_agent_has_mozilla': 1 if 'mozilla' in user_agent.lower() else 0,
                'user_agent_has_webkit': 1 if 'webkit' in user_agent.lower() else 0,
                'user_agent_suspicious_ratio': self._calculate_suspicious_ratio(user_agent),
                'has_multiple_suspicious_headers': 1 if len(suspicious_headers) > 1 else 0,
                'has_critical_suspicious_headers': 1 if len(suspicious_headers) > 3 else 0,
                'request_too_fast': 1 if 0 < request_interval < 0.5 else 0,
                'request_very_fast': 1 if 0 < request_interval < 0.3 else 0,
                'request_rhythmic': 1 if self._is_rhythmic_interval(request_interval) else 0,
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting enhanced features: {e}")
            return {}
    
    def _calculate_suspicious_ratio(self, user_agent):
        """Calculate ratio of suspicious words in user agent"""
        if not user_agent:
            return 1.0  # Empty user agent is highly suspicious
        
        words = user_agent.lower().split()
        if not words:
            return 1.0
        
        suspicious_words = [
            'python', 'java', 'curl', 'wget', 'bot', 'crawler', 'spider',
            'scraper', 'test', 'automation', 'script', 'tool', 'client',
            'requests', 'http', 'api', 'fetch', 'node'
        ]
        
        suspicious_count = sum(1 for word in words if any(susp in word for susp in suspicious_words))
        return suspicious_count / len(words)
    
    def _is_rhythmic_interval(self, interval):
        """Check if request interval follows rhythmic pattern (automation signature)"""
        if not interval or interval <= 0:
            return False
        
        # Check if interval is close to common automation rhythms
        common_rhythms = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        return any(abs(interval - rhythm) < 0.05 for rhythm in common_rhythms)
    
    def predict_bot_probability(self, features):
        """BALANCED bot detection - accurate detection while protecting legitimate users"""
        try:
            # BALANCED scoring for bot probability
            rule_based_score = 0.0
            bot_indicators = 0
            critical_indicators = 0
            legitimate_browser_indicators = 0
            
            # Check for LEGITIMATE BROWSER indicators first
            user_agent_length = features.get('user_agent_length', 0)
            has_mozilla = features.get('user_agent_has_mozilla', 0)
            has_webkit = features.get('user_agent_has_webkit', 0)
            has_version = features.get('user_agent_has_version', 0)
            word_count = features.get('user_agent_word_count', 0)
            
            # Identify legitimate browsers
            if has_mozilla and has_webkit and has_version and word_count >= 5:
                legitimate_browser_indicators += 3  # Strong browser signature
            elif (has_mozilla or has_webkit) and has_version and word_count >= 4:
                legitimate_browser_indicators += 2  # Moderate browser signature
            elif has_version and word_count >= 3:
                legitimate_browser_indicators += 1  # Basic browser signature
            
            # If it looks like a legitimate browser, be MUCH more conservative
            is_likely_legitimate_browser = legitimate_browser_indicators >= 2
            
            # CRITICAL indicators of automation (very high weight)
            if features.get('is_automation', 0):
                if is_likely_legitimate_browser:
                    rule_based_score += 0.4  # Reduced penalty for browser-like UAs
                else:
                    rule_based_score += 0.7  # Full penalty for non-browser UAs
                critical_indicators += 1
                bot_indicators += 1
            
            if features.get('is_headless', 0):
                rule_based_score += 0.6  # Always suspicious
                critical_indicators += 1
                bot_indicators += 1
            
            # SUSPICIOUS HEADERS - more nuanced
            suspicious_count = features.get('suspicious_headers_count', 0)
            if suspicious_count > 2 and not is_likely_legitimate_browser:
                rule_based_score += 0.4
                bot_indicators += 1
            elif suspicious_count > 4:  # Only flag browsers with many suspicious headers
                rule_based_score += 0.3
                bot_indicators += 1
            elif suspicious_count > 0 and not is_likely_legitimate_browser:
                rule_based_score += 0.2  # Mild penalty for non-browsers
            
            # REQUEST TIMING - more reasonable thresholds
            request_interval = features.get('request_interval', 0)
            if request_interval < 0.2 and request_interval > 0:  # Very rapid (< 200ms)
                rule_based_score += 0.4
                bot_indicators += 1
            elif request_interval < 0.5 and request_interval > 0:  # Fast (< 500ms)
                if not is_likely_legitimate_browser:
                    rule_based_score += 0.3  # Only penalize non-browsers
                    bot_indicators += 1
            
            # MISSING COOKIES - less aggressive for browsers
            if not features.get('has_cookies', 0):
                if is_likely_legitimate_browser:
                    rule_based_score += 0.05  # Very mild penalty for browsers
                else:
                    rule_based_score += 0.2  # Higher penalty for non-browsers
                    bot_indicators += 1
            
            # USER AGENT ANALYSIS - more nuanced
            if user_agent_length == 0:  # Empty user agent
                rule_based_score += 0.5
                bot_indicators += 1
            elif user_agent_length < 15 and not is_likely_legitimate_browser:  # Very short non-browser UA
                rule_based_score += 0.3
                bot_indicators += 1
            elif user_agent_length > 500:  # Unusually long
                rule_based_score += 0.2
                bot_indicators += 1
            
            # TIMING PATTERNS - only penalize if clearly non-browser
            hour = features.get('hour_of_day', 12)
            if (hour < 3 or hour > 23) and not is_likely_legitimate_browser:
                rule_based_score += 0.1  # Mild penalty for unusual hours
                bot_indicators += 1
            
            # WEEKEND ACTIVITY - only suspicious for non-browsers
            if features.get('is_weekend', 0) and not is_likely_legitimate_browser:
                rule_based_score += 0.05
            
            # ENHANCED FEATURE ANALYSIS - only for non-browsers
            if not is_likely_legitimate_browser:
                # Missing version info for non-browsers
                if not features.get('user_agent_has_version', 0):
                    rule_based_score += 0.2
                    bot_indicators += 1
                
                # Missing browser engines for non-browsers
                if not has_mozilla and not has_webkit:
                    rule_based_score += 0.3
                    bot_indicators += 1
                
                # Too few words in user agent for non-browsers
                if word_count < 2:
                    rule_based_score += 0.25
                    bot_indicators += 1
                
                # High suspicious word ratio for non-browsers
                suspicious_ratio = features.get('user_agent_suspicious_ratio', 0)
                if suspicious_ratio > 0.5:  # 50% or more suspicious words
                    rule_based_score += 0.4
                    bot_indicators += 1
                elif suspicious_ratio > 0.3:  # 30% or more suspicious words
                    rule_based_score += 0.2
                    bot_indicators += 1
            
            # ENHANCED TIMING AND HEADER ANALYSIS
            if features.get('has_critical_suspicious_headers', 0):
                rule_based_score += 0.4
                critical_indicators += 1
                bot_indicators += 1
            
            if features.get('request_very_fast', 0):  # < 300ms
                rule_based_score += 0.4
                bot_indicators += 1
            
            if features.get('request_rhythmic', 0) and not is_likely_legitimate_browser:
                rule_based_score += 0.3
                bot_indicators += 1
            
            # PROTECTIVE LOGIC FOR LEGITIMATE BROWSERS
            if is_likely_legitimate_browser:
                # Significantly reduce score for legitimate browsers
                rule_based_score *= 0.6  # 40% reduction
                
                # Require multiple strong indicators for legitimate browsers
                if bot_indicators < 2 and critical_indicators == 0:
                    rule_based_score = min(rule_based_score, 0.2)  # Cap at 20%
                elif critical_indicators == 0:
                    rule_based_score = min(rule_based_score, 0.4)  # Cap at 40% without critical indicators
            
            # ENHANCED SCORING LOGIC - more balanced
            if critical_indicators >= 1:
                rule_based_score = max(rule_based_score, 0.5)  # Minimum 50% if critical indicator present
            elif bot_indicators >= 3 and not is_likely_legitimate_browser:
                rule_based_score = max(rule_based_score, 0.4)  # Minimum 40% for multiple indicators (non-browsers)
            elif bot_indicators >= 2 and not is_likely_legitimate_browser:
                rule_based_score = max(rule_based_score, 0.3)  # Minimum 30% for some indicators (non-browsers)
            
            # Cap the final score
            final_score = min(rule_based_score, 1.0)
            
            # Enhanced logging for debugging
            if final_score > 0.3 or is_likely_legitimate_browser:
                logger.info(f"Bot detection: Score={final_score:.3f}, Indicators={bot_indicators}, "
                           f"Critical={critical_indicators}, Legitimate_browser={is_likely_legitimate_browser}, "
                           f"Browser_indicators={legitimate_browser_indicators}")
            
            return final_score
        
        except Exception as e:
            logger.error(f"Error in balanced bot prediction: {e}")
            return 0.1  # Low default for errors

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
        
        # Determine final classification - BALANCED approach that protects legitimate users
        confidence = abs(bot_probability - 0.5) * 2  # Scale to 0-1
        is_bot = bot_probability > 0.55  # Increased from 0.35 to 0.55 - more balanced threshold
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
        
        # Return response based on detection result - BALANCED blocking threshold
        if is_bot and confidence > 0.7:  # Increased from 0.5 to 0.7 - only block high confidence bots
            return JsonResponse({
                'status': 'blocked',
                'message': 'Automated HTTP client detected. Access denied.',
                'detection_id': detection_record.id,
                'classification': classification,
                'confidence': round(confidence * 100, 2),
                'bot_probability': round(bot_probability * 100, 2),
                'reason': 'High probability of automated HTTP client',
                'detected_indicators': {
                    'automation_tool': is_automation,
                    'headless_browser': is_headless,
                    'suspicious_headers': len(suspicious_headers) > 0,
                    'suspicious_headers_count': len(suspicious_headers),
                    'rate_limit_exceeded': rate_limit_exceeded,
                    'fast_requests': request_interval is not None and request_interval < 1.0,
                    'very_fast_requests': request_interval is not None and request_interval < 0.3,
                    'missing_cookies': not cookies_present,
                    'user_agent_suspicious': is_automation or is_headless
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
