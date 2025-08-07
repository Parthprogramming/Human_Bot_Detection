import json
import time
import hashlib
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.core.cache import cache
from django.db import models
from .models import HttpBotDetection
import os,re

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def init_session(request):
    return JsonResponse({"message": "Session initialized"})

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
    
    def detect_suspicious_headers(self, request, collected_headers=None):
        """Enhanced detection of suspicious headers using collected header data"""
        suspicious = []
        headers = request.META
        
        if collected_headers:
            header_patterns = {
                'User-Agent': ['python', 'java', 'curl', 'wget', 'bot', 'crawler', 'spider', 'scraper'],
                'Accept': ['*/*'],  
                'Connection': ['close'],  
                'Cache-Control': ['no-cache'], 
            }
            
            for header_name, header_value in collected_headers.items():
                if header_value:  
                    header_value_lower = header_value.lower()
                    
                    
                    if header_name in header_patterns:
                        for pattern in header_patterns[header_name]:
                            if pattern in header_value_lower:
                                suspicious.append(f"Suspicious {header_name}: contains '{pattern}'")
            
            critical_browser_headers = ['Accept', 'Accept-Language', 'Accept-Encoding', 'User-Agent']
            missing_critical = [h for h in critical_browser_headers if not collected_headers.get(h)]
            if len(missing_critical) >= 2:
                suspicious.append(f"Missing critical browser headers: {missing_critical}")
            
            security_headers = ['Sec-Fetch-Site', 'Sec-Fetch-Mode', 'Sec-Fetch-Dest']
            missing_security = [h for h in security_headers if not collected_headers.get(h)]
            if len(missing_security) == len(security_headers):
                suspicious.append("Missing all Sec-Fetch headers (old browser or bot)")
            
            user_agent = collected_headers.get('User-Agent', '').lower()
            accept = collected_headers.get('Accept', '').lower()
            
            if user_agent and not any(browser in user_agent for browser in self.legitimate_browsers):
                if not accept or accept == '*/*':
                    suspicious.append("Non-browser user agent with generic accept header")
            
            if 'application/json' in accept and 'text/html' not in accept:
                suspicious.append("JSON-only accept header (API client pattern)")
                
        for header_key, header_value in headers.items():
            if isinstance(header_value, str):
                header_value_lower = header_value.lower()
                for automation_indicator in self.automation_headers:
                    if automation_indicator in header_value_lower:
                        suspicious.append(f"{header_key}: {header_value}")
                
                for pattern in self.suspicious_header_patterns:
                    if pattern in header_value_lower:
                        suspicious.append(f"Suspicious pattern '{pattern}' in {header_key}")
        
        referer = collected_headers.get('Referer', '') if collected_headers else headers.get('HTTP_REFERER', '')
        if not referer and request.path != '/':
            suspicious.append("Missing referer for non-root request")
        
        return suspicious
    
    def detect_spoofed_user_agent(self, collected_headers):
        """Detect bots that spoof User-Agent but miss modern browser headers"""
        if not collected_headers:
            return []
        
        suspicious = []
        user_agent = collected_headers.get('User-Agent', '').lower()
        
        # Only check if there's a User-Agent that claims to be a modern browser
        if not user_agent:
            return suspicious
        
        # Check if User-Agent claims to be a modern browser
        modern_browsers = {
            'chrome': {'min_version': 80, 'pattern': r'chrome/(\d+)'},
            'firefox': {'min_version': 75, 'pattern': r'firefox/(\d+)'},
            'safari': {'min_version': 13, 'pattern': r'safari/(\d+)'},
            'edge': {'min_version': 80, 'pattern': r'edg/(\d+)'}
        }
        
        claimed_browser = None
        claimed_version = None
        
        import re
        for browser, info in modern_browsers.items():
            if browser in user_agent:
                match = re.search(info['pattern'], user_agent)
                if match:
                    claimed_version = int(match.group(1))
                    if claimed_version >= info['min_version']:
                        claimed_browser = browser
                        break
        
        if not claimed_browser:
            return suspicious
        

        sec_fetch_headers = ['Sec-Fetch-Site', 'Sec-Fetch-Mode', 'Sec-Fetch-Dest']
        missing_sec_fetch = [h for h in sec_fetch_headers if not collected_headers.get(h)]
        
        sec_ch_ua_headers = ['Sec-CH-UA', 'Sec-CH-UA-Platform', 'Sec-CH-UA-Mobile']
        missing_sec_ch_ua = [h for h in sec_ch_ua_headers if not collected_headers.get(h)]
        
        if len(missing_sec_fetch) == len(sec_fetch_headers):
            suspicious.append(f"SPOOFED UA: {claimed_browser.title()} v{claimed_version} missing ALL Sec-Fetch headers")
        
        if claimed_browser in ['chrome', 'edge'] and claimed_version >= 89:
            if len(missing_sec_ch_ua) == len(sec_ch_ua_headers):
                suspicious.append(f"SPOOFED UA: {claimed_browser.title()} v{claimed_version} missing ALL Sec-CH-UA headers")
        
        accept = collected_headers.get('Accept', '')
        accept_language = collected_headers.get('Accept-Language', '')
        accept_encoding = collected_headers.get('Accept-Encoding', '')
        
        if claimed_browser and accept == '*/*':
            suspicious.append(f"SPOOFED UA: {claimed_browser.title()} with generic Accept header")
        
        if claimed_browser and not accept_language:
            suspicious.append(f"SPOOFED UA: {claimed_browser.title()} missing Accept-Language")
        
        if claimed_browser and not accept_encoding:
            suspicious.append(f"SPOOFED UA: {claimed_browser.title()} missing Accept-Encoding")
        
        total_headers = len([h for h in collected_headers.values() if h])
        if claimed_browser and total_headers < 8:
            suspicious.append(f"SPOOFED UA: {claimed_browser.title()} with minimal headers ({total_headers} headers)")
        
        return suspicious
    
    def is_headless_browser(self, user_agent):
       
        user_agent_lower = user_agent.lower()
        headless_indicators = ['headless', 'phantomjs', 'htmlunit']
        return any(indicator in user_agent_lower for indicator in headless_indicators)
    
    def is_automation_tool(self, user_agent):
        """HUMAN-FRIENDLY detection of automation tools - protects legitimate browsers"""
        if not user_agent:
            return True  
        user_agent_lower = user_agent.lower()
        
        
        legitimate_browser_indicators = ['mozilla', 'chrome', 'firefox', 'safari', 'edge', 'opera']
        has_browser_signature = any(browser in user_agent_lower for browser in legitimate_browser_indicators)
        
        if has_browser_signature:
            clear_automation_indicators = [
                'selenium', 'webdriver', 'phantomjs', 'headless',
                'automation', 'test', 'robot', 'script'
            ]
            
            for indicator in clear_automation_indicators:
                if indicator in user_agent_lower:
                    logger.info(f"Browser with automation indicator detected: {indicator}")
                    return True
            
            return False
        
        for tool in self.suspicious_user_agents:
            if tool in user_agent_lower:
                return True
        
        automation_patterns = [
            r'python/\d+\.\d+',  
            r'java/\d+\.\d+',    
            r'go-http-client',   
            r'node\.js',         
            r'apache-httpclient',
            r'okhttp',           
            r'^[a-z]+-[a-z]+$',  
        ]
        
        for pattern in automation_patterns:
            if re.search(pattern, user_agent_lower):
                return True
        
        suspicious_indicators = [
            len(user_agent) < 15,  
            len(user_agent) > 400, 
            user_agent.count(' ') < 2,  
            not any(char.isdigit() for char in user_agent),  
        ]
        
        if sum(suspicious_indicators) >= 3:  
            return True
            
        return False
    
    def extract_request_headers(self, request):
        """Extract specific headers for analysis and storage"""
        target_headers = [
            'HOST', 'CONNECTION', 'CACHE_CONTROL', 'UPGRADE_INSECURE_REQUESTS',
            'USER_AGENT', 'ACCEPT', 'SEC_FETCH_SITE', 'SEC_FETCH_MODE', 
            'SEC_FETCH_USER', 'SEC_FETCH_DEST', 'SEC_CH_UA', 'SEC_CH_UA_PLATFORM',
            'SEC_CH_UA_MOBILE', 'ACCEPT_ENCODING', 'ACCEPT_LANGUAGE', 'COOKIE'
        ]
        
        collected_headers = {}
        
        header_mapping = {
            'HTTP_HOST': 'Host',
            'HTTP_CONNECTION': 'Connection',
            'HTTP_CACHE_CONTROL': 'Cache-Control',
            'HTTP_UPGRADE_INSECURE_REQUESTS': 'Upgrade-Insecure-Requests',
            'HTTP_USER_AGENT': 'User-Agent',
            'HTTP_ACCEPT': 'Accept',
            'HTTP_SEC_FETCH_SITE': 'Sec-Fetch-Site',
            'HTTP_SEC_FETCH_MODE': 'Sec-Fetch-Mode',
            'HTTP_SEC_FETCH_USER': 'Sec-Fetch-User',
            'HTTP_SEC_FETCH_DEST': 'Sec-Fetch-Dest',
            'HTTP_SEC_CH_UA': 'Sec-CH-UA',
            'HTTP_SEC_CH_UA_PLATFORM': 'Sec-CH-UA-Platform',
            'HTTP_SEC_CH_UA_MOBILE': 'Sec-CH-UA-Mobile',
            'HTTP_ACCEPT_ENCODING': 'Accept-Encoding',
            'HTTP_ACCEPT_LANGUAGE': 'Accept-Language',
            'HTTP_COOKIE': 'Cookie'
        }
        
        for meta_key, header_name in header_mapping.items():
            header_value = request.META.get(meta_key, '')
            collected_headers[header_name] = header_value
        
        additional_headers = {
            'HTTP_REFERER': 'Referer',
            'HTTP_X_FORWARDED_FOR': 'X-Forwarded-For',
            'HTTP_X_REAL_IP': 'X-Real-IP',
            'HTTP_ORIGIN': 'Origin',
            'HTTP_DNT': 'DNT',
            'HTTP_X_REQUESTED_WITH': 'X-Requested-With'
        }
        
        for meta_key, header_name in additional_headers.items():
            if meta_key in request.META:
                collected_headers[header_name] = request.META[meta_key]
        
        header_analysis = {
            'total_headers': len([h for h in collected_headers.values() if h]),
            'missing_headers': [name for name, value in collected_headers.items() if not value],
            'has_sec_fetch_headers': any(name.startswith('Sec-Fetch-') for name, value in collected_headers.items() if value),
            'has_sec_ch_headers': any(name.startswith('Sec-CH-') for name, value in collected_headers.items() if value),
            'cookie_count': len(request.COOKIES) if request.COOKIES else 0
        }
        
        return {
            'headers': collected_headers,
            'analysis': header_analysis
        }

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
            spoofed_ua_indicators = request_data.get('spoofed_ua_indicators', [])  
            request_interval = request_data.get('request_interval', 0) or 0
            
            features = {
                'request_interval': request_interval,
                'user_agent_length': len(user_agent),
                'has_cookies': 1 if request_data.get('cookies_present') else 0,
                'has_session_cookie': 1 if request_data.get('has_session_cookie') else 0,  
                'has_csrf_cookie': 1 if request_data.get('has_csrf_cookie') else 0,  
                'has_legitimate_cookies': 1 if (request_data.get('has_session_cookie') or request_data.get('has_csrf_cookie')) else 0,  
                'has_client_tokens': 1 if request_data.get('has_client_tokens') else 0, 
                'suspicious_headers_count': len(suspicious_headers),
                'spoofed_ua_count': len(spoofed_ua_indicators),  
                'has_spoofed_ua': 1 if spoofed_ua_indicators else 0,  
                'is_headless': 1 if request_data.get('is_headless_browser') else 0,
                'is_automation': 1 if request_data.get('automation_detected') else 0,
                'hour_of_day': datetime.now().hour,
                'is_weekend': 1 if datetime.now().weekday() >= 5 else 0,
                
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
            return 1.0  
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
        
        common_rhythms = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        return any(abs(interval - rhythm) < 0.05 for rhythm in common_rhythms)
    
    def predict_bot_probability(self, features):
        """HUMAN-FRIENDLY bot detection - protects legitimate users while catching real bots"""
        try:
            rule_based_score = 0.0
            bot_indicators = 0
            critical_indicators = 0
            legitimate_browser_indicators = 0
            
            user_agent_length = features.get('user_agent_length', 0)
            has_mozilla = features.get('user_agent_has_mozilla', 0)
            has_webkit = features.get('user_agent_has_webkit', 0)
            has_version = features.get('user_agent_has_version', 0)
            word_count = features.get('user_agent_word_count', 0)
            
            if has_mozilla or has_webkit: 
                legitimate_browser_indicators += 2
            if has_version:
                legitimate_browser_indicators += 1
            if word_count >= 3: 
                legitimate_browser_indicators += 1
            if user_agent_length > 50:  
                legitimate_browser_indicators += 1
            
            is_likely_legitimate_browser = legitimate_browser_indicators >= 2
            
            if is_likely_legitimate_browser:
                logger.info(f"Detected legitimate browser - applying protection. Indicators: {legitimate_browser_indicators}")
            
            if features.get('is_automation', 0) and not is_likely_legitimate_browser:
                rule_based_score += 0.6  
                critical_indicators += 1
                bot_indicators += 1
            elif features.get('is_automation', 0) and is_likely_legitimate_browser:
                rule_based_score += 0.2  # Very mild penalty
            
            spoofed_ua_count = features.get('spoofed_ua_count', 0)
            has_spoofed_ua = features.get('has_spoofed_ua', 0)
            
            if has_spoofed_ua:
                spoofed_penalty = min(spoofed_ua_count * 0.25, 0.8)  
                rule_based_score += spoofed_penalty
                critical_indicators += 1
                bot_indicators += 1
                logger.info(f"SPOOFED USER-AGENT DETECTED: {spoofed_ua_count} indicators, penalty: {spoofed_penalty}")
            
            if features.get('is_headless', 0):
                if is_likely_legitimate_browser:
                    rule_based_score += 0.3  
                else:
                    rule_based_score += 0.6  
                critical_indicators += 1
                bot_indicators += 1
            
            suspicious_count = features.get('suspicious_headers_count', 0)
            if is_likely_legitimate_browser:
                if suspicious_count > 5:  # Very high threshold for browsers
                    rule_based_score += 0.2  # Mild penalty
                    bot_indicators += 1
            else:
                # For non-browsers, be more strict but still reasonable
                if suspicious_count > 2:
                    rule_based_score += 0.4
                    bot_indicators += 1
                elif suspicious_count > 0:
                    rule_based_score += 0.1  # Very mild penalty
            
            # REQUEST TIMING - much more lenient
            request_interval = features.get('request_interval', 0)
            if request_interval < 0.1 and request_interval > 0:  # Only extremely rapid (< 100ms)
                if is_likely_legitimate_browser:
                    rule_based_score += 0.1  # Very mild penalty for browsers
                else:
                    rule_based_score += 0.3  # Moderate penalty for non-browsers
                bot_indicators += 1
            elif request_interval < 0.2 and request_interval > 0:  # Very fast (< 200ms)
                if not is_likely_legitimate_browser:
                    rule_based_score += 0.2  # Only penalize non-browsers
                    bot_indicators += 1
            
            # ENHANCED TOKEN ANALYSIS - Client-generated tokens are strongest legitimacy indicator
            has_any_cookies = features.get('has_cookies', 0)
            has_session = features.get('has_session_cookie', 0)
            has_csrf = features.get('has_csrf_cookie', 0)
            has_legitimate = features.get('has_legitimate_cookies', 0)
            has_client_tokens = features.get('has_client_tokens', 0)  # NEW: Client-generated tokens
            
            # STRONGEST LEGITIMACY: Client-generated tokens (frontend flow)
            if has_client_tokens:
                # Major legitimacy bonus for client-generated tokens
                rule_based_score -= 0.4  # Strong reduction in bot score
                logger.info("Client-generated tokens detected - strong legitimacy indicator")
                
                # Additional protection for users with client tokens
                if is_likely_legitimate_browser:
                    rule_based_score -= 0.2  # Extra bonus for legitimate browsers with client tokens
                    logger.info("Legitimate browser with client tokens - maximum protection")
            
            elif not has_any_cookies:
                # No cookies at all - very suspicious
                if is_likely_legitimate_browser:
                    rule_based_score += 0.4  # High penalty for browsers without any cookies
                    bot_indicators += 1
                    logger.info("Browser with NO cookies detected - high suspicion")
                else:
                    rule_based_score += 0.6  # Very high penalty for non-browsers without cookies
                    bot_indicators += 1
                    logger.info("Non-browser with NO cookies detected - very high suspicion")
            elif not has_legitimate:
                if is_likely_legitimate_browser:
                    rule_based_score += 0.2  # Moderate penalty for browsers without legitimate cookies
                    bot_indicators += 1
                    logger.info("Browser with cookies but no session/CSRF - moderate suspicion")
                else:
                    rule_based_score += 0.4  # High penalty for non-browsers without legitimate cookies
                    bot_indicators += 1
                    logger.info("Non-browser with cookies but no session/CSRF - high suspicion")
            elif has_session and has_csrf:
                if is_likely_legitimate_browser:
                    rule_based_score -= 0.1  # Small bonus for legitimate browser with proper cookies
                    logger.info("Legitimate browser with proper session/CSRF cookies - reduced suspicion")
                # Don't penalize non-browsers that somehow have legitimate cookies
            
            # USER AGENT ANALYSIS - more forgiving
            if user_agent_length == 0:  # Empty user agent
                rule_based_score += 0.5
                bot_indicators += 1
            elif user_agent_length < 10 and not is_likely_legitimate_browser:  # Very short non-browser UA
                rule_based_score += 0.3
                bot_indicators += 1
            elif user_agent_length > 600:  # Extremely long (browsers can be long but not this long)
                rule_based_score += 0.1  # Mild penalty
                bot_indicators += 1
            
            # TIMING PATTERNS - only penalize clear non-browsers
            hour = features.get('hour_of_day', 12)
            if (hour < 2 or hour > 24) and not is_likely_legitimate_browser:
                rule_based_score += 0.05  # Very mild penalty
            
            # WEEKEND ACTIVITY - remove this penalty entirely for browsers
            if features.get('is_weekend', 0) and not is_likely_legitimate_browser:
                rule_based_score += 0.02  # Almost no penalty
            
            # ENHANCED FEATURE ANALYSIS - only for clear non-browsers
            if not is_likely_legitimate_browser:
                # Missing version info for non-browsers
                if not features.get('user_agent_has_version', 0):
                    rule_based_score += 0.15  # Reduced penalty
                    bot_indicators += 1
                
                # Missing browser engines for non-browsers
                if not has_mozilla and not has_webkit:
                    rule_based_score += 0.25  # Reduced penalty
                    bot_indicators += 1
                
                # Too few words in user agent for non-browsers
                if word_count < 2:
                    rule_based_score += 0.2  # Reduced penalty
                    bot_indicators += 1
                
                # High suspicious word ratio for non-browsers
                suspicious_ratio = features.get('user_agent_suspicious_ratio', 0)
                if suspicious_ratio > 0.7:  # Raised threshold to 70%
                    rule_based_score += 0.3  # Reduced penalty
                    bot_indicators += 1
                elif suspicious_ratio > 0.5:  # 50% or more suspicious words
                    rule_based_score += 0.15  # Reduced penalty
            
            # ENHANCED TIMING AND HEADER ANALYSIS - more lenient
            if features.get('has_critical_suspicious_headers', 0):
                if is_likely_legitimate_browser:
                    rule_based_score += 0.2  # Reduced penalty for browsers
                else:
                    rule_based_score += 0.4
                critical_indicators += 1
                bot_indicators += 1
            
            if features.get('request_very_fast', 0):  # < 300ms
                if is_likely_legitimate_browser:
                    rule_based_score += 0.1  # Reduced penalty for browsers
                else:
                    rule_based_score += 0.3
                bot_indicators += 1
            
            if features.get('request_rhythmic', 0) and not is_likely_legitimate_browser:
                rule_based_score += 0.2  # Reduced penalty
                bot_indicators += 1
            
            # STRONG PROTECTION FOR LEGITIMATE BROWSERS
            if is_likely_legitimate_browser:
                # Dramatically reduce score for legitimate browsers
                rule_based_score *= 0.3  # 70% reduction (was 40%)
                
                # Very strict requirements for flagging browsers as bots
                if critical_indicators == 0:
                    rule_based_score = min(rule_based_score, 0.15)  # Cap at 15% without critical indicators
                elif critical_indicators == 1 and bot_indicators < 3:
                    rule_based_score = min(rule_based_score, 0.3)  # Cap at 30% with 1 critical indicator
                
                logger.info(f"Browser protection applied: score reduced to {rule_based_score:.3f}")
            
            # MUCH MORE CONSERVATIVE SCORING LOGIC
            if critical_indicators >= 2:  # Need 2+ critical indicators
                rule_based_score = max(rule_based_score, 0.6)  # Minimum 60%
            elif critical_indicators >= 1 and bot_indicators >= 3:  # 1 critical + 3 other indicators
                rule_based_score = max(rule_based_score, 0.5)  # Minimum 50%
            elif bot_indicators >= 5 and not is_likely_legitimate_browser:  # Many indicators for non-browsers
                rule_based_score = max(rule_based_score, 0.4)  # Minimum 40%
            
            # Cap the final score
            final_score = min(rule_based_score, 1.0)
            
            # Enhanced logging for debugging
            logger.info(f"Bot detection: Score={final_score:.3f}, Indicators={bot_indicators}, "
                       f"Critical={critical_indicators}, Legitimate_browser={is_likely_legitimate_browser}, "
                       f"Browser_indicators={legitimate_browser_indicators}, UA_length={user_agent_length}")
            
            return final_score
        
        except Exception as e:
            logger.error(f"Error in human-friendly bot prediction: {e}")
            return 0.05  # Very low default for errors

detector = HttpBotDetector()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def detect_http_bot(request):
    """Main endpoint for HTTP bot detection with USAI ID verification"""
    try:
        # Extract request information
        ip_address = detector.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        endpoint = request.path
        method = request.method
        timestamp = timezone.now()
        
        # Extract USAI ID from request
        usai_id = None
        browser_info = None
        
        if method == 'POST' and request.content_type == 'application/json':
            try:
                request_body = json.loads(request.body)
                usai_id = request_body.get('usai_id', '')
                browser_info = request_body.get('browser_info', {})
            except json.JSONDecodeError:
                usai_id = ''
                browser_info = {}
        
        # Also check headers for USAI ID
        if not usai_id:
            usai_id = request.META.get('HTTP_X_USAI_ID', '')
        
        # Extract comprehensive header information
        header_data = detector.extract_request_headers(request)
        collected_headers = header_data['headers']
        header_analysis = header_data['analysis']
        
        # Calculate request interval
        request_interval = detector.calculate_request_interval(ip_address)
        
        # ENHANCED: Extract session ID and CSRF token from multiple sources
        # Priority: 1) Request body (client-generated), 2) Headers, 3) Cookies
        
        # Extract from request body (client-side generated tokens)
        client_session_id = ''
        client_csrf_token = ''
        
        if method == 'POST' and request.content_type == 'application/json':
            try:
                request_body = json.loads(request.body)
                client_session_id = request_body.get('session_id', '') or request_body.get('sessionId', '')
                client_csrf_token = request_body.get('csrf_token', '') or request_body.get('csrfToken', '')
            except json.JSONDecodeError:
                pass
        
        # Extract from headers (alternative client-side method)
        header_session_id = request.META.get('HTTP_X_SESSION_ID', '')
        header_csrf_token = request.META.get('HTTP_X_CSRF_TOKEN', '')
        
        # DEBUGGING: Check all possible CSRF header names
        csrf_header_alternatives = [
            'HTTP_X_CSRF_TOKEN', 'HTTP_X_CSRFTOKEN', 'HTTP_CSRF_TOKEN', 
            'HTTP_CSRFTOKEN', 'HTTP_X_CSRF', 'HTTP_CSRF'
        ]
        csrf_header_debug = {}
        for header_name in csrf_header_alternatives:
            csrf_header_debug[header_name] = request.META.get(header_name, "")
        
        # Also try Django's standard CSRF header
        standard_csrf_header = request.META.get('HTTP_X_CSRFTOKEN', '')
        if standard_csrf_header:
            header_csrf_token = standard_csrf_header
        
        logger.info(f"CSRF HEADER DEBUG: {csrf_header_debug}")
        logger.info(f"Final header CSRF token: {'YES' if header_csrf_token else 'NO'}")
        
        # Extract from cookies (fallback)
        cookie_session_id = request.COOKIES.get("sessionid", "")
        cookie_csrf_token = request.COOKIES.get("csrftoken", "")
        
        # DEBUGGING: Check all possible CSRF cookie names
        csrf_alternatives = ["csrftoken", "csrf_token", "CSRF_TOKEN", "X-CSRFToken"]
        csrf_debug_info = {}
        for name in csrf_alternatives:
            csrf_debug_info[name] = request.COOKIES.get(name, "")
        
        # Also check Django's default CSRF cookie name from settings
        from django.conf import settings
        django_csrf_cookie_name = getattr(settings, 'CSRF_COOKIE_NAME', 'csrftoken')
        if django_csrf_cookie_name not in csrf_alternatives:
            csrf_debug_info[django_csrf_cookie_name] = request.COOKIES.get(django_csrf_cookie_name, "")
        
        # Use Django's configured CSRF cookie name
        cookie_csrf_token = request.COOKIES.get(django_csrf_cookie_name, "")
        
        # Log all cookies for debugging
        all_cookies = dict(request.COOKIES)
        logger.info(f"ALL COOKIES RECEIVED: {list(all_cookies.keys())}")
        logger.info(f"CSRF COOKIE DEBUG: {csrf_debug_info}")
        logger.info(f"Django CSRF cookie name: {django_csrf_cookie_name}")
        logger.info(f"CSRF token found: {'YES' if cookie_csrf_token else 'NO'}")
        if all_cookies:
            logger.info(f"All cookie values: {all_cookies}")

        # PRIORITY: Use client-generated tokens first, then headers, then cookies
        final_session_id = client_session_id or header_session_id or cookie_session_id
        final_csrf_token = client_csrf_token or header_csrf_token or cookie_csrf_token
        
        # Determine legitimacy based on presence of client-generated tokens
        cookies_present = bool(final_session_id or final_csrf_token)
        has_client_tokens = bool(client_session_id or client_csrf_token)
        
        cookies = dict(request.COOKIES) if request.COOKIES else {}  # Extract cookies as dictionary

        # Store the final tokens (prioritizing client-generated ones)
        cookie_data = {
            'sessionid': final_session_id,
            'csrftoken': final_csrf_token
        }
        
        # Enhanced logging for token source tracking
        total_cookies = len(cookies)
        logger.info(f"Token Analysis - IP: {ip_address}")
        logger.info(f"  Client tokens: Session={'present' if client_session_id else 'missing'}, CSRF={'present' if client_csrf_token else 'missing'}")
        logger.info(f"  Header tokens: Session={'present' if header_session_id else 'missing'}, CSRF={'present' if header_csrf_token else 'missing'}")
        logger.info(f"  Cookie tokens: Session={'present' if cookie_session_id else 'missing'}, CSRF={'present' if cookie_csrf_token else 'missing'}")
        logger.info(f"  Final tokens: Session={'present' if final_session_id else 'missing'}, CSRF={'present' if final_csrf_token else 'missing'}")
        logger.info(f"  Has client-generated tokens: {has_client_tokens}")
        
        if not final_session_id and not final_csrf_token:
            logger.info("No legitimate tokens found - likely bot")
        elif has_client_tokens:
            logger.info("Client-generated tokens detected - likely legitimate user")
        else:
            logger.info("Only cookie/header tokens found - possible bot or edge case")
        
        suspicious_headers = detector.detect_suspicious_headers(request, collected_headers)
        
        spoofed_ua_indicators = detector.detect_spoofed_user_agent(collected_headers)
        
        is_headless = detector.is_headless_browser(user_agent)
        is_automation = detector.is_automation_tool(user_agent)
        request_fingerprint = detector.generate_request_fingerprint(request)
        
        payload_schema_valid = True
        if method == 'POST':
            try:
                if request.content_type == 'application/json':
                    json.loads(request.body)
            except json.JSONDecodeError:
                payload_schema_valid = False
        
        rate_limit_key = f"rate_limit_{ip_address}"
        request_count = cache.get(rate_limit_key, 0)
        rate_limit_exceeded = request_count > 100  # More than 100 requests per hour
        cache.set(rate_limit_key, request_count + 1, timeout=3600)
        
        request_data = {
            'request_interval': request_interval,
            'user_agent': user_agent,
            'cookies_present': cookies_present,  
            'has_session_cookie': bool(final_session_id),  
            'has_csrf_cookie': bool(final_csrf_token),     
            'has_client_tokens': has_client_tokens,        
            'suspicious_headers': suspicious_headers,
            'spoofed_ua_indicators': spoofed_ua_indicators,
            'is_headless_browser': is_headless,
            'automation_detected': is_automation,
        }
        
        features = detector.extract_features_for_ml(request_data)
        
        has_spoofed_ua = features.get('has_spoofed_ua', 0)
        has_csrf = features.get('has_csrf_cookie', 0)
        has_client_tokens = features.get('has_client_tokens', 0)
        
        # Check if CSRF token is completely empty (no cookie, no header, no body)
        csrf_completely_empty = (
            not has_csrf and 
            not final_csrf_token and 
            not header_csrf_token and 
            not client_csrf_token
        )
        
        # Check if session ID is completely empty (no cookie, no header, no body)
        session_completely_empty = (
            not final_session_id and 
            not header_session_id and 
            not client_session_id and
            not cookie_session_id
        )
        

        if (csrf_completely_empty and session_completely_empty) or (has_spoofed_ua and csrf_completely_empty and not has_client_tokens):
            if csrf_completely_empty and session_completely_empty:
                logger.warning(f"DIRECT BOT DETECTION: No CSRF token AND No session ID - IP: {ip_address}")
            else:
                logger.warning(f"DIRECT BOT DETECTION: Spoofed User-Agent with completely empty CSRF token - IP: {ip_address}")
            is_bot = True
            classification = 'HTTP_Client_Bot'
            bot_probability = 0.95  
            confidence = 0.95
        else:
            bot_probability = detector.predict_bot_probability(features)
            
            bot_threshold = 0.70 
            is_bot = bot_probability >= bot_threshold
            classification = 'HTTP_Client_Bot' if is_bot else 'Human'
            
            if is_bot:
                confidence = min((bot_probability - bot_threshold) / (1.0 - bot_threshold), 1.0)
            else:
                confidence = min((bot_threshold - bot_probability) / bot_threshold, 1.0)
            
            confidence = max(0.0, min(1.0, confidence))

        session_id = final_session_id
        csrf_token = final_csrf_token
        
        if not session_id:
            logger.info("No session ID found - request has no legitimate session")
        
        if not csrf_token:
            logger.info("No CSRF token found - request has no legitimate CSRF token")
        
        
        logger.info(f"Cookie tracking - Session: {'present' if session_id else 'empty'}, CSRF: {'present' if csrf_token else 'empty'}")
        
        detection_record = HttpBotDetection.objects.create(
            ip_address=ip_address,
            timestamp=timestamp,
            user_agent=user_agent,
            headers=collected_headers,  # Store the collected headers
            endpoint=endpoint,
            method=method,
            request_interval=request_interval,
            payload_schema_valid=payload_schema_valid,
            cookies_present=cookies_present,
            cookies=cookie_data,  
            classification=classification,
            confidence=confidence,
            suspicious_headers=suspicious_headers,
            request_fingerprint=request_fingerprint,
            session_id=session_id,
            is_headless_browser=is_headless,
            automation_detected=is_automation,
            rate_limit_exceeded=rate_limit_exceeded
        )
        
        logger.info(f"HTTP Bot Detection - IP: {ip_address}, USAI: {usai_id}, Session: {session_id}, Prediction: {classification}, "
                   f"Confidence: {confidence:.2f}, Bot Probability: {bot_probability:.2f}")
        
        detection_analysis = {
            'usai_id': usai_id,
            'ip_address': ip_address,
            'timestamp': timestamp.isoformat(),
            'user_agent': user_agent,
            'headers': collected_headers,
            'header_analysis': header_analysis,
            'endpoint': endpoint,
            'method': method,
            'request_interval': request_interval,
            'payload_schema_valid': payload_schema_valid,
            'cookies_present': cookies_present,
            'cookies': cookie_data,  
            'classification': classification,
            'confidence': round(confidence * 100, 2),
            'bot_probability': round(bot_probability * 100, 2),
            'suspicious_headers': suspicious_headers,
            'suspicious_headers_count': len(suspicious_headers),
            'spoofed_ua_indicators': spoofed_ua_indicators,  
            'spoofed_ua_count': len(spoofed_ua_indicators),  
            'request_fingerprint': request_fingerprint,
            'session_id': session_id,
            'is_headless_browser': is_headless,
            'automation_detected': is_automation,
            'rate_limit_exceeded': rate_limit_exceeded,
            'browser_info': browser_info if browser_info else {},
            'detection_features': {
                'user_agent_length': len(user_agent),
                'has_cookies': cookies_present,
                'request_timing': {
                    'interval': request_interval,
                    'too_fast': request_interval is not None and request_interval < 1.0,
                    'very_fast': request_interval is not None and request_interval < 0.3
                },
                'timing_analysis': {
                    'hour_of_day': timestamp.hour,
                    'is_weekend': timestamp.weekday() >= 5,
                    'unusual_hours': timestamp.hour < 5 or timestamp.hour > 23
                }
            }
        }
        
       
        if is_bot:
            # Classified as bot - determine blocking based on confidence
            if confidence > 0.8:  # Very high confidence required for blocking (increased from 0.7)
                response = JsonResponse({
                    'status': 'blocked',
                    'message': 'Automated HTTP client detected. Access denied.',
                    'detection_id': detection_record.id,
                    **detection_analysis,
                    'reason': 'High confidence automated HTTP client detection',
                    'detected_indicators': {
                        'automation_tool': is_automation,
                        'headless_browser': is_headless,
                        'suspicious_headers': len(suspicious_headers) > 0,
                        'suspicious_headers_count': len(suspicious_headers),
                        'spoofed_user_agent': len(spoofed_ua_indicators) > 0,  # NEW
                        'spoofed_ua_indicators_count': len(spoofed_ua_indicators),  # NEW
                        'rate_limit_exceeded': rate_limit_exceeded,
                        'fast_requests': request_interval is not None and request_interval < 1.0,
                        'very_fast_requests': request_interval is not None and request_interval < 0.3,
                        'missing_cookies': not cookies_present,
                        'user_agent_suspicious': is_automation or is_headless,
                        'unusual_timing': timestamp.hour < 5 or timestamp.hour > 23,
                        'weekend_activity': timestamp.weekday() >= 5
                    }
                }, status=403)
            else:
                # Low confidence bot - allow but flag
                response = JsonResponse({
                    'status': 'allowed',
                    'message': 'Possible automated client detected but allowed due to low confidence.',
                    'detection_id': detection_record.id,
                    **detection_analysis,
                    'warning': 'Request shows some automation characteristics'
                }, status=200)
        else:
            # Classified as human
            response = JsonResponse({
                'status': 'allowed',
                'message': 'Request appears to be from legitimate human user.',
                'detection_id': detection_record.id,
                **detection_analysis
            }, status=200)

        return response
        
    except Exception as e:
        logger.error(f"Error in HTTP bot detection: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error during bot detection',
            'error': str(e)
        }, status=500)

