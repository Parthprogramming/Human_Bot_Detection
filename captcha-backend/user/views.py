from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, UserSession, SignInAttempt, SignUpAttempt, BehavioralData
import json
import uuid
import logging
import math
import statistics
from datetime import datetime, timedelta
import threading
import time

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
        
        # Simply store the name and USAI ID in SignUpAttempt table
        signup_attempt = SignUpAttempt.objects.create(
            session_id=session_id,
            name=name,
            usai_id=usai_id,
            success=True,
        )
        
        # Also create a UserSession entry for the signup
        user_session = UserSession.objects.create(
            session_id=session_id,
            name=name,
            usai_id=usai_id,
            session_type='SIGNUP'
        )
        
        print(f"DEBUG: Successfully created signup attempt with ID: {signup_attempt.id}")  # Debug log
        print(f"DEBUG: Successfully created user session with ID: {user_session.id}")  # Debug log
        logger.info(f"User {name} successfully signed up with USAI ID {usai_id}")
        
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
        # Parse JSON data from request
        data = json.loads(request.body)
        
        # Extract required fields
        usai_id = data.get('usai_id', '').strip()
        password = data.get('password', '')
        username = data.get('username', usai_id)  # Allow login with username or usai_id
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get client information
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Validation
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
        
        # Try to find user by USAI ID first
        user = None
        user_profile = None
        name = None
        
        try:
            user_profile = UserProfile.objects.get(usai_id=usai_id)
            user = user_profile.user
            name = f"{user.first_name} {user.last_name}".strip() or user.username
        except UserProfile.DoesNotExist:
            # If not found by USAI ID, try by username
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
        
        # Authenticate user
        authenticated_user = authenticate(request, username=user.username, password=password)
        
        if authenticated_user is not None:
            # Login successful
            login(request, authenticated_user)
            
            # Create user session
            user_session = UserSession.objects.create(
                session_id=session_id,
                user=authenticated_user,
                name=name,
                usai_id=usai_id,
                session_type='SIGNIN',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log successful attempt
            SignInAttempt.objects.create(
                session_id=session_id,
                name=name,
                usai_id=usai_id,
                user=authenticated_user,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"User {authenticated_user.username} successfully signed in with USAI ID {usai_id}")
            
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
            # Authentication failed
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


@require_http_methods(["GET"])
def check_session(request, session_id):
    """
    Check if a session is still active
    """
    try:
        session = UserSession.objects.get(session_id=session_id, is_active=True)
        
        if session.is_session_expired():
            session.is_active = False
            session.save()
            
            return JsonResponse({
                'success': False,
                'message': 'Session expired'
            }, status=401)
        
        # Update last activity
        session.update_activity()
        
        return JsonResponse({
            'success': True,
            'session_id': session.session_id,
            'user_id': session.user.id if session.user else None,
            'name': session.name,
            'usai_id': session.usai_id,
            'session_type': session.session_type
        }, status=200)
        
    except UserSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Session not found'
        }, status=404)


