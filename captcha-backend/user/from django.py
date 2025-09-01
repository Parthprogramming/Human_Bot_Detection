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
        """Enhanced time-series analysis with better tolerance for legitimate users"""
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
                return 0.75  # More generous neutral score when no valid comparisons
            
            average_similarity = total_similarity / valid_comparisons
            
            # Apply more generous minimum threshold - humans can vary significantly
            return max(0.55, min(1.0, average_similarity))
            
        except Exception as e:
            print(f"Error in time-series analysis: {e}")
            return 0.75  # More generous fallback
    
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
        """Compare statistical properties with more realistic tolerances"""
        try:
            if len(current_features) < 2 or len(baseline_features) < 2:
                return None
            
            current_mean = np.mean(current_features)
            baseline_mean = np.mean(baseline_features)
            current_std = np.std(current_features)
            baseline_std = np.std(baseline_features)
            
            # Much more lenient difference calculations
            mean_diff = abs(current_mean - baseline_mean) / (abs(baseline_mean) + 200)  # Increased offset
            std_diff = abs(current_std - baseline_std) / (baseline_std + 100)  # Increased offset
            
            # Convert to similarity with very generous scaling
            mean_similarity = max(0.3, 1.0 - mean_diff * 0.3)  # Reduced penalty further
            std_similarity = max(0.3, 1.0 - std_diff * 0.2)   # Reduced penalty further
            
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
                return 0.7  # More generous neutral for insufficient data
            
            # Normalize intervals to compare patterns rather than absolute timing
            current_norm = self._normalize_intervals(current_intervals)
            baseline_norm = self._normalize_intervals(baseline_intervals)
            
            if not current_norm or not baseline_norm:
                return 0.7
            
            # Calculate correlation with more generous interpretation
            min_len = min(len(current_norm), len(baseline_norm), 20)  # Increased comparison limit
            current_sample = current_norm[:min_len]
            baseline_sample = baseline_norm[:min_len]
            
            correlation = np.corrcoef(current_sample, baseline_sample)[0, 1]
            
            if math.isnan(correlation):
                return 0.7
            
            # Convert correlation to similarity with very generous scaling
            similarity = (abs(correlation) + 0.5) / 1.5  # Significantly boost correlation scores
            return max(0.4, min(1.0, similarity))
            
        except Exception as e:
            print(f"Error comparing timing rhythms: {e}")
            return None
        
    def _compare_value_ranges(self, current_features, baseline_features):
        """Compare value ranges with more tolerant approach"""
        try:
            current_min, current_max = min(current_features), max(current_features)
            baseline_min, baseline_max = min(baseline_features), max(baseline_features)
            
            current_range = current_max - current_min
            baseline_range = baseline_max - baseline_min
            
            if baseline_range == 0:
                return 0.8  # More generous default for zero range
            
            # Compare ranges with very generous tolerance
            range_diff = abs(current_range - baseline_range) / baseline_range
            range_similarity = max(0.3, 1.0 - range_diff * 0.2)  # Very generous
            
            # Compare overlap
            overlap_start = max(current_min, baseline_min)
            overlap_end = min(current_max, baseline_max)
            
            if overlap_end > overlap_start:
                overlap = overlap_end - overlap_start
                total_span = max(current_max, baseline_max) - min(current_min, baseline_min)
                overlap_similarity = overlap / total_span if total_span > 0 else 0.8
            else:
                overlap_similarity = 0.5  # Reasonable score even for no overlap
            
            return (range_similarity + overlap_similarity) / 2
            
        except Exception as e:
            return None

    def _calculate_time_series_similarity(self, current_values, baseline_values):
        """More robust and tolerant similarity calculation"""
        try:
            if len(current_values) < 2 or len(baseline_values) < 2:
                return 0.7  # More generous neutral for insufficient data
            
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
        """Enhanced statistical analysis with better tolerance for human variation"""
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
                return 0.7  # More generous neutral score for insufficient data
            
            current_vec = np.array([pair[0] for pair in valid_pairs])
            baseline_vec = np.array([pair[1] for pair in valid_pairs])
            
            # Improved similarity calculation with better tolerance
            try:
                # Normalize to prevent scale issues
                current_norm = current_vec / (np.linalg.norm(current_vec) + 1e-6)
                baseline_norm = baseline_vec / (np.linalg.norm(baseline_vec) + 1e-6)

                # Cosine similarity
                cosine_sim = np.dot(current_norm, baseline_norm)
                cosine_sim = max(-1, min(1, cosine_sim))
                similarity = (cosine_sim + 1) / 2

                # Apply minimum threshold that's reasonable for human variation
                return max(0.4, min(1.0, similarity))
                
            except Exception:
                # Fallback to element-wise comparison with more tolerance
                relative_diffs = np.abs(current_vec - baseline_vec) / (np.abs(baseline_vec) + 1e-6)
                avg_diff = np.mean(relative_diffs)
                similarity = max(0.4, 1.0 - min(1.0, avg_diff * 0.5))  # Reduced penalty
                return similarity

        except Exception as e:
            print(f"Error in statistical analysis: {e}")
            return 0.7  # More generous fallback
        
    def _analyze_device_fingerprints(self, current_data, baseline_data):
        """Analyze device/environment fingerprints with tolerance for minor changes"""
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
                        # Be more tolerant of minor device fingerprint changes
                        total_score += 0.6
                elif metric == 'gpu_info':
                    current_vendor = str(current_value.get('vendor', '')).lower()
                    baseline_vendor = str(baseline_value.get('vendor', '')).lower()
                    
                    if current_vendor == baseline_vendor:
                        total_score += 1.0
                    elif current_vendor and baseline_vendor:
                        total_score += 0.8  # More generous for similar GPUs
                    else:
                        total_score += 0.5  # More generous default
                
                valid_metrics += 1
            
            if valid_metrics == 0:
                return 0.7  # More generous when no metrics available
            
            return total_score / valid_metrics
            
        except Exception as e:
            print(f"Error in device analysis: {e}")
            return 0.7  # More generous fallback
        
    def _analyze_boolean_signals(self, current_data, baseline_data):
        """Much more lenient boolean signal analysis to avoid false positives"""
        try:
            boolean_metrics = [
                'paste_detected', 'is_automated_browser', 'missing_canvas_fingerprint', 
                'suspicious_flag', 'evasion_signals'
            ]
            
            total_score = 1.0
            
            for metric in boolean_metrics:
                current_value = current_data.get(metric, False)
                
                # Much more lenient penalties - these are often false positives
                if metric == 'paste_detected' and current_value:
                    total_score -= 0.02  # Minimal penalty - paste is common
                elif metric == 'is_automated_browser' and current_value:
                    total_score -= 0.15  # Reduced penalty
                elif metric == 'missing_canvas_fingerprint' and current_value:
                    total_score -= 0.05  # Very small penalty
                elif metric == 'suspicious_flag' and current_value:
                    total_score -= 0.08  # Reduced penalty
                elif metric == 'evasion_signals' and current_value:
                    evasion_data = current_data.get('evasion_signals', {})
                    if isinstance(evasion_data, dict):
                        if evasion_data.get('webdriver', False):
                            total_score -= 0.2  # Reduced from 0.6
                        if evasion_data.get('languages_spoofed', False):
                            total_score -= 0.05  # Minimal penalty
                        if evasion_data.get('plugins_spoofed', False):
                            total_score -= 0.05  # Minimal penalty
            
            return max(0.5, total_score)  # Higher minimum score
            
        except Exception as e:
            print(f"Error in boolean analysis: {e}")
            return 0.75  # More generous fallback

    def _check_immediate_red_flags(self, current_data):
        """Check for critical security violations only"""
        try:
            # Check honeypot fields
            honeypot_value = current_data.get('honeypot_value', '')
            if honeypot_value and honeypot_value.strip():
                return {
                    'blocked': True,
                    'reason': 'Honeypot field filled - likely automated attack'
                }

            # Only block on very clear automation signals
            evasion_signals = current_data.get('evasion_signals', {})
            if isinstance(evasion_signals, dict):
                if evasion_signals.get('webdriver', False) and evasion_signals.get('headless_mode', False):
                    return {
                        'blocked': True,
                        'reason': 'Multiple automation signals detected'
                    }

            # Check for extremely suspicious GPU vendors only
            gpu_info = current_data.get('gpu_info', {})
            gpu_vendor = str(gpu_info.get('vendor', '')).lower()
            highly_suspicious_vendors = ['llvmpipe', 'swiftshader']  # Reduced list
            if any(vendor in gpu_vendor for vendor in highly_suspicious_vendors):
                return {
                    'blocked': True,
                    'reason': 'Highly suspicious GPU vendor detected'
                }

            return {'blocked': False, 'reason': None}

        except Exception as e:
            print(f"Error checking red flags: {e}")
            return {'blocked': False, 'reason': None}
    
    def _fuse_domain_scores(self, time_series_score, statistical_score, boolean_score, device_score):
        """Enhanced scoring fusion with realistic thresholds and better weighting"""
        try:
            print(f"   Domain scores - Time: {time_series_score:.3f}, Statistical: {statistical_score:.3f}")
            print(f"   Domain scores - Boolean: {boolean_score:.3f}, Device: {device_score:.3f}")

            # More balanced and realistic weighting that favors behavioral patterns
            weights = {
                'time_series': 0.40,    # Primary behavioral indicator (increased)
                'statistical': 0.35,    # Secondary behavioral indicator  
                'boolean': 0.15,        # Security flags (reduced impact)
                'device': 0.10          # Environment consistency (minimal impact)
            }

            # Apply realistic minimum floors - legitimate users shouldn't fail on single domain
            time_series_score = max(0.45, time_series_score)   # Higher floor
            statistical_score = max(0.45, statistical_score)    # Higher floor
            boolean_score = max(0.60, boolean_score)            # Much higher floor for security
            device_score = max(0.50, device_score)              # Reasonable floor

            final_score = (
                weights['time_series'] * time_series_score +
                weights['statistical'] * statistical_score +
                weights['boolean'] * boolean_score +
                weights['device'] * device_score
            )

            # Ensure reasonable bounds with very generous interpretation
            final_score = max(0.4, min(1.0, final_score))

            print(f"   Final score: {final_score:.3f}")
            return final_score

        except Exception as e:
            print(f"Error in score fusion: {e}")
            return 0.75  # More generous fallback
    
    def _compare_metric_arrays(self, current_array, baseline_array):
        """Compare two arrays of metrics with better tolerance"""
        try:
            if not current_array or not baseline_array:
                return 0.6
            
            # More tolerant length comparison
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
                        # More tolerant value comparison
                        mean_diff = abs(current_mean - baseline_mean)
                        tolerance = max(abs(baseline_mean) * 0.5, 50)  # 50% tolerance or minimum 50
                        value_similarity = max(0.3, 1.0 - (mean_diff / tolerance))
                        return (length_similarity + value_similarity) / 2
                except:
                    pass
            
            return length_similarity
            
        except Exception as e:
            print(f"Error comparing metric arrays: {e}")
            return 0.6

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
        """Enhanced fallback analysis that's more permissive for legitimate users"""
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
            
            # Much more permissive fallback - only block clear automation
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
            print(f"Session: {session_id}")

            baseline_data = None
            user_id = None

            # Check if baseline_behavior_or_user_id is a user_id string to retrieve from database
            if isinstance(baseline_behavior_or_user_id, str):
                user_id = baseline_behavior_or_user_id
                print(f"Retrieving baseline for user: {user_id}")

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
                        print(f"Retrieved baseline for user {user_id}")
                    else:
                        print(f"No baseline found for user {user_id} - using permissive fallback")

                except Exception as e:
                    print(f"Database error retrieving baseline for {user_id}: {e}")
                    return {
                        'is_authorized': True,  # Fail open on database error
                        'confidence': 0.7,
                        'mahalanobis_distance': 0.0,
                        'standard_deviations': 0.0,
                        'authorization_reason': f'DATABASE_FALLBACK: Database error occurred but allowing user access - {str(e)}',
                        'analysis_type': 'database_error_fallback',
                        'recommendation': 'ALLOW: Database error - using permissive fallback',
                        'risk_factors': []
                    }
            else:
                # Use provided baseline data directly (legacy mode)
                baseline_data = baseline_behavior_or_user_id
                print(f"Using provided baseline data directly")

            if not baseline_data:
                return {
                    'is_authorized': True,  # Be permissive when no baseline
                    'confidence': 0.7,
                    'mahalanobis_distance': 0.0,
                    'standard_deviations': 0.0,
                    'authorization_reason': 'MISSING_BASELINE: No baseline data available - using permissive authorization',
                    'analysis_type': 'missing_baseline_fallback',
                    'recommendation': 'ALLOW: Missing baseline - collecting data for future analysis',
                    'risk_factors': []
                }

            # Check for immediate red flags (honeypot, evasion)
            immediate_red_flags = self._check_immediate_red_flags(current_data)
            if immediate_red_flags['blocked']:
                return {
                    'is_authorized': False,
                    'confidence': 0.95,
                    'authorization_reason': f'IMMEDIATE_BLOCK: {immediate_red_flags["reason"]}',
                    'analysis_type': 'immediate_red_flag',
                    'recommendation': 'BLOCK: Critical security violation detected',
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

            # Run comprehensive analysis
            time_series_score = self._analyze_time_series_metrics(current_data, baseline_data)
            statistical_score = self._analyze_statistical_metrics(current_data, baseline_data)
            boolean_score = self._analyze_boolean_signals(current_data, baseline_data)
            device_score = self._analyze_device_fingerprints(current_data, baseline_data)

            # Fusion across all domains
            print(f"Fusing scores across all domains...")
            final_score = self._fuse_domain_scores(time_series_score, statistical_score, boolean_score, device_score)
            print(f"   Final fused score: {final_score:.3f}")

            # FINAL AUTHORIZATION DECISION - More permissive threshold
            authorization_threshold = 0.35  # Lowered from 0.45 - more permissive
            is_authorized = final_score >= authorization_threshold
            confidence = final_score

            # Generate risk factors based on analysis
            risk_factors = []

            if time_series_score < 0.4:
                risk_factors.append({
                    'metric': 'time_series_similarity',
                    'severity': 'HIGH' if time_series_score < 0.2 else 'MEDIUM',
                    'value': time_series_score,
                    'threshold': 0.4,
                    'description': f'Time-series behavioral patterns show low similarity: {time_series_score:.3f}'
                })

            if statistical_score < 0.4:
                risk_factors.append({
                    'metric': 'statistical_similarity',
                    'severity': 'HIGH' if statistical_score < 0.2 else 'MEDIUM',
                    'value': statistical_score,
                    'threshold': 0.4,
                    'description': f'Statistical behavioral metrics show low similarity: {statistical_score:.3f}'
                })

            if boolean_score < 0.6:
                risk_factors.append({
                    'metric': 'boolean_signals',
                    'severity': 'HIGH' if boolean_score < 0.4 else 'MEDIUM',
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

            # Comprehensive analysis result
            analysis_result = {
                'is_authorized': is_authorized,
                'confidence': confidence,
                'final_score': final_score,
                'authorization_reason': f'COMPREHENSIVE_ANALYSIS: Final score {final_score:.3f} {"≥" if is_authorized else "<"} {authorization_threshold} threshold',
                'analysis_type': 'comprehensive_multi_domain',
                'risk_factors': risk_factors,

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

            print(f"FINAL DECISION: {'AUTHORIZED' if is_authorized else 'UNAUTHORIZED'} (Score: {final_score:.3f})")
            return analysis_result

        except Exception as e:
            print(f"CRITICAL ERROR in comprehensive behavioral analysis: {e}")
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
                'severity': 'LOW',  # Reduced severity
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
        """Enhanced simple validation for new users with better tolerance"""
        try:
            print(f"Running simple behavioral validation for session: {session_id}")
            
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
            
            # Very permissive interaction threshold check
            min_interactions = 2  # Lowered even further
            
            if total_interactions >= min_interactions:
                # Check for obvious automation signals
                evasion_signals = current_data.get('evasion_signals', {})
                automation_signals = sum(1 for v in evasion_signals.values() if v) if isinstance(evasion_signals, dict) else 0
                
                # Check for paste detection and other suspicious flags
                paste_detected = current_data.get('paste_detected', False)
                is_automated = current_data.get('is_automated_browser', False)
                
                # Calculate simple risk score - more permissive
                risk_score = 0.05  # Lower base risk
                
                if automation_signals > 0:
                    risk_score += 0.15 * min(automation_signals, 3)  # Reduced penalty
                if paste_detected:
                    risk_score += 0.05  # Minimal penalty for paste
                if is_automated:
                    risk_score += 0.25  # Reduced penalty
                
                risk_score = min(risk_score, 0.8)
                confidence = 1.0 - risk_score
                
                # Much more lenient decision for new users
                is_authorized = risk_score < 0.7  # Allow up to high risk for new users
                
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
                # Very limited interaction - still allow for new users
                return {
                    'is_authorized': True,  # Very permissive for new users
                    'confidence': 0.7,
                    'risk_score': 0.3,
                    'anomaly_score': 0.3,
                    'authorization_reason': f'LIMITED_INTERACTION: Only {total_interactions} interactions but allowing new user',
                    'recommendation': 'ALLOW: New user with minimal interaction',
                    'analysis_type': 'limited_interaction_allowed',
                    'total_interactions': total_interactions,
                    'risk_factors': [
                        {
                            'metric': 'limited_interaction_new_user',
                            'severity': 'LOW',  # Reduced severity
                            'value': total_interactions,
                            'threshold': min_interactions,
                            'description': f'New user with limited interaction data: {total_interactions} interactions'
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
        print(f"BASELINE STORAGE REQUEST RECEIVED: {request.method}")
        print(f"Request body size: {len(request.body)} bytes")
        
        data = json.loads(request.body)
        
        # Extract session ID and baseline data
        session_id = data.get('session_id')
        baseline_data = data.get('baseline_data', {})

        if not session_id:
            print("ERROR: No session ID provided")
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        if not baseline_data:
            print("ERROR: No baseline data provided")
            return JsonResponse({
                'success': False,
                'message': 'Baseline data is required'
            }, status=400)

        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)