@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def initialize_session(request):
    """
    Initialize session endpoint - now works with client-generated tokens
    This endpoint allows legitimate frontend apps to register their client tokens
    and receive server-side session confirmation
    """
    try:
        # Extract client-generated tokens if provided
        client_session_id = ''
        client_csrf_token = ''
        
        if request.method == 'POST' and request.content_type == 'application/json':
            try:
                request_body = json.loads(request.body)
                client_session_id = request_body.get('session_id', '') or request_body.get('sessionId', '')
                client_csrf_token = request_body.get('csrf_token', '') or request_body.get('csrfToken', '')
            except json.JSONDecodeError:
                pass
        
        # Also check headers
        if not client_session_id:
            client_session_id = request.META.get('HTTP_X_SESSION_ID', '')
        if not client_csrf_token:
            client_csrf_token = request.META.get('HTTP_X_CSRF_TOKEN', '')
        
        # If no client tokens provided, this might be a bot or incomplete integration
        if not client_session_id and not client_csrf_token:
            logger.warning("Session initialization without client tokens - possible bot or incomplete integration")
            
            # For backward compatibility, generate server tokens
            from django.middleware.csrf import get_token
            
            if not request.session.session_key:
                request.session.create()
            request.session.modified = True
            request.session.save()
            
            server_session_id = request.session.session_key
            server_csrf_token = get_token(request)
            
            # DEBUGGING: Log CSRF token generation
            logger.info(f"GENERATED SERVER CSRF TOKEN: {server_csrf_token}")
            logger.info(f"CSRF token length: {len(server_csrf_token) if server_csrf_token else 0}")
            logger.info(f"Session key: {server_session_id}")
            
            response_data = {
                'status': 'warning',
                'message': 'Session initialized with server tokens - consider implementing client token generation',
                'session_data': {
                    'session_id': server_session_id,
                    'csrf_token': server_csrf_token,
                    'timestamp': timezone.now().isoformat(),
                    'ip_address': detector.get_client_ip(request),
                    'token_source': 'server_generated'
                },
                'recommendation': 'Implement client-side token generation for better bot protection'
            }
            
            response = JsonResponse(response_data)
            response.set_cookie('sessionid', server_session_id, max_age=86400, httponly=True, samesite='Lax')
            response.set_cookie('csrftoken', server_csrf_token, max_age=86400, samesite='Lax')
            
            # DEBUGGING: Log cookie setting
            logger.info(f"SETTING COOKIES: sessionid={server_session_id}, csrftoken={server_csrf_token[:20]}...")
            
        else:
            # Client provided tokens - validate and confirm
            logger.info(f"Session initialization with client tokens: Session={bool(client_session_id)}, CSRF={bool(client_csrf_token)}")
            
            # Validate client token formats (basic validation)
            session_valid = client_session_id.startswith('client_') if client_session_id else False
            csrf_valid = client_csrf_token.startswith('csrf_') if client_csrf_token else False
            
            response_data = {
                'status': 'success',
                'message': 'Session initialized with client tokens',
                'session_data': {
                    'session_id': client_session_id,
                    'csrf_token': client_csrf_token,
                    'timestamp': timezone.now().isoformat(),
                    'ip_address': detector.get_client_ip(request),
                    'token_source': 'client_generated',
                    'validation': {
                        'session_format_valid': session_valid,
                        'csrf_format_valid': csrf_valid
                    }
                }
            }
            
            if not session_valid or not csrf_valid:
                response_data['warning'] = 'Client token format validation failed - check token generation'
                logger.warning(f"Invalid client token format: Session={session_valid}, CSRF={csrf_valid}")
            
            response = JsonResponse(response_data)
            
            # Set cookies with client tokens
            if client_session_id:
                response.set_cookie('sessionid', client_session_id, max_age=86400, httponly=True, samesite='Lax')
            if client_csrf_token:
                response.set_cookie('csrftoken', client_csrf_token, max_age=86400, samesite='Lax')
        
        # Set additional tracking cookies
        response.set_cookie('bot_detection_init', 'true', max_age=3600)
        response.set_cookie('visit_timestamp', str(int(timezone.now().timestamp())), max_age=3600)
        response.set_cookie('client_id', f"client_{int(timezone.now().timestamp())}", max_age=86400)
        
        logger.info(f"Session initialized successfully for IP: {detector.get_client_ip(request)}")
        return response
        
    except Exception as e:
        logger.error(f"Error initializing session: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to initialize session',
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