class BehavioralAnalyzer:
    """
    Advanced behavioral analysis engine for real-time user authentication
    """
    
    def __init__(self):
        self.authorized_profiles = {}  # Cache for authorized user behavioral profiles
        self.real_time_sessions = {}   # Track real-time behavioral data
        
    def calculate_behavioral_metrics(self, behavioral_data):
        """
        Calculate advanced behavioral metrics from raw data
        """
        metrics = {}
        
        try:
            # Cursor movement analysis
            cursor_movements = behavioral_data.get('cursor_movements', [])
            if cursor_movements:
                speeds = []
                accelerations = []
                angles = []
                
                for i in range(1, len(cursor_movements)):
                    prev = cursor_movements[i-1]
                    curr = cursor_movements[i]
                    
                    # Calculate speed
                    dx = curr.get('x', 0) - prev.get('x', 0)
                    dy = curr.get('y', 0) - prev.get('y', 0)
                    dt = (curr.get('timestamp', 0) - prev.get('timestamp', 0)) / 1000.0
                    
                    if dt > 0:
                        distance = math.sqrt(dx**2 + dy**2)
                        speed = distance / dt
                        speeds.append(speed)
                        
                        # Calculate angle
                        angle = math.atan2(dy, dx)
                        angles.append(angle)
                
                # Calculate accelerations
                for i in range(1, len(speeds)):
                    accel = speeds[i] - speeds[i-1]
                    accelerations.append(accel)
                
                metrics['avg_speed'] = statistics.mean(speeds) if speeds else 0
                metrics['speed_variance'] = statistics.variance(speeds) if len(speeds) > 1 else 0
                metrics['avg_acceleration'] = statistics.mean(accelerations) if accelerations else 0
                metrics['acceleration_variance'] = statistics.variance(accelerations) if len(accelerations) > 1 else 0
                metrics['angle_variance'] = statistics.variance(angles) if len(angles) > 1 else 0
                metrics['movement_entropy'] = self.calculate_entropy(angles) if angles else 0
            
            # Keystroke dynamics
            key_press_times = behavioral_data.get('key_press_times', [])
            key_hold_times = behavioral_data.get('key_hold_times', [])
            
            if key_press_times:
                intervals = []
                for i in range(1, len(key_press_times)):
                    interval = key_press_times[i] - key_press_times[i-1]
                    intervals.append(interval)
                
                metrics['avg_keystroke_interval'] = statistics.mean(intervals) if intervals else 0
                metrics['keystroke_variance'] = statistics.variance(intervals) if len(intervals) > 1 else 0
            
            if key_hold_times:
                metrics['avg_key_hold_time'] = statistics.mean(key_hold_times)
                metrics['key_hold_variance'] = statistics.variance(key_hold_times) if len(key_hold_times) > 1 else 0
            
            # Click patterns
            click_timestamps = behavioral_data.get('click_timestamps', [])
            if click_timestamps:
                click_intervals = []
                for i in range(1, len(click_timestamps)):
                    interval = click_timestamps[i] - click_timestamps[i-1]
                    click_intervals.append(interval)
                
                metrics['avg_click_interval'] = statistics.mean(click_intervals) if click_intervals else 0
                metrics['click_variance'] = statistics.variance(click_intervals) if len(click_intervals) > 1 else 0
            
            # Advanced metrics
            metrics['cursor_entropy'] = behavioral_data.get('cursor_entropy', 0)
            metrics['bot_fingerprint_score'] = behavioral_data.get('bot_fingerprint_score', 0)
            metrics['suspicious_feature_ratio'] = behavioral_data.get('suspicious_feature_ratio', 0)
            metrics['idle_time'] = behavioral_data.get('idle_time', 0)
            metrics['action_count'] = behavioral_data.get('action_count', 0)
            
        except Exception as e:
            logger.error(f"Error calculating behavioral metrics: {str(e)}")
            
        return metrics
    
    def calculate_entropy(self, values):
        """
        Calculate Shannon entropy of a list of values
        """
        if not values:
            return 0
        
        # Discretize continuous values into bins
        bins = 10
        min_val = min(values)
        max_val = max(values)
        
        if min_val == max_val:
            return 0
        
        bin_size = (max_val - min_val) / bins
        counts = [0] * bins
        
        for value in values:
            bin_index = min(int((value - min_val) / bin_size), bins - 1)
            counts[bin_index] += 1
        
        total = len(values)
        entropy = 0
        
        for count in counts:
            if count > 0:
                probability = count / total
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def build_user_profile(self, session_id):
        """
        Build a behavioral profile for an authorized user
        """
        try:
            # Get all behavioral data for this session from authorized user
            behavioral_records = BehavioralData.objects.filter(
                session_id=session_id,
                user_auth='Authorized_user'
            ).order_by('-created_at')[:50]  # Last 50 records
            
            if not behavioral_records:
                return None
            
            profile_metrics = []
            for record in behavioral_records:
                behavioral_data = {
                    'cursor_movements': record.cursor_movements,
                    'key_press_times': record.key_press_times,
                    'key_hold_times': record.key_hold_times,
                    'click_timestamps': record.click_timestamps,
                    'cursor_entropy': record.cursor_entropy,
                    'bot_fingerprint_score': record.bot_fingerprint_score,
                    'suspicious_feature_ratio': record.suspicious_feature_ratio,
                    'idle_time': record.idle_time,
                    'action_count': record.action_count,
                }
                
                metrics = self.calculate_behavioral_metrics(behavioral_data)
                profile_metrics.append(metrics)
            
            # Calculate profile statistics
            profile = {}
            if profile_metrics:
                for key in profile_metrics[0].keys():
                    values = [m[key] for m in profile_metrics if key in m and m[key] is not None]
                    if values:
                        profile[f'{key}_mean'] = statistics.mean(values)
                        profile[f'{key}_std'] = statistics.stdev(values) if len(values) > 1 else 0
                        profile[f'{key}_min'] = min(values)
                        profile[f'{key}_max'] = max(values)
            
            self.authorized_profiles[session_id] = profile
            return profile
            
        except Exception as e:
            logger.error(f"Error building user profile: {str(e)}")
            return None
    
    def analyze_real_time_behavior(self, session_id, current_data):
        """
        Analyze current behavioral data against authorized user profile
        """
        try:
            # Get or build user profile
            if session_id not in self.authorized_profiles:
                profile = self.build_user_profile(session_id)
                if not profile:
                    # No profile available, treat as first-time analysis
                    return {
                        'is_authorized': True,  # Assume authorized for first interaction
                        'confidence': 0.5,
                        'anomaly_score': 0.0,
                        'risk_factors': [],
                        'recommendation': 'Building user profile...'
                    }
            else:
                profile = self.authorized_profiles[session_id]
            
            # Calculate current metrics
            current_metrics = self.calculate_behavioral_metrics(current_data)
            
            # Compare against profile
            anomaly_scores = []
            risk_factors = []
            
            for metric_name, current_value in current_metrics.items():
                if current_value is None:
                    continue
                    
                mean_key = f'{metric_name}_mean'
                std_key = f'{metric_name}_std'
                
                if mean_key in profile and std_key in profile:
                    expected_mean = profile[mean_key]
                    expected_std = profile[std_key]
                    
                    if expected_std > 0:
                        # Calculate z-score
                        z_score = abs(current_value - expected_mean) / expected_std
                        anomaly_scores.append(z_score)
                        
                        # Flag significant deviations
                        if z_score > 2.5:  # More than 2.5 standard deviations
                            risk_factors.append({
                                'metric': metric_name,
                                'current': current_value,
                                'expected': expected_mean,
                                'deviation': z_score,
                                'severity': 'HIGH' if z_score > 3.5 else 'MEDIUM'
                            })
            
            # Calculate overall anomaly score
            overall_anomaly = statistics.mean(anomaly_scores) if anomaly_scores else 0.0
            
            # Determine authorization status
            threshold = 2.0  # Configurable threshold
            is_authorized = overall_anomaly < threshold
            confidence = max(0.1, 1.0 - (overall_anomaly / 5.0))  # Scale confidence
            
            # Additional suspicious behavior checks
            suspicious_indicators = []
            
            # Check for bot-like patterns
            if current_data.get('bot_fingerprint_score', 0) > 0.7:
                suspicious_indicators.append('High bot fingerprint score')
                is_authorized = False
            
            if current_data.get('cursor_entropy', 0) < 1.0:
                suspicious_indicators.append('Low cursor entropy (robotic movement)')
                is_authorized = False
            
            if current_data.get('suspicious_feature_ratio', 0) > 0.6:
                suspicious_indicators.append('High suspicious feature ratio')
                is_authorized = False
            
            # Recommendation based on analysis
            if not is_authorized:
                if overall_anomaly > 3.0:
                    recommendation = 'BLOCK: Highly suspicious behavior detected'
                elif len(suspicious_indicators) > 2:
                    recommendation = 'CHALLENGE: Multiple suspicious indicators'
                else:
                    recommendation = 'MONITOR: Unusual behavior patterns'
            else:
                recommendation = 'ALLOW: Behavior matches authorized user profile'
            
            return {
                'is_authorized': is_authorized,
                'confidence': confidence,
                'anomaly_score': overall_anomaly,
                'risk_factors': risk_factors,
                'suspicious_indicators': suspicious_indicators,
                'recommendation': recommendation,
                'profile_size': len(profile) // 4 if profile else 0  # Number of metrics in profile
            }
            
        except Exception as e:
            logger.error(f"Error in real-time analysis: {str(e)}")
            return {
                'is_authorized': False,
                'confidence': 0.0,
                'anomaly_score': 10.0,
                'risk_factors': [{'metric': 'error', 'severity': 'HIGH'}],
                'recommendation': 'BLOCK: Analysis error'
            }


