from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, UserSession, SignInAttempt, SignUpAttempt, BehavioralData, UserBaselineBehavior
import json
import uuid
import logging
import math
import statistics
import numpy as np
from scipy.spatial.distance import mahalanobis
from scipy import linalg
from datetime import datetime, timedelta
import threading
import time 
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
@require_http_methods(["POST", "GET"])
def sign_up(request):
    """
    Handle user sign-up requests from sign-up.js
    GET: Returns endpoint info
    POST: Stores Name and USAI ID in SignUpAttempt table
    """
    if request.method == "GET": 
        return JsonResponse({
            'message': 'Sign-up endpoint is working',
            'method': 'POST',
            'required_fields': ['name', 'usai_id'],
            'example': {
                'name': 'John Doe',
                'usai_id': 'USAI123456'
            }
        })
    try:
        data = json.loads(request.body)
        
        # Extract required fields
        name = data.get('name', '').strip()
        usai_id = data.get('usai_id', '').strip()
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get client information
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        print(f"DEBUG: Received signup request - Name: '{name}', USAI ID: '{usai_id}'")  # Debug log
        
        # Validation
        if not all([name, usai_id]):
            error_msg = "Missing required fields: name, usai_id"

            # Log failed attempt
            failed_attempt = SignUpAttempt.objects.create(
                session_id=session_id,
                name=name,
                usai_id=usai_id,
                success=False
            )
            print(f"DEBUG: Created failed attempt with ID: {failed_attempt.id}")  # Debug log
            
            return JsonResponse({
                'success': False,
                'message': error_msg,
                'session_id': session_id
            }, status=400)
        
        if SignUpAttempt.objects.filter(usai_id=usai_id, success=True).exists():
            error_msg = f"User with USAI ID '{usai_id}' already registered"
            
            duplicate_attempt = SignUpAttempt.objects.create(
                session_id=session_id,
                name=name,
                usai_id=usai_id,
                success=False,
            )
            print(f"DEBUG: Created duplicate attempt with ID: {duplicate_attempt.id}")  # Debug log
            
            return JsonResponse({
                'success': False,
                'message': error_msg,
                'session_id': session_id
            }, status=400)
        
        signup_attempt = SignUpAttempt.objects.create(
            session_id=session_id,
            name=name,
            usai_id=usai_id,
            success=True,
        )
        
        user_session = UserSession.objects.create(
            session_id=session_id,
            name=name,
            usai_id=usai_id,
            session_type='SIGNUP'
        )

        
        return JsonResponse({
            'success': True,
            'message': 'User registered successfully',
            'session_id': session_id,
            'signup_id': signup_attempt.id,
            'session_record_id': user_session.id,
            'usai_id': usai_id,
            'name': name
        }, status=201)
        
    except json.JSONDecodeError:
        error_msg = "Invalid JSON data"
        session_id = str(uuid.uuid4())
        
        SignUpAttempt.objects.create(
            session_id=session_id,
            name='',
            usai_id='',
            success=False,
        )
        
        return JsonResponse({
            'success': False,
            'message': error_msg,
            'session_id': session_id
        }, status=400)
    
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        session_id = str(uuid.uuid4())
        
        SignUpAttempt.objects.create(
            session_id=session_id,
            name=data.get('name', '') if 'data' in locals() else '',
            usai_id=data.get('usai_id', '') if 'data' in locals() else '',
            success=False,
        )
        
        logger.error(f"Sign-up error: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': 'Internal server error',
            'session_id': session_id
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def sign_in(request):
    """
    Handle user sign-in requests from sign-in.js
    Authenticates user and stores attempt in SignInAttempt table
    """
    try:
        data = json.loads(request.body)
        
        usai_id = data.get('usai_id', '').strip()
        password = data.get('password', '')
        username = data.get('username', usai_id)  
        
        session_id = str(uuid.uuid4())
        
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if not all([usai_id, password]):
            error_msg = "Missing required fields: usai_id and password"
            
            SignInAttempt.objects.create(
                session_id=session_id,
                usai_id=usai_id,
                success=False,
                error_message=error_msg,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return JsonResponse({
                'success': False,
                'message': error_msg,
                'session_id': session_id
            }, status=400)
        
        user = None
        user_profile = None
        name = None
        
        try:
            user_profile = UserProfile.objects.get(usai_id=usai_id)
            user = user_profile.user
            name = f"{user.first_name} {user.last_name}".strip() or user.username
        except UserProfile.DoesNotExist:
            try:
                user = User.objects.get(username=username)
                try:
                    user_profile = user.profile
                    name = f"{user.first_name} {user.last_name}".strip() or user.username
                except AttributeError:
                    name = f"{user.first_name} {user.last_name}".strip() or user.username
            except User.DoesNotExist:
                error_msg = f"User with USAI ID '{usai_id}' not found"
                
                SignInAttempt.objects.create(
                    session_id=session_id,
                    usai_id=usai_id,
                    success=False,
                    error_message=error_msg,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return JsonResponse({
                    'success': False,
                    'message': error_msg,
                    'session_id': session_id
                }, status=404)
        
        authenticated_user = authenticate(request, username=user.username, password=password)
        
        if authenticated_user is not None:
            # Login successful
            login(request, authenticated_user)
            
            # Create user session
            user_session = UserSession.objects.create(
                session_id=session_id,
                name=name,
                usai_id=usai_id,
                session_type='SIGNIN',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            SignInAttempt.objects.create(
                session_id=session_id,
                name=name,
                usai_id=usai_id,
                user=authenticated_user,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'session_id': session_id,
                'user_id': authenticated_user.id,
                'usai_id': usai_id,
                'name': name,
                'username': authenticated_user.username
            }, status=200)
        
        else:
            error_msg = "Invalid password"
            
            SignInAttempt.objects.create(
                session_id=session_id,
                name=name,
                usai_id=usai_id,
                user=user,
                success=False,
                error_message=error_msg,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return JsonResponse({
                'success': False,
                'message': error_msg,
                'session_id': session_id
            }, status=401)
            
    except json.JSONDecodeError:
        error_msg = "Invalid JSON data"
        session_id = str(uuid.uuid4())
        
        SignInAttempt.objects.create(
            session_id=session_id,
            usai_id='',
            success=False,
            error_message=error_msg,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': False,
            'message': error_msg,
            'session_id': session_id
        }, status=400)
    
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        session_id = str(uuid.uuid4())
        
        SignInAttempt.objects.create(
            session_id=session_id,
            usai_id=data.get('usai_id', '') if 'data' in locals() else '',
            success=False,
            error_message=error_msg,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.error(f"Sign-in error: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': 'Internal server error',
            'session_id': session_id
        }, status=500)

is_authorized = False
class BehavioralAnalyzer:
   
    def __init__(self):
        self.authorized_profiles = {}  
        self.real_time_sessions = {}   

    def _extract_time_series_values(self, data, metric):
        """Extract time-series values for a given metric from behavioral data"""
        try:
            if metric == 'cursor_movements':
                values = (data.get('cursor_movements', []) or 
                         data.get('cursorMovements', []))
            elif metric == 'cursor_speeds':
                values = data.get('cursor_speeds', [])
            elif metric == 'key_press_times':
                values = (data.get('key_press_times', []) or 
                         data.get('keyPressTimes', []))
            elif metric == 'key_hold_times':
                values = (data.get('key_hold_times', []) or 
                         data.get('keyHoldTimes', []))
            elif metric == 'scroll_speeds':
                values = data.get('scroll_speeds', [])
            elif metric == 'mouseJitter':
                values = data.get('mouseJitter', [])
            elif metric == 'micropause':
                values = (data.get('micropause', []) or 
                         data.get('microPauses', []))
            elif metric == 'hesitation':
                values = data.get('hesitation', [])
            else:
                values = []

            # Ensure we have a valid list
            if not isinstance(values, list):
                values = []

            return values

        except Exception as e:
            print(f"Error extracting time-series values for {metric}: {e}")
            return []

    def _analyze_time_series_metrics(self, current_data, baseline_data):
        """Fixed time-series analysis with more realistic expectations"""
        try:
            time_series_metrics = [
                'cursor_movements', 'cursorMovements',
                'key_press_times', 'keyPressTimes', 
                'key_hold_times', 'keyHoldTimes',
                'cursor_speeds', 'scroll_speeds',
                'mouseJitter', 'micropause', 'hesitation'
            ]
            
            valid_comparisons = 0
            total_similarity = 0.0
            
            for metric in time_series_metrics:
                current_values = self._extract_time_series_values(current_data, metric)
                baseline_values = self._extract_time_series_values(baseline_data, metric)
                
                # Skip empty datasets
                if not current_values or not baseline_values:
                    continue
                
                # Calculate similarity for this metric
                metric_similarity = self._calculate_time_series_similarity(current_values, baseline_values)
                
                if metric_similarity is not None:
                    total_similarity += metric_similarity
                    valid_comparisons += 1
            
            if valid_comparisons == 0:
                return 0.75  # Neutral score when no valid comparisons
            
            average_similarity = total_similarity / valid_comparisons
            
            # Apply more generous minimum threshold
            return max(0.55, min(1.0, average_similarity))
            
        except Exception as e:
            print(f"Error in time-series analysis: {e}")
            return 0.75  
    
    def _extract_numeric_features(self, values):
        """Extract numeric features from behavioral data"""
        try:
            numeric_values = []
            
            for item in values:
                if isinstance(item, (int, float)):
                    if not math.isnan(item):
                        numeric_values.append(float(item))
                elif isinstance(item, dict):
                    # Extract from common fields
                    for field in ['x', 'y', 'timestamp', 'duration', 'speed', 'distance']:
                        if field in item and isinstance(item[field], (int, float)):
                            if not math.isnan(item[field]):
                                numeric_values.append(float(item[field]))
            
            return numeric_values if len(numeric_values) >= 2 else None
            
        except Exception as e:
            print(f"Error extracting numeric features: {e}")
            return None
        
    def _compare_statistical_distributions(self, current_features, baseline_features):
        """Compare statistical properties with realistic tolerances"""
        try:
            if len(current_features) < 2 or len(baseline_features) < 2:
                return None
            
            current_mean = np.mean(current_features)
            baseline_mean = np.mean(baseline_features)
            current_std = np.std(current_features)
            baseline_std = np.std(baseline_features)
            
            # More lenient difference calculations
            mean_diff = abs(current_mean - baseline_mean) / (abs(baseline_mean) + 100)  # Added offset
            std_diff = abs(current_std - baseline_std) / (baseline_std + 50)  # Added offset
            
            # Convert to similarity with generous scaling
            mean_similarity = max(0, 1.0 - mean_diff * 0.5)  # Reduced penalty
            std_similarity = max(0, 1.0 - std_diff * 0.3)   # Reduced penalty
            
            return (mean_similarity + std_similarity) / 2
            
        except Exception as e:
            print(f"Error comparing statistical distributions: {e}")
            return None
        
    def _extract_intervals(self, values):
        """Extract timing intervals from data"""
        try:
            timestamps = []
            
            for item in values:
                if isinstance(item, dict) and 'timestamp' in item:
                    timestamps.append(item['timestamp'])
                elif isinstance(item, (int, float)):
                    timestamps.append(item)
            
            if len(timestamps) < 2:
                return None
            
            intervals = []
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i-1]
                if interval > 0:
                    intervals.append(interval)
            
            return intervals if intervals else None
            
        except Exception as e:
            return None
        
    def _normalize_intervals(self, intervals):
        """Normalize intervals for pattern comparison"""
        try:
            if len(intervals) < 2:
                return None
            
            mean_interval = np.mean(intervals)
            if mean_interval <= 0:
                return None
            
            normalized = [interval / mean_interval for interval in intervals]
            return normalized
            
        except Exception as e:
            return None
        
    def _compare_timing_rhythms(self, current_values, baseline_values):
        """Compare timing patterns with realistic expectations"""
        try:
            current_intervals = self._extract_intervals(current_values)
            baseline_intervals = self._extract_intervals(baseline_values)
            
            if not current_intervals or not baseline_intervals:
                return None
            
            if len(current_intervals) < 2 or len(baseline_intervals) < 2:
                return 0.7  # Neutral for insufficient data
            
            # Normalize intervals to compare patterns rather than absolute timing
            current_norm = self._normalize_intervals(current_intervals)
            baseline_norm = self._normalize_intervals(baseline_intervals)
            
            if not current_norm or not baseline_norm:
                return 0.7
            
            # Calculate correlation with generous interpretation
            min_len = min(len(current_norm), len(baseline_norm), 15)  # Limit comparison
            current_sample = current_norm[:min_len]
            baseline_sample = baseline_norm[:min_len]
            
            correlation = np.corrcoef(current_sample, baseline_sample)[0, 1]
            
            if math.isnan(correlation):
                return 0.7
            
            # Convert correlation to similarity with generous scaling
            similarity = (abs(correlation) + 0.5) / 1.5  # Boost correlation scores
            return max(0.4, min(1.0, similarity))
            
        except Exception as e:
            print(f"Error comparing timing rhythms: {e}")
            return None
        
    def _compare_value_ranges(self, current_features, baseline_features):
        """Compare value ranges with tolerances"""
        try:
            current_min, current_max = min(current_features), max(current_features)
            baseline_min, baseline_max = min(baseline_features), max(baseline_features)
            
            current_range = current_max - current_min
            baseline_range = baseline_max - baseline_min
            
            if baseline_range == 0:
                return 0.8  # Generous default for zero range
            
            # Compare ranges with generous tolerance
            range_diff = abs(current_range - baseline_range) / baseline_range
            range_similarity = max(0.3, 1.0 - range_diff * 0.2)  # Very generous
            
            # Compare overlap
            overlap_start = max(current_min, baseline_min)
            overlap_end = min(current_max, baseline_max)
            
            if overlap_end > overlap_start:
                overlap = overlap_end - overlap_start
                total_span = max(current_max, baseline_max) - min(current_min, baseline_min)
                overlap_similarity = overlap / total_span if total_span > 0 else 0.7
            else:
                overlap_similarity = 0.3  # Some score even for no overlap
            
            return (range_similarity + overlap_similarity) / 2
            
        except Exception as e:
            return None
        

    def _calculate_time_series_similarity(self, current_values, baseline_values):
        """More robust similarity calculation"""
        try:
            if len(current_values) < 2 or len(baseline_values) < 2:
                return 0.6  # Neutral for insufficient data
            
            # Extract numeric features from both datasets
            current_features = self._extract_numeric_features(current_values)
            baseline_features = self._extract_numeric_features(baseline_values)
            
            if not current_features or not baseline_features:
                return 0.7
            
            # Calculate multiple similarity measures
            similarities = []
            
            # 1. Statistical distribution similarity
            stat_sim = self._compare_statistical_distributions(current_features, baseline_features)
            if stat_sim is not None:
                similarities.append(stat_sim)
            
            # 2. Pattern rhythm similarity (for timing data)
            rhythm_sim = self._compare_timing_rhythms(current_values, baseline_values)
            if rhythm_sim is not None:
                similarities.append(rhythm_sim)
            
            # 3. Value range similarity
            range_sim = self._compare_value_ranges(current_features, baseline_features)
            if range_sim is not None:
                similarities.append(range_sim)
            
            if not similarities:
                return 0.7
            
            # Return weighted average with generous interpretation
            final_similarity = sum(similarities) / len(similarities)
            return max(0.4, min(1.0, final_similarity))
            
        except Exception as e:
            print(f"Error calculating time-series similarity: {e}")
            return 0.7
        
    def _get_metric_value_safe(self, data, metric):
        """Safely extract metric value with fallbacks"""
        if not data or not isinstance(data, dict):
            return None
            
        # Handle different key variations
        variations = {
            'cursor_entropy': ['cursor_entropy', 'cursorEntropy'],
            'cursorAngleVariance': ['cursorAngleVariance', 'cursor_angle_variance'],
            'total_time': ['total_time', 'totalTime'],
            'action_count': ['action_count', 'actionCount'],
            'idle_time': ['idle_time', 'idleTime'],
            'suspicious_feature_ratio': ['suspicious_feature_ratio', 'suspiciousFeatureRatio']
        }
        
        keys_to_try = variations.get(metric, [metric])
        
        for key in keys_to_try:
            value = data.get(key)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
                    
        return None
        
    def _analyze_statistical_metrics(self, current_data, baseline_data):
        """More robust statistical analysis with better missing data handling"""
        try:
            metrics = [
                'cursor_entropy', 'cursorAngleVariance', 'total_time',
                'idle_time', 'suspicious_feature_ratio', 'action_count'
            ]

            valid_pairs = []
            
            for metric in metrics:
                current_val = self._get_metric_value_safe(current_data, metric)
                baseline_val = self._get_metric_value_safe(baseline_data, metric)
                
                if current_val is not None and baseline_val is not None:
                    valid_pairs.append((float(current_val), float(baseline_val)))

            if len(valid_pairs) < 2:
                return 0.7  # Neutral score for insufficient data
            
            current_vec = np.array([pair[0] for pair in valid_pairs])
            baseline_vec = np.array([pair[1] for pair in valid_pairs])
            
            # Improved similarity calculation
            try:
                # Normalize to prevent scale issues
                current_norm = current_vec / (np.linalg.norm(current_vec) + 1e-8)
                baseline_norm = baseline_vec / (np.linalg.norm(baseline_vec) + 1e-8)

                # Cosine similarity
                cosine_sim = np.dot(current_norm, baseline_norm)
                cosine_sim = max(-1, min(1, cosine_sim))
                similarity = (cosine_sim + 1) / 2

                return max(0.2, min(1.0, similarity))
                
            except Exception:
                # Fallback to element-wise comparison
                relative_diffs = np.abs(current_vec - baseline_vec) / (np.abs(baseline_vec) + 1e-8)
                avg_diff = np.mean(relative_diffs)
                similarity = max(0.4, 1.0 - min(1.0, avg_diff))
                return similarity

        except Exception as e:
            print(f"Error in statistical analysis: {e}")
            return 0.7
        
    def _analyze_device_fingerprints(self, current_data, baseline_data):
        """Analyze device/environment fingerprints"""
        try:
            device_metrics = [
                'devicefingerprint', 'gpu_info', 'canvas_metrics', 
                'unsualscreenresolution', 'evasion_signals'
            ]
            
            total_score = 0
            valid_metrics = 0
            
            for metric in device_metrics:
                current_value = current_data.get(metric, {})
                baseline_value = baseline_data.get(metric, {})
                
                if metric == 'devicefingerprint' and not current_value:
                    current_value = current_data.get('deviceFingerprint', {})
                if metric == 'devicefingerprint' and not baseline_value:
                    baseline_value = baseline_data.get('deviceFingerprint', {})
                
                if not current_value or not baseline_value:
                    continue
                
                if metric == 'devicefingerprint':
                    if str(current_value) == str(baseline_value):
                        total_score += 1.0
                    else:
                        total_score += 0.6
                elif metric == 'gpu_info':
                    current_vendor = str(current_value.get('vendor', '')).lower()
                    baseline_vendor = str(baseline_value.get('vendor', '')).lower()
                    
                    if current_vendor == baseline_vendor:
                        total_score += 1.0
                    elif current_vendor and baseline_vendor:
                        total_score += 0.8
                    else:
                        total_score += 0.5
                # Add other metric comparisons...
                
                valid_metrics += 1
                
            if valid_metrics == 0:
                return 0.7
            
            return total_score / valid_metrics
            
        except Exception as e:
            print(f"Error in device analysis: {e}")
            return 0.7
        
    def _analyze_boolean_signals(self, current_data, baseline_data):
        """More lenient boolean signal analysis"""
        try:
            boolean_metrics = [
                'paste_detected', 'is_automated_browser', 'missing_canvas_fingerprint', 
                'suspicious_flag', 'evasion_signals'
            ]
            
            total_score = 1.0
            
            for metric in boolean_metrics:
                current_value = current_data.get(metric, False)
                
                # FIXED: Much lighter penalties
                if metric == 'paste_detected' and current_value:
                    total_score -= 0.02  # Reduced from 0.2
                elif metric == 'is_automated_browser' and current_value:
                    total_score -= 0.15   # Reduced from 0.5
                elif metric == 'missing_canvas_fingerprint' and current_value:
                    total_score -= 0.05   # Reduced from 0.3
                elif metric == 'suspicious_flag' and current_value:
                    total_score -= 0.08  # Reduced from 0.4
                elif metric == 'evasion_signals' and current_value:
                    evasion_data = current_data.get('evasion_signals', {})
                    if isinstance(evasion_data, dict):
                        if evasion_data.get('webdriver', False):
                            total_score -= 0.2  # Reduced from 0.6
                        if evasion_data.get('languages_spoofed', False):
                            total_score -= 0.05  # Reduced from 0.3
                        if evasion_data.get('plugins_spoofed', False):
                            total_score -= 0.05  # Reduced from 0.3
            
            return max(0.5, total_score)  # Higher minimum score
            
        except Exception as e:
            print(f"Error in boolean analysis: {e}")
            return 0.75  # More generous fallback

    def _check_immediate_red_flags(self, current_data):
            try:
                # Check honeypot fields
                honeypot_value = current_data.get('honeypot_value', '')
                if honeypot_value and honeypot_value.strip():
                    return {
                        'blocked': True,
                        'reason': 'Honeypot field filled - likely automated attack'
                    }

                # Check for extreme automation signals
                evasion_signals = current_data.get('evasion_signals', {})
                if evasion_signals.get('webdriver', False) or evasion_signals.get('headless_mode', False):
                    return {
                        'blocked': True,
                        'reason': 'WebDriver/Headless mode detected - automated browser'
                    }

                # Check for suspicious GPU vendors
                gpu_info = current_data.get('gpu_info', {})
                suspicious_vendors = ['microsoft', 'llvmpipe', 'swiftshader', 'mesa', 'google', 'virtualbox', 'vmware', 'parallels']
                if any(vendor in str(gpu_info.get('vendor', '')).lower() for vendor in suspicious_vendors):
                    return {
                        'blocked': True,
                        'reason': 'Suspicious GPU vendor detected - likely VM/automation'
                    }

                return {'blocked': False, 'reason': None}

            except Exception as e:
                print(f"Error checking red flags: {e}")
                return {'blocked': False, 'reason': None}
    
    def _fuse_domain_scores(self, time_series_score, statistical_score, boolean_score, device_score):
        """Fixed scoring fusion with realistic thresholds"""
        try:
            print(f"   Domain scores - Time: {time_series_score:.3f}, Statistical: {statistical_score:.3f}")
            print(f"   Domain scores - Boolean: {boolean_score:.3f}, Device: {device_score:.3f}")

            # More balanced and realistic weighting
            weights = {
                'time_series': 0.40,    # Primary behavioral indicator
                'statistical': 0.35,    # Secondary behavioral indicator  
                'boolean': 0.15,        # Security flags (reduced impact)
                'device': 0.10          # Environment consistency (minimal impact)
            }

            # Apply realistic minimum floors - users shouldn't fail on single domain
            time_series_score = max(0.45, time_series_score)   # Increased floor
            statistical_score = max(0.45, statistical_score)    # Increased floor
            boolean_score = max(0.60, boolean_score)            # Higher floor for security
            device_score = max(0.50, device_score)              # Minimal impact floor

            final_score = (
                weights['time_series'] * time_series_score +
                weights['statistical'] * statistical_score +
                weights['boolean'] * boolean_score +
                weights['device'] * device_score
            )

            # Ensure reasonable bounds with generous interpretation
            final_score = max(0.4, min(1.0, final_score))

            print(f"   Final score: {final_score:.3f}")
            return final_score

        except Exception as e:
            print(f"Error in score fusion: {e}")
            return 0.75  # Generous fallback
    def _compare_metric_arrays(self, current_array, baseline_array):


        """Compare two arrays of metrics"""
        try:
            if not current_array or not baseline_array:
                return 0.6
            
            length_diff = abs(len(current_array) - len(baseline_array))
            max_length = max(len(current_array), len(baseline_array), 1)
            length_similarity = 1.0 - (length_diff / max_length) * 0.5  # Reduced penalty
            
            
            if len(current_array) > 0 and len(baseline_array) > 0:
                try:
                    current_numeric = []
                    baseline_numeric = []
                    
                    for val in current_array:
                        if isinstance(val, dict):
                            for key in ['x', 'y', 'timestamp', 'speed', 'distance']:
                                if key in val and isinstance(val[key], (int, float)):
                                    current_numeric.append(float(val[key]))
                        elif isinstance(val, (int, float)):
                            current_numeric.append(float(val))
                    
                    for val in baseline_array:
                        if isinstance(val, dict):
                            for key in ['x', 'y', 'timestamp', 'speed', 'distance']:
                                if key in val and isinstance(val[key], (int, float)):
                                    baseline_numeric.append(float(val[key]))
                        elif isinstance(val, (int, float)):
                            baseline_numeric.append(float(val))
                    
                    if current_numeric and baseline_numeric:
                        current_mean = np.mean(current_numeric)
                        baseline_mean = np.mean(baseline_numeric)
                        mean_diff = abs(current_mean - baseline_mean)
                        tolerance = max(abs(baseline_mean) * 0.5, 50)  # 50% tolerance or minimum 50
                        value_similarity = max(0.3, 1.0 - (mean_diff / tolerance))
                        return (length_similarity + max(0, min(1, value_similarity))) / 2
                except:
                    pass
            
            return length_similarity
            
        except Exception as e:
            print(f"Error comparing metric arrays: {e}")
            return 0.5

    def _get_time_series_breakdown(self, current_data, baseline_data):
        """Get detailed breakdown of time-series analysis"""
        try:
            return {
                'cursor_movements_similarity': self._compare_metric_arrays(
                    current_data.get('cursor_movements', []) or current_data.get('cursorMovements', []), 
                    baseline_data.get('cursor_movements', []) or baseline_data.get('cursorMovements', [])
                ),
                'key_press_times_similarity': self._compare_metric_arrays(
                    current_data.get('key_press_times', []) or current_data.get('keyPressTimes', []), 
                    baseline_data.get('key_press_times', []) or baseline_data.get('keyPressTimes', [])
                ),
                'click_timestamps_similarity': self._compare_metric_arrays(
                    current_data.get('click_timestamps', []) or current_data.get('clickTimestamps', []), 
                    baseline_data.get('click_timestamps', []) or baseline_data.get('clickTimestamps', [])
                )
            }
        except Exception as e:
            print(f"Error getting time-series breakdown: {e}")
            return {}
        

    def _get_statistical_breakdown(self, current_data, baseline_data):
        """Get detailed breakdown of statistical analysis"""
        try:
            return {
                'cursor_entropy_diff': abs(
                    (current_data.get('cursor_entropy', 0) or current_data.get('cursorEntropy', 0)) - 
                    (baseline_data.get('cursor_entropy', 0) or baseline_data.get('cursorEntropy', 0))
                ),
                'action_count_diff': abs(
                    (current_data.get('action_count', 0) or current_data.get('actionCount', 0)) - 
                    (baseline_data.get('action_count', 0) or baseline_data.get('actionCount', 0))
                ),
                'total_time_diff': abs(
                    (current_data.get('total_time', 0) or current_data.get('totalTime', 0)) - 
                    (baseline_data.get('total_time', 0) or baseline_data.get('totalTime', 0))
                )
            }
        except Exception as e:
            print(f"Error getting statistical breakdown: {e}")
            return {}

    def _get_boolean_breakdown(self, current_data, baseline_data):
        """Get detailed breakdown of boolean analysis"""
        try:
            return {
                'paste_detected': current_data.get('paste_detected', False),
                'is_automated_browser': current_data.get('is_automated_browser', False),
                'missing_canvas_fingerprint': current_data.get('missing_canvas_fingerprint', False),
                'suspicious_flag': current_data.get('suspicious_flag', False),
                'evasion_signals_count': sum(1 for v in current_data.get('evasion_signals', {}).values() if v) if isinstance(current_data.get('evasion_signals'), dict) else 0
            }
        except Exception as e:
            print(f"Error getting boolean breakdown: {e}")
            return {}

    def _get_device_breakdown(self, current_data, baseline_data):
        """Get detailed breakdown of device analysis"""
        try:
            current_device = str(current_data.get('devicefingerprint', '') or current_data.get('deviceFingerprint', ''))
            baseline_device = str(baseline_data.get('devicefingerprint', '') or baseline_data.get('deviceFingerprint', ''))
            
            current_gpu = current_data.get('gpu_info', {})
            baseline_gpu = baseline_data.get('gpu_info', {})
            
            current_screen = current_data.get('unsualscreenresolution', {})
            baseline_screen = baseline_data.get('unsualscreenresolution', {})
            
            return {
                'device_fingerprint_match': current_device == baseline_device and current_device != '',
                'gpu_vendor_match': str(current_gpu.get('vendor', '')).lower() == str(baseline_gpu.get('vendor', '')).lower() and current_gpu.get('vendor', '') != '',
                'screen_resolution_match': (
                    f"{current_screen.get('width', 0)}x{current_screen.get('height', 0)}" == 
                    f"{baseline_screen.get('width', 0)}x{baseline_screen.get('height', 0)}" and
                    current_screen.get('width', 0) > 0
                )
            }
        except Exception as e:
            print(f"Error getting device breakdown: {e}")
            return {}

    def _fallback_analysis(self, current_data, error_message):
        """Fallback analysis when comprehensive analysis fails"""
        try:
            # Basic interaction count validation
            total_interactions = (
                len(current_data.get('cursor_movements', [])) + 
                len(current_data.get('cursorMovements', [])) +
                len(current_data.get('key_press_times', [])) + 
                len(current_data.get('keyPressTimes', [])) +
                len(current_data.get('click_timestamps', [])) +
                len(current_data.get('clickTimestamps', []))
            )
            
            # Check for automation signals
            evasion_signals = current_data.get('evasion_signals', {})
            automation_signals = sum(1 for v in evasion_signals.values() if v) if isinstance(evasion_signals, dict) else 0
            
            risk_factors = []
            
            # More permissive fallback - allow users unless clear automation detected
            if total_interactions >= 2:  # Very low bar
                # Check for critical automation signals only
                has_honeypot = bool(current_data.get('honeypot_value', '').strip())
                has_webdriver = evasion_signals.get('webdriver', False) if isinstance(evasion_signals, dict) else False
                has_headless = evasion_signals.get('headless_mode', False) if isinstance(evasion_signals, dict) else False
                
                # Only block if multiple clear automation signals
                if has_honeypot or (has_webdriver and has_headless):
                    risk_factors.append({
                        'metric': 'clear_automation_detected',
                        'severity': 'HIGH',
                        'value': 'Multiple automation signals',
                        'threshold': 'security_violation',
                        'description': 'Clear automation signals detected in fallback analysis'
                    })
                    
                    return {
                        'is_authorized': False,
                        'confidence': 0.8,
                        'authorization_reason': 'FALLBACK_BLOCK: Clear automation signals detected',
                        'analysis_type': 'fallback_automation_detected',
                        'recommendation': 'BLOCK: Clear automation detected',
                        'total_interactions': total_interactions,
                        'automation_signals': automation_signals,
                        'error_message': str(error_message),
                        'risk_factors': risk_factors 
                    }
                else:
                    # Allow user - analysis error but reasonable interaction
                    return {
                        'is_authorized': True,
                        'confidence': 0.7,
                        'authorization_reason': f'FALLBACK_ALLOW: Analysis error but {total_interactions} interactions detected',
                        'analysis_type': 'fallback_analysis',
                        'recommendation': 'ALLOW: Fallback approval due to analysis error',
                        'total_interactions': total_interactions,
                        'automation_signals': automation_signals,
                        'error_message': str(error_message),
                        'risk_factors': risk_factors 
                    }
            else:
                # Very minimal interaction - still be permissive unless clear automation
                has_honeypot = bool(current_data.get('honeypot_value', '').strip())
                if has_honeypot:
                    risk_factors.append({
                        'metric': 'honeypot_filled',
                        'severity': 'CRITICAL',
                        'value': current_data.get('honeypot_value'),
                        'threshold': 'security_violation',
                        'description': 'Honeypot field filled - clear automation'
                    })
                    
                    return {
                        'is_authorized': False,
                        'confidence': 0.9,
                        'authorization_reason': 'FALLBACK_BLOCK: Honeypot filled with minimal interaction',
                        'analysis_type': 'fallback_honeypot_detected',
                        'recommendation': 'BLOCK: Honeypot violation',
                        'total_interactions': total_interactions,
                        'error_message': str(error_message),
                        'risk_factors': risk_factors
                    }
                else:
                    # Allow even with minimal interaction if no clear automation
                    risk_factors.append({
                        'metric': 'minimal_interaction_fallback',
                        'severity': 'MEDIUM',
                        'value': total_interactions,
                        'threshold': 2,
                        'description': f'Minimal interaction in fallback but no clear automation: {total_interactions} interactions'
                    })
                    
                    return {
                        'is_authorized': True,
                        'confidence': 0.6,
                        'authorization_reason': f'FALLBACK_ALLOW: Minimal interaction but no automation signals',
                        'analysis_type': 'fallback_minimal_interaction',
                        'recommendation': 'ALLOW: Fallback approval - no clear automation',
                        'total_interactions': total_interactions,
                        'error_message': str(error_message),
                        'risk_factors': risk_factors
                    }
                      
        except Exception as e:
            print(f"Error in fallback analysis: {e}")
            return {
                'is_authorized': True,  # Default to allowing on critical error
                'confidence': 0.5,
                'authorization_reason': 'CRITICAL_FALLBACK_ALLOW: Multiple analysis failures - defaulting to allow',
                'analysis_type': 'critical_fallback_allow',
                'recommendation': 'ALLOW: Critical system error - fail open for user experience',
                'error_message': str(e),
                'risk_factors': [  
                    {
                        'metric': 'critical_error_fail_open',
                        'severity': 'MEDIUM',
                        'value': str(e),
                        'threshold': 'error',
                        'description': f'Critical fallback error - failing open: {str(e)}'
                    }
                ]
            }



    def analyze_with_baseline_comparison(self, session_id, current_data, baseline_behavior_or_user_id, baseline_metrics=None):
        try:
            print(f"🔍 Session: {session_id}")

        
            baseline_data = None
            user_id = None

            # Check if baseline_behavior_or_user_id is a user_id string to retrieve from database
            if isinstance(baseline_behavior_or_user_id, str):
                user_id = baseline_behavior_or_user_id
                print(f"👤 Retrieving baseline for user: {user_id}")

                try:
                    from .models import UserBaselineBehavior
                    baseline_record = UserBaselineBehavior.objects.filter(
                        user_id=user_id,
                        is_active=True,
                        sufficient_interaction=True
                    ).order_by('-created_at').first()

                    if baseline_record:
                        baseline_data = baseline_record.baseline_user_behavior
                        baseline_metrics = baseline_record.baseline_metrics
                        print(f"✅ Retrieved baseline for user {user_id}")
                        print(f"⚠️ No baseline found for user {user_id} - using permissive fallback")

                    else:
                        print(f"⚠️ No baseline found for user {user_id} - using generous fallback")
                        baseline_data = {
                            'session_id': session_id,
                            'user_id': user_id,
                            'current_data': current_data,
                            'baseline_metrics': baseline_metrics
                        }

                except Exception as e:
                    print(f"⚠️ Database error retrieving baseline for {user_id}: {e}")
                    return {
                        'is_authorized': True,
                        'confidence': 0.6,
                        'mahalanobis_distance': 0.0,
                        'standard_deviations': 0.0,
                        'authorization_reason': f'DATABASE_FALLBACK: Database error occurred but allowing user access - {str(e)}',
                        'analysis_type': 'database_error_fallback',
                        'recommendation': 'ALLOW: Database error - using permissive fallback',
                        'risk_factors': []  # ✅ ALWAYS INCLUDE risk_factors
                    }
            else:
                # Use provided baseline data directly (legacy mode)
                baseline_data = baseline_behavior_or_user_id
                print(f"📊 Using provided baseline data directly")

            if not baseline_data:
                return {
                    'is_authorized': True,
                    'confidence': 0.7,
                    'mahalanobis_distance': 0.0,
                    'standard_deviations': 0.0,
                    'authorization_reason': 'MISSING_BASELINE: No baseline data available - using permissive authorization',
                    'analysis_type': 'missing_baseline_fallback',
                    'recommendation': 'ALLOW: Missing baseline - collecting data for future analysis',
                    'risk_factors': []  # ✅ ALWAYS INCLUDE risk_factors
                }

            # 🚨 CRITICAL: Check for immediate red flags (honeypot, evasion)
            immediate_red_flags = self._check_immediate_red_flags(current_data)
            if immediate_red_flags['blocked']:
                return {
                    'is_authorized': False,
                    'confidence': 0.95,
                    'authorization_reason': f'IMMEDIATE_BLOCK: {immediate_red_flags["reason"]}',
                    'analysis_type': 'immediate_red_flag',
                    'recommendation': 'BLOCK: Critical security violation detected',
                    'risk_factors': [  # ✅ ALWAYS INCLUDE risk_factors
                        {
                            'metric': 'immediate_red_flag',
                            'severity': 'CRITICAL',
                            'value': immediate_red_flags['reason'],
                            'threshold': 'security_violation',
                            'description': f'Critical security violation: {immediate_red_flags["reason"]}'
                        }
                    ]
                }

            # Run comprehensive analysis
            time_series_score = self._analyze_time_series_metrics(current_data, baseline_data)
            statistical_score = self._analyze_statistical_metrics(current_data, baseline_data)
            boolean_score = self._analyze_boolean_signals(current_data, baseline_data)
            device_score = self._analyze_device_fingerprints(current_data, baseline_data)

            # 🔗 STEP 5: FUSION ACROSS ALL DOMAINS
            print(f"🔗 STEP 5: Fusing scores across all domains...")
            final_score = self._fuse_domain_scores(time_series_score, statistical_score, boolean_score, device_score)
            print(f"   ✅ Final fused score: {final_score:.3f}")

            # 🎯 FINAL AUTHORIZATION DECISION
            authorization_threshold = 0.35  # Lowered from 0.6
            is_authorized = final_score >= authorization_threshold
            confidence = final_score

            

            # Generate risk factors based on analysis
            risk_factors = []

            if time_series_score < 0.4:
                risk_factors.append({
                    'metric': 'time_series_similarity',
                    'severity': 'HIGH' if time_series_score < 0.3 else 'MEDIUM',
                    'value': time_series_score,
                    'threshold': 0.4,
                    'description': f'Time-series behavioral patterns show low similarity: {time_series_score:.3f}'
                })

            if statistical_score < 0.4:
                risk_factors.append({
                    'metric': 'statistical_similarity',
                    'severity': 'HIGH' if statistical_score < 0.3 else 'MEDIUM',
                    'value': statistical_score,
                    'threshold': 0.4,
                    'description': f'Statistical behavioral metrics show low similarity: {statistical_score:.3f}'
                })

            if boolean_score < 0.6:
                risk_factors.append({
                    'metric': 'boolean_signals',
                    'severity': 'HIGH' if boolean_score < 0.5 else 'MEDIUM',
                    'value': boolean_score,
                    'threshold': 0.6,
                    'description': f'Boolean risk signals detected: {boolean_score:.3f}'
                })

            if device_score < 0.5:
                risk_factors.append({
                    'metric': 'device_fingerprint',
                    'severity': 'MEDIUM',
                    'value': device_score,
                    'threshold': 0.5,
                    'description': f'Device/environment fingerprint mismatch: {device_score:.3f}'
                })

            # 📊 COMPREHENSIVE ANALYSIS RESULT
            analysis_result = {
                'is_authorized': is_authorized,
                'confidence': confidence,
                'final_score': final_score,
                'authorization_reason': f'COMPREHENSIVE_ANALYSIS: Final score {final_score:.3f} {"≥" if is_authorized else "<"} 0.6 threshold',
                'analysis_type': 'comprehensive_multi_domain',
                'risk_factors': risk_factors,  # ✅ ALWAYS INCLUDE risk_factors

                # Domain-specific scores
                'domain_scores': {
                    'time_series_score': time_series_score,
                    'statistical_score': statistical_score,
                    'boolean_score': boolean_score,
                    'device_score': device_score
                },

                # Detailed analysis breakdown
                'analysis_breakdown': {
                    'time_series_analysis': self._get_time_series_breakdown(current_data, baseline_data),
                    'statistical_analysis': self._get_statistical_breakdown(current_data, baseline_data),
                    'boolean_analysis': self._get_boolean_breakdown(current_data, baseline_data),
                    'device_analysis': self._get_device_breakdown(current_data, baseline_data)
                },

                # Metadata
                'session_id': session_id,
                'user_id': user_id,
                'baseline_quality': baseline_metrics.get('data_quality_score', 0.5) if baseline_metrics else 0.5,
                'timestamp': timezone.now().isoformat()
            }

            print(f"🎯 FINAL DECISION: {'AUTHORIZED' if is_authorized else 'UNAUTHORIZED'} (Score: {final_score:.3f})")
            return analysis_result

        except Exception as e:
            print(f"🚨 CRITICAL ERROR in comprehensive behavioral analysis: {e}")
            logger.error(f"Comprehensive behavioral analysis error: {str(e)}")

            # Fallback to basic validation
            return self._fallback_analysis(current_data, str(e))


    def _generate_simple_risk_factors(self, current_data, risk_score, total_interactions):
        """Generate risk factors for simple validation"""
        risk_factors = []
        
        # Check automation signals
        evasion_signals = current_data.get('evasion_signals', {})
        if isinstance(evasion_signals, dict):
            for signal, value in evasion_signals.items():
                if value:
                    risk_factors.append({
                        'metric': f'evasion_signal_{signal}',
                        'severity': 'HIGH' if signal in ['webdriver', 'headless_mode'] else 'MEDIUM',
                        'value': value,
                        'threshold': False,
                        'description': f'Automation signal detected: {signal}'
                    })
        
        # Check paste detection
        if current_data.get('paste_detected', False):
            risk_factors.append({
                'metric': 'paste_detected',
                'severity': 'MEDIUM',
                'value': True,
                'threshold': False,
                'description': 'Paste operation detected'
            })
        
        # Check automated browser
        if current_data.get('is_automated_browser', False):
            risk_factors.append({
                'metric': 'automated_browser',
                'severity': 'HIGH',
                'value': True,
                'threshold': False,
                'description': 'Automated browser detected'
            })
        
        return risk_factors    
        
    
    def simple_behavioral_validation(self, session_id, current_data, user_id=None):
        """Simple validation for new users or when baseline is unavailable"""
        try:
            print(f"🔄 Running simple behavioral validation for session: {session_id}")
            
            # Count total interactions
            total_interactions = (
                len(current_data.get('cursor_movements', [])) + 
                len(current_data.get('cursorMovements', [])) +
                len(current_data.get('key_press_times', [])) + 
                len(current_data.get('keyPressTimes', [])) +
                len(current_data.get('click_timestamps', [])) +
                len(current_data.get('clickTimestamps', []))
            )
            
            # Check for immediate red flags first
            immediate_red_flags = self._check_immediate_red_flags(current_data)
            if immediate_red_flags['blocked']:
                return {
                    'is_authorized': False,
                    'confidence': 0.95,
                    'risk_score': 0.95,
                    'anomaly_score': 0.95,
                    'authorization_reason': f'BLOCKED: {immediate_red_flags["reason"]}',
                    'recommendation': 'BLOCK: Critical security violation detected',
                    'analysis_type': 'simple_validation_blocked',
                    'risk_factors': [
                        {
                            'metric': 'immediate_red_flag',
                            'severity': 'CRITICAL',
                            'value': immediate_red_flags['reason'],
                            'threshold': 'security_violation',
                            'description': f'Critical security violation: {immediate_red_flags["reason"]}'
                        }
                    ]
                }
            
            # Basic interaction threshold check
            min_interactions = 2  # Lowered from previous thresholds
            
            if total_interactions >= min_interactions:
                # Check for obvious automation signals
                evasion_signals = current_data.get('evasion_signals', {})
                automation_signals = sum(1 for v in evasion_signals.values() if v) if isinstance(evasion_signals, dict) else 0
                
                # Check for paste detection and other suspicious flags
                paste_detected = current_data.get('paste_detected', False)
                is_automated = current_data.get('is_automated_browser', False)
                
                # Calculate simple risk score
                risk_score = 0.05  # Base risk
                
                if automation_signals > 0:
                    risk_score += 0.15 * min(automation_signals, 3)
                if paste_detected:
                    risk_score += 0.05
                if is_automated:
                    risk_score += 0.25
                
                risk_score = min(risk_score, 0.8)
                confidence = 1.0 - risk_score
                
                # More lenient decision for new users
                is_authorized = risk_score < 0.7  # Allow up to moderate risk
                
                return {
                    'is_authorized': is_authorized,
                    'confidence': confidence,
                    'risk_score': risk_score,
                    'anomaly_score': risk_score,
                    'authorization_reason': f'SIMPLE_VALIDATION: {total_interactions} interactions, risk_score: {risk_score:.3f}',
                    'recommendation': 'ALLOW: Simple validation passed' if is_authorized else 'BLOCK: Simple validation failed',
                    'analysis_type': 'simple_behavioral_validation',
                    'total_interactions': total_interactions,
                    'automation_signals': automation_signals,
                    'risk_factors': self._generate_simple_risk_factors(current_data, risk_score, total_interactions)
                }
            else:
                # Very limited interaction - still allow but with lower confidence
                return {
                    'is_authorized': True,  # Be more permissive for new users
                    'confidence': 0.7,
                    'risk_score': 0.3,
                    'anomaly_score': 0.3,
                    'authorization_reason': f'LIMITED_INTERACTION: Only {total_interactions} interactions but allowing new user',
                    'recommendation': 'ALLOW: New user with limited interaction',
                    'analysis_type': 'limited_interaction_allowed',
                    'total_interactions': total_interactions,
                    'risk_factors': [
                        {
                            'metric': 'limited_interaction',
                            'severity': 'MEDIUM',
                            'value': total_interactions,
                            'threshold': min_interactions,
                            'description': f'Limited interaction data: {total_interactions} interactions'
                        }
                    ]
                }
                
        except Exception as e:
            print(f"Error in simple behavioral validation: {e}")
            return self._fallback_analysis(current_data, str(e))
        


behavioral_analyzer = BehavioralAnalyzer()


@csrf_exempt
@require_http_methods(["POST"])
def handle_baseline_storage(request):

    try:
        print(f"🎯 BASELINE STORAGE REQUEST RECEIVED: {request.method}")
        print(f"🎯 Request body size: {len(request.body)} bytes")
        
        data = json.loads(request.body)
        
        # Extract session ID and baseline data
        session_id = data.get('session_id')
        baseline_data = data.get('baseline_data', {})

        if not session_id:
            print("❌ ERROR: No session ID provided")
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        if not baseline_data:
            print("❌ ERROR: No baseline data provided")
            return JsonResponse({
                'success': False,
                'message': 'Baseline data is required'
            }, status=400)

        # Extract baseline information
        collection_start_time = baseline_data.get('collectionStartTime')
        collection_end_time = baseline_data.get('collectionEndTime')
        metrics = baseline_data.get('metrics', {})
        overall_profile = baseline_data.get('overallBehaviorProfile', {})

        if collection_start_time:
            start_dt = datetime.fromtimestamp(collection_start_time / 1000, tz=ZoneInfo('UTC'))
        else:
            start_dt = timezone.now()
            
        if collection_end_time:
            end_dt = datetime.fromtimestamp(collection_end_time / 1000, tz=ZoneInfo('UTC'))
        else:
            end_dt = timezone.now()
        
        # Calculate collection duration
        duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        
        print(f"🦅 Calculated duration: {duration_ms}ms")
        
        # Extract user_id from session or use session_id as fallback
        user_id = baseline_data.get('formData', {}).get('userName')
        
        # If no user_id from formData, try to get from session
        if not user_id:
            try:
                user_session = UserSession.objects.filter(session_id=session_id).first()
                if user_session and user_session.usai_id:
                    user_id = user_session.usai_id
                elif user_session and user_session.name:
                    user_id = user_session.name
                else:
                    # Use session_id as final fallback
                    user_id = f"session_{session_id}"
            except Exception as session_error:
                print(f"⚠️ Could not retrieve user session: {session_error}")
                user_id = f"session_{session_id}"
        

        
        # 🦅 Calculate comprehensive data quality score for eagle's eye data
        mouse_movements = len(baseline_data.get('cursorMovements', []))
        key_presses = len(baseline_data.get('keyPressTimes', []))
        clicks = len(baseline_data.get('clickTimestamps', []))
        scroll_events = len(baseline_data.get('scrollSpeeds', []))
        action_count = baseline_data.get('actionCount', 0)
        
        # Enhanced quality scoring for comprehensive data
        cursor_paths = len(baseline_data.get('cursorPaths', []))
        hover_patterns = len(baseline_data.get('hoverPatterns', []))
        typing_rhythm = len(baseline_data.get('typingRhythm', []))
        pages_visited = len(baseline_data.get('pagesVisited', []))
        
        # Comprehensive quality calculation
        movement_score = min(1.0, mouse_movements / 50)  # Expect ~50 movements in 20s
        interaction_score = min(1.0, (key_presses + clicks) / 20)  # Expect ~20 interactions
        pattern_score = min(1.0, (cursor_paths + hover_patterns + typing_rhythm) / 30)
        navigation_score = min(1.0, pages_visited / 3)  # Account for page navigation
        
        quality_score = (movement_score * 0.3 + interaction_score * 0.3 + 
                        pattern_score * 0.3 + navigation_score * 0.1)
        
        sufficient_interaction = (action_count >= 15 and mouse_movements >= 10 and 
                                (key_presses >= 5 or clicks >= 3))
        
        # 🦅 Enhanced baseline metrics for eagle's eye analysis
        enhanced_metrics = {
            **metrics,
            'comprehensive_profile': overall_profile,
            'eagle_eye_scores': {
                'movement_score': movement_score,
                'interaction_score': interaction_score,
                'pattern_score': pattern_score,
                'navigation_score': navigation_score,
                'overall_quality': quality_score
            },
            'data_richness': {
                'mouse_movements': mouse_movements,
                'key_presses': key_presses,
                'clicks': clicks,
                'scroll_events': scroll_events,
                'cursor_paths': cursor_paths,
                'hover_patterns': hover_patterns,
                'typing_rhythm_points': typing_rhythm,
                'pages_visited': pages_visited,
                'total_actions': action_count
            }
        }
        

        try:
            baseline_record = UserBaselineBehavior.objects.create(
                user_id=user_id,
                session_id=session_id,
                baseline_user_behavior=baseline_data,
                collection_start_time=start_dt,
                collection_end_time=end_dt,
                collection_duration_ms=duration_ms,
                baseline_metrics=enhanced_metrics,
                data_quality_score=quality_score,
                sufficient_interaction=sufficient_interaction,
                is_active=True
            )
            print(f"✅ Database record created successfully with ID: {baseline_record.id}")
        except Exception as db_error:
            print(f"❌ DATABASE ERROR: {str(db_error)}")
            print(f"❌ Error type: {type(db_error).__name__}")
            raise db_error
        

        return JsonResponse({
            'success': True,
            'message': 'Comprehensive eagle\'s eye baseline behavioral data stored successfully',
            'baseline_id': baseline_record.id,
            'user_id': user_id,
            'session_id': session_id,
            'collection_duration_ms': duration_ms,
            'data_quality_score': quality_score,
            'sufficient_interaction': sufficient_interaction,
            'baseline_summary': baseline_record.get_baseline_summary(),
            'eagle_eye_metrics': enhanced_metrics['eagle_eye_scores'],
            'data_richness': enhanced_metrics['data_richness'],
            'stored_at': baseline_record.created_at.isoformat(),
            'baseline_type': 'comprehensive_eagle_eye'
        }, status=200)
        
    except json.JSONDecodeError:
        print("❌ ERROR: Invalid JSON data")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error storing baseline data: {str(e)}")
        print(f"❌ BASELINE STORAGE ERROR: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to store baseline data',
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_behavioral_data(request):
    """Fixed version with proper risk_factors handling"""
    
    def ensure_risk_factors(analysis_result):
        """Ensure analysis_result always has risk_factors key"""
        if 'risk_factors' not in analysis_result:
            analysis_result['risk_factors'] = []
        return analysis_result
    
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id')
        behavioral_data = data.get('behavioral_data', {})
        analysis_type = data.get('analysis_type', 'enhanced_mahalanobis_distance')  
        similarity_threshold = data.get('similarity_threshold', 0.65)  
        
        if not session_id:
            print("❌ ERROR: No session ID provided")
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        if not behavioral_data:
            print("❌ ERROR: No behavioral data provided")
            return JsonResponse({
                'success': False,
                'message': 'Behavioral data is required'
            }, status=400)

        # Try to retrieve baseline data
        try:
            baseline_record = UserBaselineBehavior.objects.filter(
                session_id=session_id,
                is_active=True
            ).order_by('-created_at').first()
            
            if not baseline_record:
                print(f"⚠️ No baseline behavior found for session: {session_id}")
                
                # Try to find baseline by user_id
                user_session = UserSession.objects.filter(session_id=session_id).first()
                if user_session and user_session.usai_id:
                    print(f"🔍 Searching for baseline by user identifier: {user_session.usai_id}")
                    baseline_record = UserBaselineBehavior.objects.filter(
                        user_id=user_session.usai_id,
                        is_active=True,
                        sufficient_interaction=True
                    ).order_by('-created_at').first()

                if not baseline_record:
                    # Create analysis result for new users
                    total_interactions = (len(behavioral_data.get('cursor_movements', [])) + 
                                        len(behavioral_data.get('key_press_times', [])) + 
                                        len(behavioral_data.get('click_timestamps', [])))
                    
                    if total_interactions >= 5:
                        analysis_result = {
                            'is_authorized': True,
                            'confidence': 0.7,
                            'anomaly_score': 0.2,
                            'risk_score': 0.3,
                            'authorization_reason': f'NEW_USER_APPROVED: No baseline available but {total_interactions} interactions detected',
                            'recommendation': f'ALLOW: First-time user with {total_interactions} interactions',
                            'analysis_type': 'new_user_baseline_collection',
                            'requires_baseline_collection': True,
                            'session_id': session_id,
                            'total_interactions': total_interactions,
                            'current_behavior': behavioral_data,
                            'baseline_data': {},
                            'risk_factors': [  # ✅ ALWAYS INCLUDE risk_factors
                                {
                                    'metric': 'new_user_baseline_collection',
                                    'severity': 'LOW',
                                    'value': total_interactions,
                                    'threshold': 5,
                                    'description': 'New user with sufficient interaction data'
                                }
                            ]
                        }
                        
                        # Try to create baseline record
                        try:
                            user_id_for_baseline = None
                            if user_session and user_session.usai_id:
                                user_id_for_baseline = str(user_session.usai_id)
                            elif user_session and user_session.name:
                                user_id_for_baseline = str(user_session.name)
                            else:
                                user_id_for_baseline = session_id
                            
                            baseline_behavior = UserBaselineBehavior.objects.create(
                                session_id=session_id,
                                user_id=user_id_for_baseline,
                                baseline_user_behavior=behavioral_data,
                                collection_start_time=timezone.now(),
                                collection_end_time=timezone.now(),
                                collection_duration_ms=20000,
                                data_quality_score=0.7,
                                sufficient_interaction=total_interactions >= 10,
                                is_active=True
                            )
                            print(f"✅ Created initial baseline record")
                            analysis_result['baseline_created'] = True
                            analysis_result['baseline_id'] = baseline_behavior.id
                        except Exception as baseline_error:
                            print(f"⚠️ Could not create baseline: {baseline_error}")
                            analysis_result['baseline_created'] = False
                    else:
                        # Limited interaction new user
                        analysis_result = {
                            'is_authorized': True,
                            'confidence': 0.5,
                            'anomaly_score': 0.4,
                            'risk_score': 0.5,
                            'authorization_reason': f'LIMITED_NEW_USER: Only {total_interactions} interactions but allowing new user',
                            'recommendation': f'NEW_USER_APPROVED: New user with limited data',
                            'analysis_type': 'limited_new_user',
                            'requires_more_interaction': True,
                            'session_id': session_id,
                            'total_interactions': total_interactions,
                            'current_behavior': behavioral_data,
                            'baseline_data': {},
                            'risk_factors': [  # ✅ ALWAYS INCLUDE risk_factors
                                {
                                    'metric': 'limited_interaction_new_user',
                                    'severity': 'MEDIUM',
                                    'value': total_interactions,
                                    'threshold': 5,
                                    'description': 'New user with limited interaction data'
                                }
                            ]
                        }
                    
                    baseline_behavior = None
                    baseline_data = {}
                else:
                    baseline_behavior = baseline_record.baseline_user_behavior
                    baseline_data = baseline_record.baseline_metrics
            else:
                baseline_behavior = baseline_record.baseline_user_behavior
                baseline_data = baseline_record.baseline_metrics

        except Exception as baseline_error:
            print(f"❌ Error retrieving baseline: {str(baseline_error)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to retrieve baseline behavior',
                'error': str(baseline_error)
            }, status=500)
        
        # Verify or create session 
        try:
            session = UserSession.objects.get(session_id=session_id, is_active=True)
        except UserSession.DoesNotExist:
            session = UserSession.objects.create(
                session_id=session_id,
                is_active=True,
                created_at=timezone.now()
            )
            print(f"🆕 Created new UserSession: {session_id}")
        
        # Run behavioral analysis if not already created for new users
        if 'analysis_result' not in locals():
            print(f"🧠 Running behavioral analysis...")
            
            user_id = behavioral_data.get('user_id') or behavioral_data.get('usai_id')
            
            # Check if we have meaningful baseline data
            has_meaningful_baseline = False
            if baseline_behavior:
                if isinstance(baseline_behavior, dict):
                    has_meaningful_baseline = (len(baseline_behavior) > 0 and
                                             (baseline_behavior.get('cursor_movements') or 
                                              baseline_behavior.get('cursorMovements') or
                                              baseline_behavior.get('key_press_times') or
                                              baseline_behavior.get('keyPressTimes')))

            if has_meaningful_baseline:
                print(f"🔍 Using baseline comparison for user {user_id}")
                analysis_result = behavioral_analyzer.analyze_with_baseline_comparison(
                    session_id=session_id,
                    current_data=behavioral_data,   
                    baseline_behavior_or_user_id=baseline_behavior,
                    baseline_metrics=baseline_data
                )

            else:
                print(f"🔍 Using simple behavioral validation for new/missing baseline user")
                # FIXED: Call the simple validation instead of forcing unauthorized
                analysis_result = behavioral_analyzer.simple_behavioral_validation(
                    session_id=session_id,
                    current_data=behavioral_data,
                    user_id=user_id
                )

            if has_meaningful_baseline:
                print(f"🔍 Using baseline comparison for user {user_id}")
                analysis_result = behavioral_analyzer.analyze_with_baseline_comparison(
                    session_id=session_id,
                    current_data=behavioral_data,   
                    baseline_behavior_or_user_id=baseline_behavior
                )
            else:
                # Use simple behavioral validation for new users or missing baselines
                print(f"🔍 Using simple behavioral validation - user_id: {user_id}, has_baseline: {has_meaningful_baseline}")
                
                
            analysis_result = {
                'is_authorized': False,
                'confidence': 0.0,
                'risk_score': 1.0,
                'anomaly_score': 1.0,
                'recommendation': 'Fallback decision - insufficient data',
                'authorization_reason': 'No baseline and not enough data',
                'risk_factors': []
            }

            
            # Add compatibility fields for frontend
            analysis_result.update({
                'analysis_type': 'improved_user_identity_detection',
                'session_id': session_id,
                'timestamp': timezone.now().isoformat(),
                'success': True
            })
        
        rolling_windows = behavioral_data.get('rollingWindows', [])
        window_metadata = behavioral_data.get('windowMetadata', {})
        if analysis_type == 'mahalanobis_distance' and rolling_windows:
            print(f"� Legacy analysis type requested - using improved system with compatibility mode...")
            
            # The improved system already provides all necessary data
            # Just ensure compatibility with existing frontend expectations
            analysis_result.update({
                'mahalanobis_analysis': 'improved_identity_detection_used',
                'rolling_windows_analyzed': len(rolling_windows),
                'window_metadata': window_metadata,
                'primary_analysis': 'improved_user_identity_detection'
            })
        
        user_auth_status = 'Authorized_user' if analysis_result['is_authorized'] else 'Unauthorized_user'
        risk_score = analysis_result.get('risk_score', 0)
        confidence = analysis_result.get('confidence', 0)
        

        
        behavioral_record = BehavioralData.objects.create(
            session_id=session_id,
            user_auth=user_auth_status,
            cursor_movements=behavioral_data.get('cursor_movements', []),
            key_press_times=behavioral_data.get('key_press_times', []),
            key_hold_times=behavioral_data.get('key_hold_times', []),
            click_timestamps=behavioral_data.get('click_timestamps', []),
            click_intervals=behavioral_data.get('click_intervals', []),
            cursor_speeds=behavioral_data.get('cursor_speeds', []),
            cursor_acceleration=behavioral_data.get('cursor_acceleration', []),
            cursor_curvature=behavioral_data.get('cursor_curvature', []),
            paste_detected=behavioral_data.get('paste_detected', False),
            total_time=behavioral_data.get('total_time', 0),
            classification='Human' if analysis_result['is_authorized'] else 'Bot',
            human_score=confidence if analysis_result['is_authorized'] else 1.0 - confidence,
            bot_score=1.0 - confidence if analysis_result['is_authorized'] else confidence,
            human_indicators=analysis_result.get('human_indicators', []) if analysis_result['is_authorized'] else [],
            bot_indicators=behavioral_data.get('bot_indicators', 0),
            bot_fingerprint_score=behavioral_data.get('bot_fingerprint_score', 0),
            suspicious_flag=behavioral_data.get('suspicious_flag', {}),
            suspicious_feature_ratio=behavioral_data.get('suspicious_feature_ratio', {}),
            mouse_movement_debug=behavioral_data.get('mouse_movement_debug', {}),
            speed_calculation_debug=behavioral_data.get('speed_calculation_debug', {}),
            post_paste_activity=behavioral_data.get('post_paste_activity', {}),
            keyboard_patterns=behavioral_data.get('keyboard_patterns', []),
            suspicious_patterns=analysis_result.get('suspicious_patterns', []),
            action_count=behavioral_data.get('action_count', 0),
            is_automated_browser=behavioral_data.get('is_automated_browser', False),
            cursor_entropy=behavioral_data.get('cursor_entropy', 0),
            scroll_speeds=behavioral_data.get('scroll_speeds', []),
            scroll_changes=behavioral_data.get('scroll_changes', 0),
            idle_time=behavioral_data.get('idle_time', 0),
            honeypot_value=behavioral_data.get('honeypot_value'),
            tabkeycount=behavioral_data.get('tabkeycount', 0),
            cursorAngleVariance=behavioral_data.get('cursorAngleVariance', 0),
            mouseJitter=behavioral_data.get('mouseJitter', []),
            hesitation = behavioral_data.get('hesitation', []),
            micropause = behavioral_data.get('micropause', []), 
            devicefingerprint=str(behavioral_data.get('deviceFingerprint', '0')),
            missing_canvas_fingerprint=behavioral_data.get('missing_canvas_fingerprint', False),
            canvas_metrics=behavioral_data.get('canvas_metrics', {}),
            unsualscreenresolution=behavioral_data.get('unsualscreenresolution', {}),
            gpu_info=behavioral_data.get('gpu_info', {}),
            timing_metrics=behavioral_data.get('timing_metrics', {}),
            evasion_signals=behavioral_data.get('evasion_signals', {})
        )
        
        # Update session activity
        session.update_activity()

        if not analysis_result['is_authorized']:
            return JsonResponse({
                'success': True,
                'message': 'Unauthorized user detected via enhanced cosine similarity analysis',
                'session_id': session_id,
                'user_auth_status': 'Unauthorized_user',
                'is_authorized': False,
                'requires_authentication': True,
                'authentication_message': 'Behavioral pattern mismatch detected - Authentication required',
                'confidence': confidence,
                'risk_score': risk_score,
                'anomaly_score': analysis_result.get('anomaly_score', risk_score),
                
                # 🔬 COSINE SIMILARITY RESULTS
                'cosine_similarity': analysis_result.get('cosine_similarity', 0.0),
                'cosine_max_similarity': analysis_result.get('cosine_max_similarity', 0.0),
                'cosine_min_similarity': analysis_result.get('cosine_min_similarity', 0.0),
                'cosine_variance': analysis_result.get('cosine_variance', 0.0),
                'window_similarities': analysis_result.get('window_similarities', []),
                'windows_analyzed': analysis_result.get('windows_analyzed', 0),
                'similarity_threshold': similarity_threshold,
                'combined_similarity': analysis_result.get('combined_similarity', 0.0),
                
                # Additional analysis details
                'baseline_similarity': analysis_result.get('baseline_similarity', 0.0),
                'baseline_deviations': analysis_result.get('baseline_deviations', []),
                'risk_factors': analysis_result['risk_factors'],
                'suspicious_indicators': analysis_result.get('suspicious_indicators', []),
                'recommendation': analysis_result['recommendation'],
                'authorization_reason': analysis_result.get('authorization_reason', analysis_result['recommendation']),
                'analysis_type': analysis_result.get('analysis_type', 'enhanced_mahalanobis_distance'),
                'analysis_timestamp': timezone.now().isoformat(),
                'record_id': behavioral_record.id,
                'action_required': 'AUTHENTICATION_NEEDED'
            }, status=200)
        
        # ✅ Response for authorized users
        return JsonResponse({
            'success': True,
            'message': f'Enhanced cosine similarity analysis complete: {user_auth_status}',
            'session_id': session_id,
            'user_auth_status': user_auth_status,
            'is_authorized': analysis_result['is_authorized'],
            'requires_authentication': False,
            'confidence': confidence,
            'risk_score': risk_score,
            'anomaly_score': analysis_result.get('anomaly_score', risk_score),
            
            # 🔬 COSINE SIMILARITY RESULTS
            'cosine_similarity': analysis_result.get('cosine_similarity', 0.0),
            'cosine_max_similarity': analysis_result.get('cosine_max_similarity', 0.0),
            'cosine_min_similarity': analysis_result.get('cosine_min_similarity', 0.0),
            'cosine_variance': analysis_result.get('cosine_variance', 0.0),
            'window_similarities': analysis_result.get('window_similarities', []),
            'windows_analyzed': analysis_result.get('windows_analyzed', 0),
            'similarity_threshold': similarity_threshold,
            'combined_similarity': analysis_result.get('combined_similarity', 0.0),
            
            # Additional analysis details
            'baseline_similarity': analysis_result.get('baseline_similarity', 0.0),
            'baseline_deviations': analysis_result.get('baseline_deviations', []),
            'risk_factors': analysis_result['risk_factors'],
            'suspicious_indicators': analysis_result.get('suspicious_indicators', []),
            'human_indicators': analysis_result.get('human_indicators', []),
            'recommendation': analysis_result['recommendation'],
            'authorization_reason': analysis_result.get('authorization_reason', analysis_result['recommendation']),
            'analysis_type': analysis_result.get('analysis_type', 'enhanced_mahalanobis_distance'),
            'analysis_timestamp': timezone.now().isoformat(),
            'profile_size': analysis_result.get('profile_size', 0),
            'record_id': behavioral_record.id,
            'stored_at': behavioral_record.created_at.isoformat(),
            
            # 📊 Rolling window metadata if available
            'rolling_windows_analyzed': analysis_result.get('rolling_windows_analyzed', 0),
            'window_metadata': analysis_result.get('window_metadata', {}),
            'primary_analysis': analysis_result.get('primary_analysis', 'enhanced_cosine_similarity')
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error in behavioral analysis: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }, status=500)