# Global analyzer instance
behavioral_analyzer = BehavioralAnalyzer()


@csrf_exempt
@require_http_methods(["POST"])
def analyze_behavioral_data(request):
    """
    Real-time behavioral analysis endpoint
    Analyzes user behavior and determines if user is authorized
    """
    try:
        data = json.loads(request.body)
        
        # Extract session ID and behavioral data
        session_id = data.get('session_id')
        behavioral_data = data.get('behavioral_data', {})
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        # Verify session exists
        try:
            session = UserSession.objects.get(session_id=session_id, is_active=True)
        except UserSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Session not found or inactive'
            }, status=404)
        
        # Perform real-time analysis
        analysis_result = behavioral_analyzer.analyze_real_time_behavior(
            session_id, behavioral_data
        )
        
        # Determine user authorization status
        user_auth_status = 'Authorized_user' if analysis_result['is_authorized'] else 'Unauthorized_user'
        
        # Store behavioral data with analysis results
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
            human_score=analysis_result['confidence'] if analysis_result['is_authorized'] else 1.0 - analysis_result['confidence'],
            bot_score=1.0 - analysis_result['confidence'] if analysis_result['is_authorized'] else analysis_result['confidence'],
            human_indicators=[] if not analysis_result['is_authorized'] else ['Normal behavioral patterns'],
            bot_indicators=analysis_result.get('suspicious_indicators', []),
            bot_fingerprint_score=behavioral_data.get('bot_fingerprint_score', 0),
            suspicious_flag=not analysis_result['is_authorized'],
            suspicious_feature_ratio=behavioral_data.get('suspicious_feature_ratio', 0),
            mouse_movement_debug=behavioral_data.get('mouse_movement_debug', {}),
            speed_calculation_debug=behavioral_data.get('speed_calculation_debug', {}),
            post_paste_activity=behavioral_data.get('post_paste_activity', {}),
            keyboard_patterns=behavioral_data.get('keyboard_patterns', []),
            suspicious_patterns=behavioral_data.get('suspicious_patterns', []),
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
            micropause=behavioral_data.get('micropause', []),
            hesitation=behavioral_data.get('hesitation', []),
            devicefingerprint=str(behavioral_data.get('devicefingerprint', '0')),
            missing_canvas_fingerprint=behavioral_data.get('missing_canvas_fingerprint', False),
            canvas_metrics=behavioral_data.get('canvas_metrics', {}),
            unsualscreenresolution=behavioral_data.get('unsualscreenresolution', {}),
            gpu_info=behavioral_data.get('gpu_info', {}),
            timing_metrics=behavioral_data.get('timing_metrics', {}),
            evasion_signals=behavioral_data.get('evasion_signals', {})
        )
        
        # Update session activity
        session.update_activity()
        
        # Log analysis result
        logger.info(f"Behavioral analysis for session {session_id}: {user_auth_status} "
                   f"(confidence: {analysis_result['confidence']:.2f}, "
                   f"anomaly: {analysis_result['anomaly_score']:.2f})")
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'user_auth_status': user_auth_status,
            'is_authorized': analysis_result['is_authorized'],
            'confidence': analysis_result['confidence'],
            'anomaly_score': analysis_result['anomaly_score'],
            'risk_factors': analysis_result['risk_factors'],
            'suspicious_indicators': analysis_result.get('suspicious_indicators', []),
            'recommendation': analysis_result['recommendation'],
            'profile_size': analysis_result.get('profile_size', 0),
            'record_id': behavioral_record.id,
            'timestamp': behavioral_record.created_at.isoformat()
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


@require_http_methods(["GET"])
def get_behavioral_analytics(request, session_id):
    """
    Get comprehensive behavioral analytics for a session
    """
    try:
        # Verify session exists
        try:
            session = UserSession.objects.get(session_id=session_id)
        except UserSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Session not found'
            }, status=404)
        
        # Get all behavioral data for this session
        behavioral_records = BehavioralData.objects.filter(
            session_id=session_id
        ).order_by('-created_at')
        
        # Calculate analytics
        total_records = behavioral_records.count()
        authorized_count = behavioral_records.filter(user_auth='Authorized_user').count()
        unauthorized_count = behavioral_records.filter(user_auth='Unauthorized_user').count()
        
        # Get recent activity (last 10 records)
        recent_activity = []
        for record in behavioral_records[:10]:
            recent_activity.append({
                'timestamp': record.created_at.isoformat(),
                'user_auth': record.user_auth,
                'classification': record.classification,
                'confidence': record.human_score if record.classification == 'Human' else record.bot_score,
                'suspicious_flag': record.suspicious_flag,
                'anomaly_indicators': len(record.bot_indicators)
            })
        
        # Risk assessment
        recent_records = behavioral_records[:20]
        if recent_records:
            recent_unauthorized = sum(1 for r in recent_records if r.user_auth == 'Unauthorized_user')
            risk_level = 'HIGH' if recent_unauthorized > 10 else 'MEDIUM' if recent_unauthorized > 5 else 'LOW'
        else:
            risk_level = 'UNKNOWN'
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'session_info': {
                'name': session.name,
                'usai_id': session.usai_id,
                'session_type': session.session_type,
                'created_at': session.created_at.isoformat(),
                'is_active': session.is_active
            },
            'analytics': {
                'total_records': total_records,
                'authorized_count': authorized_count,
                'unauthorized_count': unauthorized_count,
                'authorization_rate': (authorized_count / total_records * 100) if total_records > 0 else 0,
                'risk_level': risk_level,
                'recent_activity': recent_activity
            }
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting behavioral analytics: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Internal server error'
        }, status=500)
