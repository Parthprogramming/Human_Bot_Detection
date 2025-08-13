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



class BehavioralAnalyzer:
    """
    Advanced behavioral analysis engine for real-time user authentication
    """
    
    def __init__(self):
        self.authorized_profiles = {}  # Cache for authorized user behavioral profiles
        self.real_time_sessions = {}   # Track real-time behavioral data
        
    def calculate_behavioral_metrics(self, behavioral_data):
  
        metrics = {}
        
        try:
            
            # 🖱️ COMPREHENSIVE CURSOR MOVEMENT ANALYSIS
            cursor_movements = behavioral_data.get('cursor_movements', [])
            cursor_speeds = behavioral_data.get('cursor_speeds', [])
            cursor_acceleration = behavioral_data.get('cursor_acceleration', [])
            cursor_curvature = behavioral_data.get('cursor_curvature', [])
            
            if cursor_movements:
                # Calculate movement statistics
                speeds = cursor_speeds if cursor_speeds else []
                accelerations = cursor_acceleration if cursor_acceleration else []
                curvatures = cursor_curvature if cursor_curvature else []
                
                # If speeds not provided, calculate from movements
                if not speeds and len(cursor_movements) > 1:
                    for i in range(1, len(cursor_movements)):
                        prev = cursor_movements[i-1]
                        curr = cursor_movements[i]
                        
                        dx = curr.get('x', 0) - prev.get('x', 0)
                        dy = curr.get('y', 0) - prev.get('y', 0)
                        dt = (curr.get('timestamp', 0) - prev.get('timestamp', 0)) / 1000.0
                        
                        if dt > 0:
                            distance = math.sqrt(dx**2 + dy**2)
                            speed = distance / dt
                            speeds.append(speed)
                
                # Calculate comprehensive cursor metrics
                metrics['cursor_movement_count'] = len(cursor_movements)
                metrics['avg_cursor_speed'] = statistics.mean(speeds) if speeds else 0
                metrics['cursor_speed_variance'] = statistics.variance(speeds) if len(speeds) > 1 else 0
                metrics['max_cursor_speed'] = max(speeds) if speeds else 0
                metrics['min_cursor_speed'] = min(speeds) if speeds else 0
                
                if accelerations:
                    metrics['avg_cursor_acceleration'] = statistics.mean(accelerations)
                    metrics['cursor_acceleration_variance'] = statistics.variance(accelerations) if len(accelerations) > 1 else 0
                
                if curvatures:
                    metrics['avg_cursor_curvature'] = statistics.mean(curvatures)
                    metrics['cursor_curvature_variance'] = statistics.variance(curvatures) if len(curvatures) > 1 else 0
                
                print(f"✅ Cursor metrics: {len(cursor_movements)} movements, avg_speed: {metrics['avg_cursor_speed']:.2f}")
            
            # ⌨️ COMPREHENSIVE KEYSTROKE ANALYSIS
            key_press_times = behavioral_data.get('key_press_times', [])
            key_hold_times = behavioral_data.get('key_hold_times', [])
            
            if key_press_times:
                intervals = []
                for i in range(1, len(key_press_times)):
                    interval = key_press_times[i] - key_press_times[i-1]
                    intervals.append(interval)
                
                metrics['keystroke_count'] = len(key_press_times)
                metrics['avg_keystroke_interval'] = statistics.mean(intervals) if intervals else 0
                metrics['keystroke_variance'] = statistics.variance(intervals) if len(intervals) > 1 else 0
                metrics['keystroke_rhythm_consistency'] = 1 / (1 + metrics['keystroke_variance']) if metrics['keystroke_variance'] > 0 else 1
                
                print(f"✅ Keystroke metrics: {len(key_press_times)} keystrokes")
            
            if key_hold_times:
                metrics['avg_key_hold_time'] = statistics.mean(key_hold_times)
                metrics['key_hold_variance'] = statistics.variance(key_hold_times) if len(key_hold_times) > 1 else 0
                metrics['key_hold_consistency'] = 1 / (1 + metrics['key_hold_variance']) if metrics['key_hold_variance'] > 0 else 1
            
            # 🖱️ COMPREHENSIVE CLICK ANALYSIS
            click_timestamps = behavioral_data.get('click_timestamps', [])
            click_intervals = behavioral_data.get('click_intervals', [])
            
            if click_timestamps:
                if not click_intervals and len(click_timestamps) > 1:
                    click_intervals = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
                
                metrics['click_count'] = len(click_timestamps)
                metrics['avg_click_interval'] = statistics.mean(click_intervals) if click_intervals else 0
                metrics['click_variance'] = statistics.variance(click_intervals) if len(click_intervals) > 1 else 0
                metrics['click_rhythm_consistency'] = 1 / (1 + metrics['click_variance']) if metrics['click_variance'] > 0 else 1
                
                print(f"✅ Click metrics: {len(click_timestamps)} clicks")
            
            # 📜 SCROLL BEHAVIOR ANALYSIS
            scroll_speeds = behavioral_data.get('scroll_speeds', [])
            scroll_changes = behavioral_data.get('scroll_changes', 0)
            
            if scroll_speeds:
                metrics['avg_scroll_speed'] = statistics.mean(scroll_speeds)
                metrics['scroll_speed_variance'] = statistics.variance(scroll_speeds) if len(scroll_speeds) > 1 else 0
                metrics['scroll_smoothness'] = 1 / (1 + metrics['scroll_speed_variance']) if metrics['scroll_speed_variance'] > 0 else 1
            
            metrics['scroll_changes_count'] = scroll_changes
            metrics['scroll_frequency'] = scroll_changes / max(behavioral_data.get('total_time', 1), 1) * 1000
            
            # 🎯 MOUSE JITTER ANALYSIS
            mouse_jitter = behavioral_data.get('mouseJitter', [])
            if mouse_jitter:
                jitter_distances = [item.get('distance', 0) for item in mouse_jitter if isinstance(item, dict)]
                jitter_speeds = [item.get('speed', 0) for item in mouse_jitter if isinstance(item, dict)]
                
                metrics['mouse_jitter_count'] = len(mouse_jitter)
                metrics['avg_jitter_distance'] = statistics.mean(jitter_distances) if jitter_distances else 0
                metrics['avg_jitter_speed'] = statistics.mean(jitter_speeds) if jitter_speeds else 0
                metrics['jitter_intensity'] = metrics['mouse_jitter_count'] / max(len(cursor_movements), 1) if cursor_movements else 0
                
                print(f"✅ Jitter analysis: {len(mouse_jitter)} jitter events")
            
            # ⏸️ HESITATION AND MICROPAUSE ANALYSIS
            hesitation_times = behavioral_data.get('hesitation', [])
            micropauses = behavioral_data.get('micropause', [])
            
            if hesitation_times:
                hesitation_durations = [item.get('duration', 0) for item in hesitation_times if isinstance(item, dict)]
                metrics['hesitation_count'] = len(hesitation_times)
                metrics['avg_hesitation_duration'] = statistics.mean(hesitation_durations) if hesitation_durations else 0
                metrics['hesitation_variance'] = statistics.variance(hesitation_durations) if len(hesitation_durations) > 1 else 0
                metrics['hesitation_frequency'] = metrics['hesitation_count'] / max(behavioral_data.get('total_time', 1), 1) * 1000
                
                print(f"✅ Hesitation analysis: {len(hesitation_times)} hesitations")
            
            if micropauses:
                micropause_durations = [item.get('duration', 0) for item in micropauses if isinstance(item, dict)]
                metrics['micropause_count'] = len(micropauses)
                metrics['avg_micropause_duration'] = statistics.mean(micropause_durations) if micropause_durations else 0
                metrics['micropause_variance'] = statistics.variance(micropause_durations) if len(micropause_durations) > 1 else 0
                metrics['micropause_frequency'] = metrics['micropause_count'] / max(behavioral_data.get('total_time', 1), 1) * 1000
                
                print(f"✅ Micropause analysis: {len(micropauses)} micropauses")
            
            # 🖥️ DEVICE FINGERPRINTING ANALYSIS
            device_fingerprint = behavioral_data.get('devicefingerprint', '0')
            canvas_metrics = behavioral_data.get('canvas_metrics', {})
            gpu_info = behavioral_data.get('gpu_info', {})
            unusual_screen = behavioral_data.get('unsualscreenresolution', {})
            evasion_signals = behavioral_data.get('evasion_signals', {})
            
            # Device analysis
            metrics['device_fingerprint_entropy'] = len(str(device_fingerprint))
            metrics['missing_canvas_fingerprint'] = behavioral_data.get('missing_canvas_fingerprint', False)
            
            # Canvas analysis
            if canvas_metrics:
                metrics['canvas_geometry_complexity'] = canvas_metrics.get('geometryLength', 0)
                metrics['canvas_text_complexity'] = canvas_metrics.get('textLength', 0)
                metrics['canvas_winding_support'] = 1 if canvas_metrics.get('winding') == 'supported' else 0
            
            # Screen resolution analysis
            if unusual_screen:
                metrics['screen_resolution_suspicious'] = 1 if unusual_screen.get('is_unusual', False) else 0
                metrics['screen_spoofing_detected'] = 1 if unusual_screen.get('spoofedMismatch', False) else 0
                metrics['device_pixel_ratio'] = unusual_screen.get('device_pixel_ratio', 1)
            
            # Evasion signals analysis
            if evasion_signals:
                evasion_count = sum(1 for key, value in evasion_signals.items() if value)
                metrics['evasion_signals_count'] = evasion_count
                metrics['automation_risk_score'] = evasion_count / max(len(evasion_signals), 1)
                
                # Critical evasion flags
                metrics['webdriver_detected'] = 1 if evasion_signals.get('webdriver', False) else 0
                metrics['automation_detected'] = 1 if evasion_signals.get('automation', False) else 0
                metrics['headless_browser_detected'] = 1 if evasion_signals.get('headless_chrome', False) else 0
                
                print(f"✅ Evasion analysis: {evasion_count} signals detected")
            
            # 📊 TIMING METRICS ANALYSIS
            timing_metrics = behavioral_data.get('timing_metrics', {})
            if timing_metrics:
                metrics['mouse_movement_frequency'] = timing_metrics.get('mouseMovementFrequency', 0)
                metrics['key_press_frequency'] = timing_metrics.get('keyPressFrequency', 0)
                metrics['click_frequency'] = timing_metrics.get('clickFrequency', 0)
                metrics['total_idle_time'] = timing_metrics.get('totalIdleTime', 0)
                metrics['page_load_performance'] = timing_metrics.get('pageLoadComplete', 0) - timing_metrics.get('navigationStart', 0)
            
            # 🎨 CORE BEHAVIORAL SCORES
            metrics['cursor_entropy'] = behavioral_data.get('cursor_entropy', 0)
            metrics['bot_fingerprint_score'] = behavioral_data.get('bot_fingerprint_score', 0)
            metrics['suspicious_feature_ratio'] = behavioral_data.get('suspicious_feature_ratio', 0)
            metrics['idle_time'] = behavioral_data.get('idle_time', 0)
            metrics['action_count'] = behavioral_data.get('action_count', 0)
            metrics['total_time'] = behavioral_data.get('total_time', 0)
            metrics['paste_detected'] = 1 if behavioral_data.get('paste_detected', False) else 0
            metrics['is_automated_browser'] = 1 if behavioral_data.get('is_automated_browser', False) else 0
            metrics['tab_key_count'] = behavioral_data.get('tabkeycount', 0)
            metrics['cursor_angle_variance'] = behavioral_data.get('cursorAngleVariance', 0)
            
            # 📈 BEHAVIORAL PATTERN ANALYSIS
            keyboard_patterns = behavioral_data.get('keyboard_patterns', [])
            suspicious_patterns = behavioral_data.get('suspicious_patterns', [])
            
            metrics['keyboard_patterns_count'] = len(keyboard_patterns)
            metrics['suspicious_patterns_count'] = len(suspicious_patterns)
            
            # Pattern confidence analysis
            if keyboard_patterns:
                pattern_confidences = [p.get('confidence', 0) for p in keyboard_patterns if isinstance(p, dict)]
                metrics['avg_pattern_confidence'] = statistics.mean(pattern_confidences) if pattern_confidences else 0
            
            # 🔍 COMPREHENSIVE RISK ASSESSMENT
            total_actions = (metrics.get('cursor_movement_count', 0) + 
                           metrics.get('keystroke_count', 0) + 
                           metrics.get('click_count', 0) + 
                           metrics.get('scroll_changes_count', 0))
            
            metrics['total_behavioral_actions'] = total_actions
            metrics['actions_per_second'] = total_actions / max(metrics.get('total_time', 1), 1) * 1000
            
            # Calculate overall behavioral consistency
            consistency_factors = []
            if 'keystroke_rhythm_consistency' in metrics:
                consistency_factors.append(metrics['keystroke_rhythm_consistency'])
            if 'click_rhythm_consistency' in metrics:
                consistency_factors.append(metrics['click_rhythm_consistency'])
            if 'scroll_smoothness' in metrics:
                consistency_factors.append(metrics['scroll_smoothness'])
            
            metrics['overall_behavioral_consistency'] = statistics.mean(consistency_factors) if consistency_factors else 0.5
            
            # Calculate comprehensive automation risk
            automation_indicators = 0
            automation_indicators += metrics.get('evasion_signals_count', 0)
            automation_indicators += 1 if metrics.get('suspicious_patterns_count', 0) > 2 else 0
            automation_indicators += 1 if metrics.get('jitter_intensity', 0) < 0.005 else 0  # Too little natural jitter
            automation_indicators += 1 if metrics.get('overall_behavioral_consistency', 0.5) > 0.98 else 0  # Unnaturally consistent
            automation_indicators += 1 if metrics.get('is_automated_browser', 0) else 0
            
            metrics['comprehensive_automation_risk'] = automation_indicators / 5.0
            

            
        except Exception as e:
            logger.error(f"Error calculating comprehensive behavioral metrics: {str(e)}")
            print(f"❌ Error in comprehensive metrics calculation: {str(e)}")
            
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
    
    
    
    def analyze_with_baseline_comparison(self, session_id, current_data, baseline_behavior, baseline_metrics):

        try:
            

            current_metrics = self.calculate_behavioral_metrics(current_data)
            
            # 🔧 NORMALIZE BASELINE DATA STRUCTURE - Handle both formats  
            # Extract baseline behavioral data for comparison with proper field mapping
            baseline_cursor_movements = (
                baseline_behavior.get('cursor_movements', []) or 
                baseline_behavior.get('cursorMovements', [])
            )
            baseline_key_presses = (
                baseline_behavior.get('key_press_times', []) or 
                baseline_behavior.get('keyPressTimes', [])
            )
            baseline_clicks = (
                baseline_behavior.get('click_timestamps', []) or 
                baseline_behavior.get('clickTimestamps', [])
            )
            baseline_scroll_speeds = (
                baseline_behavior.get('scroll_speeds', []) or 
                baseline_behavior.get('scrollSpeeds', [])
            )
            baseline_action_count = (
                baseline_behavior.get('action_count', 0) or 
                baseline_behavior.get('actionCount', 0)
            )
            

            # Calculate baseline metrics for comparison using normalized structure
            normalized_baseline_data = {
                'cursor_movements': baseline_cursor_movements,
                'key_press_times': baseline_key_presses,
                'click_timestamps': baseline_clicks,
                'scroll_speeds': baseline_scroll_speeds,
                'action_count': baseline_action_count
            }
            
            baseline_computed_metrics = self.calculate_behavioral_metrics(normalized_baseline_data)
            
            # STEP 2: Enhanced Mahalanobis distance analysis for better authorized user detection
            mahalanobis_analysis = self.compare_with_mahalanobis_distance(
                current_data, 
                baseline_behavior,  # Pass original baseline for feature extraction
                distance_threshold=4.5  # 🆕 Increased from 3.0 to 4.5 for better authorized user detection
            )
            
  
            # Traditional baseline comparison
            baseline_deviations = []
            similarity_scores = []
            
            DEVIATION_THRESHOLD = 2.5   # 🆕 Increased from 2.0 to 2.5 for more tolerance
            
            for metric_name in ['avg_speed', 'speed_variance', 'avg_keystroke_interval', 'keystroke_variance', 'avg_click_interval']:
                current_value = current_metrics.get(metric_name, 0)
                baseline_value = baseline_computed_metrics.get(metric_name, 0)
                
                
                if baseline_value > 0:
                    # Calculate percentage difference
                    difference = abs(current_value - baseline_value) / baseline_value
                    similarity = max(0, 1 - difference)
                    similarity_scores.append(similarity)
                    
                    # Check for significant deviations
                    if difference > DEVIATION_THRESHOLD:
                        baseline_deviations.append({
                            'metric': metric_name,
                            'current_value': current_value,
                            'baseline_value': baseline_value,
                            'deviation_ratio': difference,
                            'severity': 'HIGH' if difference > 3.0 else 'MEDIUM'
                        })
                        
            
            # Calculate traditional baseline similarity
            traditional_similarity = statistics.mean(similarity_scores) if similarity_scores else 0.0
            
            
            # STEP 4: Weight Mahalanobis distance analysis more heavily as it's more sophisticated
            # Convert distance to similarity score for combination with traditional metrics
            mahal_similarity = mahalanobis_analysis.get('similarity_score', 0.0)
            combined_similarity = (
                mahal_similarity * 0.7 +  # Mahalanobis similarity (primary)
                traditional_similarity * 0.3                   # Traditional metrics (secondary)
            )
            
            # Authorization decision based on Mahalanobis distance (primary method)
            is_authorized = mahalanobis_analysis['is_authorized']
            
            # Override with traditional method if Mahalanobis result is borderline
            mahal_distance = mahalanobis_analysis.get('mahalanobis_distance', float('inf'))
            adaptive_threshold = mahalanobis_analysis.get('adaptive_threshold', 4.5)
            
            # 🆕 MORE LENIENT BORDERLINE HANDLING
            if adaptive_threshold <= mahal_distance <= (adaptive_threshold * 1.5):
                # In borderline cases, also consider traditional metrics with more lenient threshold
                is_authorized = is_authorized and (traditional_similarity >= 0.5)  # Reduced from 0.6 to 0.5
                print(f"🔧 Borderline case: Mahal={mahal_distance:.2f}, Traditional={traditional_similarity:.2f}")
            elif mahal_distance <= adaptive_threshold * 2.0:
                # For moderate deviations, be more forgiving
                is_authorized = is_authorized or (traditional_similarity >= 0.7)  # Allow override if traditional is good
                print(f"🔧 Moderate deviation: Using traditional metrics as backup")
            
            # Calculate combined confidence
            confidence = (
                mahalanobis_analysis['confidence'] * 0.7 +
                min(traditional_similarity, 1.0) * 0.3
            )
            
            # Risk assessment combining both methods
            risk_score = 1 - combined_similarity
            anomaly_score = (
                mahalanobis_analysis['risk_score'] * 0.7 +
                len(baseline_deviations) * 0.1 +
                (1 - traditional_similarity) * 0.2
            )
            
            # Generate comprehensive recommendations
            if not is_authorized:
                if mahal_distance >= adaptive_threshold * 2.5:  # Very high threshold for blocking
                    recommendation = 'BLOCK: Extreme behavioral anomaly detected (Mahalanobis distance >= 11.25)'
                elif mahal_distance >= adaptive_threshold * 1.8:
                    recommendation = 'CHALLENGE: High behavioral anomaly - additional verification required'
                else:
                    recommendation = 'MONITOR: Moderate anomaly with traditional metric deviations'
            else:
                if mahal_distance <= adaptive_threshold * 0.5:
                    recommendation = 'ALLOW: Excellent behavioral match (very low statistical deviation)'
                elif mahal_distance <= adaptive_threshold:
                    recommendation = 'ALLOW: Good behavioral match with high confidence (within adaptive threshold)'
                elif mahal_distance <= adaptive_threshold * 1.3:
                    recommendation = 'ALLOW: Acceptable behavioral match (enhanced tolerance applied)'
                else:
                    recommendation = 'ALLOW: Extended tolerance match (legitimate user with variation)'
            
            # Combine suspicious indicators from both methods (more lenient thresholds)
            suspicious_indicators = mahalanobis_analysis.get('anomaly_indicators', [])
            if traditional_similarity < 0.4:  # Reduced from 0.5 to 0.4
                suspicious_indicators.append('Low traditional metrics similarity')
            if len(baseline_deviations) > 3:  # Increased from 2 to 3
                suspicious_indicators.append('Multiple traditional metric deviations')
            

            return {
                'is_authorized': is_authorized,
                'confidence': confidence,
                'anomaly_score': anomaly_score,
                'risk_score': risk_score,
                
                # Mahalanobis distance results (primary)
                'mahalanobis_distance': mahalanobis_analysis.get('mahalanobis_distance', float('inf')),
                'adaptive_threshold': mahalanobis_analysis.get('adaptive_threshold', 4.5),
                'original_threshold': mahalanobis_analysis.get('original_threshold', 4.5),
                'authorization_reason': mahalanobis_analysis.get('authorization_reason', 'Unknown'),
                'mahalanobis_similarity': mahal_similarity,
                'normalized_distance': mahalanobis_analysis.get('normalized_distance', 1.0),
                'statistical_significance': mahalanobis_analysis.get('statistical_significance', 'HIGH'),
                'chi_squared_statistic': mahalanobis_analysis.get('chi_squared_statistic', 0.0),
                'degrees_of_freedom': mahalanobis_analysis.get('degrees_of_freedom', 0),
                'features_analyzed': mahalanobis_analysis.get('features_analyzed', 0),
                
                # Traditional metrics (secondary)
                'baseline_similarity': traditional_similarity,
                'baseline_deviations': baseline_deviations,
                'combined_similarity': combined_similarity,
                
                # Risk and indicators
                'risk_factors': [{'metric': 'enhanced_mahalanobis_analysis', 'severity': 'HIGH' if not is_authorized else 'LOW'}],
                'suspicious_indicators': suspicious_indicators,
                'recommendation': recommendation,
                'analysis_type': 'enhanced_mahalanobis_distance_v2',
                'distance_threshold': 4.5,
                'profile_size': len(baseline_computed_metrics)
            }
            
        except Exception as e:
            print(f"❌ ERROR: Error in enhanced baseline comparison: {str(e)}")
            logger.error(f"Error in enhanced baseline comparison: {str(e)}")
            return {
                'is_authorized': False,
                'confidence': 0.0,
                'anomaly_score': 10.0,
                'mahalanobis_distance': float('inf'),
                'mahalanobis_similarity': 0.0,
                'baseline_similarity': 0.0,
                'risk_factors': [{'metric': 'enhanced_mahalanobis_analysis_error', 'severity': 'HIGH'}],
                'recommendation': 'BLOCK: Enhanced Mahalanobis analysis failed',
                'analysis_type': 'enhanced_mahalanobis_distance'
            }
    
    def compare_behavioral_patterns(self, current_data, baseline_behavior):
        """
        Compare behavioral patterns between current and baseline data
        """
        try:
            # Cursor movement pattern comparison
            current_movements = current_data.get('cursor_movements', [])
            baseline_movements = baseline_behavior.get('cursorMovements', [])
            
            cursor_pattern_match = self.compare_movement_patterns(current_movements, baseline_movements)
            
            # Timing pattern comparison
            current_key_times = current_data.get('key_press_times', [])
            baseline_key_times = baseline_behavior.get('keyPressTimes', [])
            
            timing_pattern_match = self.compare_timing_patterns(current_key_times, baseline_key_times)
            
            # Click pattern comparison
            current_clicks = current_data.get('click_timestamps', [])
            baseline_clicks = baseline_behavior.get('clickTimestamps', [])
            
            click_pattern_match = self.compare_click_patterns(current_clicks, baseline_clicks)
            
            # Overall pattern match
            overall_match = (cursor_pattern_match * 0.4 + 
                           timing_pattern_match * 0.4 + 
                           click_pattern_match * 0.2)
            
            return {
                'cursor_pattern_match': cursor_pattern_match,
                'timing_pattern_match': timing_pattern_match,
                'click_pattern_match': click_pattern_match,
                'overall_match': overall_match
            }
            
        except Exception as e:
            logger.error(f"Error comparing behavioral patterns: {str(e)}")
            return {
                'cursor_pattern_match': 0.0,
                'timing_pattern_match': 0.0,
                'click_pattern_match': 0.0,
                'overall_match': 0.0
            }
    
    def compare_movement_patterns(self, current_movements, baseline_movements):
        """Compare cursor movement patterns"""
        if not current_movements or not baseline_movements:
            return 0.0
        
        # Simple pattern matching based on movement characteristics
        # This can be enhanced with more sophisticated algorithms
        return min(len(current_movements) / max(len(baseline_movements), 1), 1.0) * 0.8
    
    def compare_timing_patterns(self, current_times, baseline_times):
        """Compare keystroke timing patterns"""
        if len(current_times) < 2 or len(baseline_times) < 2:
            return 0.5
        
        # Calculate intervals
        current_intervals = [current_times[i] - current_times[i-1] for i in range(1, len(current_times))]
        baseline_intervals = [baseline_times[i] - baseline_times[i-1] for i in range(1, len(baseline_times))]
        
        if not current_intervals or not baseline_intervals:
            return 0.5
        
        # Compare average intervals
        current_avg = statistics.mean(current_intervals)
        baseline_avg = statistics.mean(baseline_intervals)
        
        if baseline_avg > 0:
            similarity = 1 - min(abs(current_avg - baseline_avg) / baseline_avg, 1.0)
            return max(similarity, 0.0)
        
        return 0.5
    
    def compare_click_patterns(self, current_clicks, baseline_clicks):
        """Compare click timing patterns"""
        if len(current_clicks) < 2 or len(baseline_clicks) < 2:
            return 0.5
        
        # Simple comparison based on click frequency
        current_freq = len(current_clicks)
        baseline_freq = len(baseline_clicks)
        
        if baseline_freq > 0:
            similarity = 1 - min(abs(current_freq - baseline_freq) / baseline_freq, 1.0)
            return max(similarity, 0.0)
        
        return 0.5
    
    def calculate_mahalanobis_distance(self, current_vector, baseline_data):
       
        try:
            current_vec = np.array(current_vector, dtype=float)
            
            # Extract multiple baseline feature vectors to build statistical distribution
            baseline_feature_vectors = []
            
            # If baseline_data is a list of multiple samples, use them directly
            if isinstance(baseline_data, list):
                for sample in baseline_data:
                    features = self.extract_behavioral_features(sample)
                    if features:
                        baseline_feature_vectors.append(features)
            else:
                # Single baseline sample - enhanced handling for better distribution modeling
                baseline_features = self.extract_behavioral_features(baseline_data)
                if baseline_features:
                    # Add the original baseline
                    baseline_feature_vectors.append(baseline_features)
                    
                    # 🆕 IMPROVED VARIATION GENERATION
                    # Create more realistic variations based on typical human behavioral variance
                    base_array = np.array(baseline_features)
                    
                    # Different types of realistic variations
                    variation_types = [
                        (0.02, 5),   # Very small variations (5 samples)
                        (0.05, 3),   # Small variations (3 samples) 
                        (0.08, 2),   # Medium variations (2 samples)
                    ]
                    
                    for std_factor, count in variation_types:
                        for _ in range(count):
                            # Use different noise patterns for different feature types
                            noise = np.random.normal(0, std_factor, len(baseline_features))
                            
                            # Apply selective noise based on feature indices
                            for i in range(len(noise)):
                                if i < 20:  # Cursor/mouse features - moderate variation
                                    noise[i] *= 0.8
                                elif i < 40:  # Keystroke features - low variation  
                                    noise[i] *= 0.5
                                else:  # Other features - higher variation allowed
                                    noise[i] *= 1.2
                            
                            variation = base_array * (1 + noise)
                            # Ensure no negative values for features that shouldn't be negative
                            variation = np.maximum(variation, base_array * 0.1)
                            baseline_feature_vectors.append(variation.tolist())
            
            if len(baseline_feature_vectors) < 2:
                print("⚠️ Insufficient baseline data for Mahalanobis distance calculation")
                return float('inf')  # High distance indicates anomaly
            
            # Convert to numpy matrix
            baseline_matrix = np.array(baseline_feature_vectors, dtype=float)
            
            # Ensure current vector matches baseline vector dimensions
            if len(current_vec) != baseline_matrix.shape[1]:
                # Pad shorter vector with zeros or truncate longer vector
                target_len = baseline_matrix.shape[1]
                if len(current_vec) < target_len:
                    current_vec = np.pad(current_vec, (0, target_len - len(current_vec)), 'constant')
                else:
                    current_vec = current_vec[:target_len]
            
            # Calculate mean and covariance matrix of baseline distribution
            baseline_mean = np.mean(baseline_matrix, axis=0)
            baseline_cov = np.cov(baseline_matrix, rowvar=False)
            
            # 🆕 ENHANCED REGULARIZATION STRATEGY
            # Adaptive regularization based on matrix condition
            condition_number = np.linalg.cond(baseline_cov)
            
            if condition_number > 1e12:  # Very ill-conditioned
                regularization = 1e-3
                print(f"⚠️ High condition number ({condition_number:.2e}), using strong regularization")
            elif condition_number > 1e8:  # Moderately ill-conditioned  
                regularization = 1e-4
                print(f"⚠️ Moderate condition number ({condition_number:.2e}), using medium regularization")
            else:
                regularization = 1e-6
                print(f"✅ Good condition number ({condition_number:.2e}), using light regularization")
            
            baseline_cov += np.eye(baseline_cov.shape[0]) * regularization
            
            # 🆕 ENHANCED DISTANCE CALCULATION WITH FALLBACKS
            try:
                # Method 1: Standard scipy mahalanobis
                inv_cov = linalg.inv(baseline_cov)
                mahal_distance = mahalanobis(current_vec, baseline_mean, inv_cov)
                
                
                # Sanity check for unrealistic distances
                if mahal_distance > 100:  # Extremely high distance suggests calculation error
                    print(f"⚠️ Unrealistic distance detected ({mahal_distance:.4f}), using fallback")
                    raise ValueError("Distance too high")
                    
                return float(mahal_distance)
                
            except (linalg.LinAlgError, np.linalg.LinAlgError, ValueError):
                # Method 2: Pseudo-inverse approach
                print("⚠️ Using pseudo-inverse for problematic covariance matrix")
                try:
                    pseudo_inv_cov = linalg.pinv(baseline_cov)
                    diff = current_vec - baseline_mean
                    mahal_distance = np.sqrt(np.dot(np.dot(diff, pseudo_inv_cov), diff))
                    
                    
                    # Scale down if unrealistic
                    if mahal_distance > 50:
                        mahal_distance = min(mahal_distance, 10.0)  # Cap at reasonable value
                        print(f"🔧 Capped distance at: {mahal_distance:.4f}")
                    
                    return float(mahal_distance)
                    
                except Exception as e:
                    # Method 3: Enhanced normalized Euclidean distance
                    print(f"⚠️ Pseudo-inverse failed ({e}), using enhanced Euclidean fallback")
                    
                    std_devs = np.std(baseline_matrix, axis=0)
                    std_devs[std_devs == 0] = np.mean(std_devs[std_devs > 0]) if np.any(std_devs > 0) else 1.0
                    
                    # Use median absolute deviation for more robust scaling
                    mad = np.median(np.abs(baseline_matrix - baseline_mean), axis=0)
                    mad[mad == 0] = np.median(mad[mad > 0]) if np.any(mad > 0) else 1.0
                    
                    # Combine std and MAD for robust distance
                    scaling_factors = np.minimum(std_devs, mad * 1.4826)  # 1.4826 is MAD scaling factor
                    euclidean_normalized = np.sqrt(np.sum(((current_vec - baseline_mean) / scaling_factors) ** 2))
                    
                    return float(euclidean_normalized)
            
        except Exception as e:
            logger.error(f"Error calculating Mahalanobis distance: {str(e)}")
            print(f"🚨 Error in Mahalanobis calculation: {e}")
            return float('inf')  # High distance indicates anomaly
    
    def extract_behavioral_features(self, behavioral_data):

        try:
            features = []
            
            print(f"� Extracting comprehensive features from ALL behavioral data...")
            
            # 📊 FIRST: Calculate comprehensive metrics to get derived features
            comprehensive_metrics = self.calculate_behavioral_metrics(behavioral_data)
            
            # 🖱️ COMPREHENSIVE CURSOR MOVEMENT FEATURES
            cursor_movements = (
                behavioral_data.get('cursor_movements', []) or 
                behavioral_data.get('cursorMovements', [])
            )
            cursor_speeds = behavioral_data.get('cursor_speeds', [])
            cursor_acceleration = behavioral_data.get('cursor_acceleration', [])
            cursor_curvature = behavioral_data.get('cursor_curvature', [])
            
            
            # Cursor movement statistical features
            if cursor_movements:
                # Basic movement calculations if not provided
                speeds = cursor_speeds if cursor_speeds else []
                if not speeds and len(cursor_movements) > 1:
                    for i in range(1, len(cursor_movements)):
                        prev = cursor_movements[i-1]
                        curr = cursor_movements[i]
                        
                        prev_x = prev.get('x', 0) if isinstance(prev, dict) else 0
                        prev_y = prev.get('y', 0) if isinstance(prev, dict) else 0
                        prev_time = prev.get('timestamp', 0) if isinstance(prev, dict) else 0
                        
                        curr_x = curr.get('x', 0) if isinstance(curr, dict) else 0
                        curr_y = curr.get('y', 0) if isinstance(curr, dict) else 0
                        curr_time = curr.get('timestamp', 0) if isinstance(curr, dict) else 0
                        
                        dx = curr_x - prev_x
                        dy = curr_y - prev_y
                        dt = (curr_time - prev_time) / 1000.0
                        
                        if dt > 0:
                            distance = math.sqrt(dx**2 + dy**2)
                            speed = distance / dt
                            speeds.append(speed)
                
                # Comprehensive cursor features
                features.extend([
                    len(cursor_movements),  # Movement count
                    statistics.mean(speeds) if speeds else 0,  # Avg speed
                    statistics.median(speeds) if speeds else 0,  # Median speed
                    max(speeds) if speeds else 0,  # Max speed
                    min(speeds) if speeds else 0,  # Min speed
                    statistics.stdev(speeds) if len(speeds) > 1 else 0,  # Speed variance
                    comprehensive_metrics.get('avg_cursor_speed', 0),
                    comprehensive_metrics.get('cursor_speed_variance', 0),
                    statistics.mean(cursor_acceleration) if cursor_acceleration else 0,
                    statistics.stdev(cursor_acceleration) if len(cursor_acceleration) > 1 else 0,
                    statistics.mean(cursor_curvature) if cursor_curvature else 0,
                    statistics.stdev(cursor_curvature) if len(cursor_curvature) > 1 else 0
                ])
                
                print(f"✅ Cursor features: {len(speeds)} movements processed")
            else:
                features.extend([0] * 12)  # 12 zeros for missing cursor data
            
            # ⌨️ COMPREHENSIVE KEYSTROKE FEATURES
            key_press_times = (
                behavioral_data.get('key_press_times', []) or 
                behavioral_data.get('keyPressTimes', [])
            )
            key_hold_times = (
                behavioral_data.get('key_hold_times', []) or 
                behavioral_data.get('keyHoldTimes', [])
            )
            
            
            if key_press_times and len(key_press_times) > 1:
                intervals = [key_press_times[i] - key_press_times[i-1] for i in range(1, len(key_press_times))]
                features.extend([
                    len(key_press_times),  # Keystroke count
                    statistics.mean(intervals),  # Avg interval
                    statistics.median(intervals),  # Median interval
                    max(intervals),  # Max interval
                    min(intervals),  # Min interval
                    statistics.stdev(intervals) if len(intervals) > 1 else 0,  # Interval variance
                    comprehensive_metrics.get('keystroke_rhythm_consistency', 0.5)
                ])
            else:
                features.extend([0, 0, 0, 0, 0, 0, 0.5])
            
            if key_hold_times:
                features.extend([
                    statistics.mean(key_hold_times),
                    statistics.stdev(key_hold_times) if len(key_hold_times) > 1 else 0,
                    comprehensive_metrics.get('key_hold_consistency', 0.5)
                ])
            else:
                features.extend([0, 0, 0.5])
                
            print(f"✅ Keystroke features processed")
            
            # �️ COMPREHENSIVE CLICK FEATURES
            click_timestamps = (
                behavioral_data.get('click_timestamps', []) or 
                behavioral_data.get('clickTimestamps', [])
            )
            click_intervals = behavioral_data.get('click_intervals', [])
            
            
            if click_timestamps and len(click_timestamps) > 1:
                if not click_intervals:
                    click_intervals = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
                
                features.extend([
                    len(click_timestamps),  # Click count
                    statistics.mean(click_intervals) if click_intervals else 0,
                    statistics.stdev(click_intervals) if len(click_intervals) > 1 else 0,
                    comprehensive_metrics.get('click_rhythm_consistency', 0.5)
                ])
            else:
                features.extend([0, 0, 0, 0.5])
                
            print(f"✅ Click features processed")
            
            # � SCROLL BEHAVIOR FEATURES
            scroll_speeds = behavioral_data.get('scroll_speeds', [])
            scroll_changes = behavioral_data.get('scroll_changes', 0)
            
            if scroll_speeds:
                features.extend([
                    len(scroll_speeds),
                    statistics.mean(scroll_speeds),
                    statistics.stdev(scroll_speeds) if len(scroll_speeds) > 1 else 0,
                    comprehensive_metrics.get('scroll_smoothness', 0.5)
                ])
            else:
                features.extend([0, 0, 0, 0.5])
            
            features.extend([
                scroll_changes,
                comprehensive_metrics.get('scroll_frequency', 0)
            ])
            
            # 🎯 MOUSE JITTER AND MOVEMENT QUALITY FEATURES
            mouse_jitter = behavioral_data.get('mouseJitter', [])
            features.extend([
                len(mouse_jitter),
                comprehensive_metrics.get('avg_jitter_distance', 0),
                comprehensive_metrics.get('avg_jitter_speed', 0),
                comprehensive_metrics.get('jitter_intensity', 0)
            ])
            
            # ⏸️ HESITATION AND MICROPAUSE FEATURES
            hesitation_times = behavioral_data.get('hesitation', [])
            micropauses = behavioral_data.get('micropause', [])
            
            features.extend([
                len(hesitation_times),
                comprehensive_metrics.get('avg_hesitation_duration', 0),
                comprehensive_metrics.get('hesitation_variance', 0),
                comprehensive_metrics.get('hesitation_frequency', 0),
                len(micropauses),
                comprehensive_metrics.get('avg_micropause_duration', 0),
                comprehensive_metrics.get('micropause_variance', 0),
                comprehensive_metrics.get('micropause_frequency', 0)
            ])
            
            # �️ DEVICE AND FINGERPRINTING FEATURES
            device_fingerprint = behavioral_data.get('devicefingerprint', '0')
            canvas_metrics = behavioral_data.get('canvas_metrics', {})
            unusual_screen = behavioral_data.get('unsualscreenresolution', {})
            
            features.extend([
                len(str(device_fingerprint)),  # Fingerprint complexity
                1 if behavioral_data.get('missing_canvas_fingerprint', False) else 0,
                canvas_metrics.get('geometryLength', 0) if canvas_metrics else 0,
                canvas_metrics.get('textLength', 0) if canvas_metrics else 0,
                1 if canvas_metrics.get('winding') == 'supported' else 0,
                1 if unusual_screen.get('is_unusual', False) else 0,
                1 if unusual_screen.get('spoofedMismatch', False) else 0,
                unusual_screen.get('device_pixel_ratio', 1) if unusual_screen else 1
            ])
            
            # 🚨 EVASION AND AUTOMATION DETECTION FEATURES
            evasion_signals = behavioral_data.get('evasion_signals', {})
            evasion_count = sum(1 for key, value in evasion_signals.items() if value) if evasion_signals else 0
            
            features.extend([
                evasion_count,
                comprehensive_metrics.get('automation_risk_score', 0),
                1 if evasion_signals.get('webdriver', False) else 0,
                1 if evasion_signals.get('automation', False) else 0,
                1 if evasion_signals.get('headless_chrome', False) else 0
            ])
            
            # 📊 TIMING AND PERFORMANCE FEATURES
            timing_metrics = behavioral_data.get('timing_metrics', {})
            if timing_metrics:
                features.extend([
                    timing_metrics.get('mouseMovementFrequency', 0),
                    timing_metrics.get('keyPressFrequency', 0),
                    timing_metrics.get('clickFrequency', 0),
                    timing_metrics.get('totalIdleTime', 0) / 1000.0,  # Convert to seconds
                    (timing_metrics.get('pageLoadComplete', 0) - timing_metrics.get('navigationStart', 0)) / 1000.0
                ])
            else:
                features.extend([0, 0, 0, 0, 0])
            
            # 🎨 CORE BEHAVIORAL SCORES AND METRICS
            features.extend([
                behavioral_data.get('cursor_entropy', 0),
                behavioral_data.get('bot_fingerprint_score', 0),
                behavioral_data.get('suspicious_feature_ratio', 0),
                behavioral_data.get('idle_time', 0) / 1000.0,  # Convert to seconds
                behavioral_data.get('action_count', 0),
                behavioral_data.get('total_time', 0) / 1000.0,  # Convert to seconds
                1 if behavioral_data.get('paste_detected', False) else 0,
                1 if behavioral_data.get('is_automated_browser', False) else 0,
                behavioral_data.get('tabkeycount', behavioral_data.get('TabKeyCount', 0)),
                behavioral_data.get('cursorAngleVariance', 0)
            ])
            
            # 📈 COMPREHENSIVE BEHAVIORAL ANALYSIS SCORES
            keyboard_patterns = behavioral_data.get('keyboard_patterns', [])
            suspicious_patterns = behavioral_data.get('suspicious_patterns', [])
            
            features.extend([
                len(keyboard_patterns),
                len(suspicious_patterns),
                comprehensive_metrics.get('total_behavioral_actions', 0),
                comprehensive_metrics.get('actions_per_second', 0),
                comprehensive_metrics.get('overall_behavioral_consistency', 0.5),
                comprehensive_metrics.get('comprehensive_automation_risk', 0)
            ])
            
            # Pattern confidence analysis
            if keyboard_patterns:
                pattern_confidences = [p.get('confidence', 0) for p in keyboard_patterns if isinstance(p, dict)]
                features.append(statistics.mean(pattern_confidences) if pattern_confidences else 0.5)
            else:
                features.append(0.5)
            

            
            return features
            
        except Exception as e:
            print(f"❌ ERROR: Error extracting behavioral features: {str(e)}")
            logger.error(f"Error extracting behavioral features: {str(e)}")
            return []
    
    def create_rolling_windows(self, data, window_size=10, step_size=5):
        """
        Create rolling windows from behavioral data for comparison
        """
        try:
            if len(data) < window_size:
                return [data]  # Return single window if data is smaller than window size
            
            windows = []
            for i in range(0, len(data) - window_size + 1, step_size):
                window = data[i:i + window_size]
                windows.append(window)
            
            return windows
            
        except Exception as e:
            logger.error(f"Error creating rolling windows: {str(e)}")
            return [data]
    
    def compare_with_mahalanobis_distance(self, current_data, baseline_behavior, distance_threshold=4.5):

        try:
            print(f"🔬 Starting Enhanced Mahalanobis distance analysis with threshold: {distance_threshold}")
            
            # Extract feature vectors from both datasets
            current_features = self.extract_behavioral_features(current_data)
            
            if not current_features:
                print("⚠️ Insufficient current behavioral data for comparison")
                return {
                    'mahalanobis_distance': float('inf'),
                    'normalized_distance': 1.0,
                    'is_authorized': False,
                    'confidence': 0.0,
                    'analysis_type': 'mahalanobis_distance',
                    'recommendation': 'BLOCK: Insufficient current behavioral data'
                }
            
            # Calculate Mahalanobis distance with enhanced error handling
            mahal_distance = self.calculate_mahalanobis_distance(current_features, baseline_behavior)
            
            # 🆕 ADAPTIVE THRESHOLD BASED ON DATA QUALITY
            # Adjust threshold based on feature vector length and baseline quality
            feature_count = len(current_features)
            if feature_count < 20:  # Few features available
                adaptive_threshold = distance_threshold * 1.5  # More lenient
                print(f"🔧 Adaptive threshold (few features): {adaptive_threshold:.2f}")
            elif feature_count > 50:  # Rich feature set
                adaptive_threshold = distance_threshold * 0.9  # Slightly stricter
                print(f"🔧 Adaptive threshold (rich features): {adaptive_threshold:.2f}")
            else:
                adaptive_threshold = distance_threshold
            
            # 🆕 MULTIPLE AUTHORIZATION CRITERIA (More lenient for authorized users)
            primary_authorized = mahal_distance <= adaptive_threshold
            
            # Secondary check: If close to threshold, use more lenient criteria
            near_threshold = adaptive_threshold <= mahal_distance <= (adaptive_threshold * 1.3)
            
            # Tertiary check: Very strict only for obvious anomalies
            obvious_anomaly = mahal_distance > (adaptive_threshold * 2.0)
            
            # 🎯 ENHANCED AUTHORIZATION LOGIC
            if primary_authorized:
                is_authorized = True
                auth_reason = "Primary: Within threshold"
            elif near_threshold and mahal_distance <= 6.0:
                is_authorized = True  # 🆕 Give benefit of doubt for borderline cases
                auth_reason = "Secondary: Near threshold but acceptable"
            elif obvious_anomaly:
                is_authorized = False
                auth_reason = "Blocked: Clear anomaly detected"
            else:
                # 🆕 Additional checks for intermediate cases
                if mahal_distance <= 7.0:  # More lenient upper bound
                    is_authorized = True
                    auth_reason = "Tertiary: Within extended tolerance"
                else:
                    is_authorized = False
                    auth_reason = "Blocked: Exceeds extended threshold"
            
            print(f"🎯 Authorization Decision: {is_authorized} ({auth_reason})")
            print(f"🔍 Distance: {mahal_distance:.4f}, Threshold: {adaptive_threshold:.4f}")
            
            # Normalize distance to 0-1 scale for easier interpretation
            normalized_distance = min(1.0, mahal_distance / adaptive_threshold)
            similarity_score = 1.0 - normalized_distance  # Convert distance to similarity
            
            # 🆕 ENHANCED CONFIDENCE CALCULATION
            if is_authorized:
                if mahal_distance <= adaptive_threshold * 0.5:
                    confidence = 0.95  # Very high confidence for excellent matches
                elif mahal_distance <= adaptive_threshold:
                    confidence = 0.85 - (mahal_distance / adaptive_threshold) * 0.3  # Scale down
                else:
                    confidence = 0.65  # Moderate confidence for borderline authorized
            else:
                if mahal_distance >= adaptive_threshold * 3:
                    confidence = 0.95  # High confidence in blocking obvious anomalies
                else:
                    confidence = 0.5 + (mahal_distance / adaptive_threshold) * 0.2  # Scale up
            
            confidence = max(0.1, min(0.99, confidence))  # Clamp between 0.1 and 0.99
            
            # 🆕 ENHANCED RECOMMENDATION LOGIC (More nuanced for authorized users)
            if is_authorized:
                if mahal_distance <= adaptive_threshold * 0.5:
                    recommendation = 'ALLOW: Excellent behavioral match (very low statistical deviation)'
                elif mahal_distance <= adaptive_threshold:
                    recommendation = 'ALLOW: Good behavioral match (within normal threshold)'
                elif mahal_distance <= adaptive_threshold * 1.3:
                    recommendation = 'ALLOW: Acceptable behavioral variation (near threshold but authorized)'
                else:
                    recommendation = 'ALLOW: Extended tolerance match (borderline but likely legitimate user)'
            else:
                if mahal_distance >= adaptive_threshold * 3:
                    recommendation = 'BLOCK: Extreme behavioral anomaly - probable bot or account takeover'
                elif mahal_distance >= adaptive_threshold * 2:
                    recommendation = 'BLOCK: High behavioral anomaly - significant deviation detected'
                else:
                    recommendation = 'CHALLENGE: Moderate behavioral anomaly - additional verification recommended'
            
            # 🆕 ENHANCED RISK ASSESSMENT
            risk_score = min(1.0, mahal_distance / (adaptive_threshold * 1.5))  # More gradual risk scaling
            anomaly_indicators = []
            
            # More nuanced anomaly detection
            if mahal_distance > adaptive_threshold * 2:
                anomaly_indicators.append(f'High Mahalanobis distance ({mahal_distance:.2f}) - significant deviation')
            elif mahal_distance > adaptive_threshold:
                anomaly_indicators.append(f'Moderate Mahalanobis distance ({mahal_distance:.2f}) - some deviation detected')
            
            if mahal_distance > adaptive_threshold * 3:
                anomaly_indicators.append('Extremely high statistical deviation from baseline')
            if mahal_distance < 0.3:  # Very low distance might indicate replay attack
                anomaly_indicators.append('Suspiciously perfect behavioral match (possible replay attack)')
            
            # Statistical significance assessment
            degrees_of_freedom = len(current_features)
            chi_squared_stat = mahal_distance ** 2
            
            # More lenient statistical significance thresholds
            if chi_squared_stat > degrees_of_freedom + 4 * np.sqrt(2 * degrees_of_freedom):
                statistical_significance = 'HIGH'
            elif chi_squared_stat > degrees_of_freedom + 3 * np.sqrt(2 * degrees_of_freedom):
                statistical_significance = 'MEDIUM'
            else:
                statistical_significance = 'LOW'
            

            return {
                'mahalanobis_distance': mahal_distance,
                'adaptive_threshold': adaptive_threshold,
                'original_threshold': distance_threshold,
                'normalized_distance': normalized_distance,
                'similarity_score': similarity_score,
                'is_authorized': is_authorized,
                'authorization_reason': auth_reason,
                'confidence': confidence,
                'risk_score': risk_score,
                'anomaly_indicators': anomaly_indicators,
                'analysis_type': 'enhanced_mahalanobis_distance',
                'recommendation': recommendation,
                'distance_threshold': distance_threshold,
                'statistical_significance': statistical_significance,
                'degrees_of_freedom': degrees_of_freedom,
                'chi_squared_statistic': chi_squared_stat,
                'features_analyzed': len(current_features)
            }
            
        except Exception as e:
            logger.error(f"Error in Mahalanobis distance comparison: {str(e)}")
            print(f"🚨 Error in Mahalanobis analysis: {e}")
            return {
                'mahalanobis_distance': float('inf'),
                'normalized_distance': 1.0,
                'is_authorized': False,
                'confidence': 0.0,
                'analysis_type': 'mahalanobis_distance',
                'recommendation': 'BLOCK: Mahalanobis distance analysis failed'
            }


# Global analyzer instance
behavioral_analyzer = BehavioralAnalyzer()


@csrf_exempt
@require_http_methods(["POST"])
def handle_baseline_storage(request):
    """
    Dedicated API endpoint for storing baseline user behavior from frontend
    Accepts comprehensive baseline behavioral data and stores it in UserBaselineBehavior model
    """
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
        user_id = baseline_data.get('formData', {}).get('userName') or f"session_{session_id}"
        
        print(f"🦅 User ID: {user_id}")
        
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
    """
    Enhanced behavioral analysis with cosine similarity and rolling window support
    """
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id')
        behavioral_data = data.get('behavioral_data', {})
        analysis_type = data.get('analysis_type', 'enhanced_mahalanobis_distance')  
        similarity_threshold = data.get('similarity_threshold', 0.75)  
        
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

        try:
            # Get the most recent baseline behavior for this session
            baseline_record = UserBaselineBehavior.objects.filter(
                session_id=session_id,
                is_active=True
            ).order_by('-created_at').first()
            
            if not baseline_record:
                print(f"⚠️ No baseline behavior found for session: {session_id}")
                return JsonResponse({
                    'success': False,
                    'message': 'No baseline behavior found for this session. Please complete baseline collection first.',
                    'requires_baseline': True,
                    'session_id': session_id
                }, status=400)
            
            baseline_behavior = baseline_record.baseline_user_behavior
            baseline_metrics = baseline_record.baseline_metrics
            

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
            # Create a new session for behavioral tracking if it doesn't exist
            session = UserSession.objects.create(
                session_id=session_id,
                is_active=True,
                created_at=timezone.now()
            )
            print(f"🆕 Created new UserSession for behavioral tracking: {session_id}")
        
        # 📊 STEP 2: ENHANCED COSINE SIMILARITY ANALYSIS WITH ROLLING WINDOWS
        print(f"🔬 Performing enhanced cosine similarity analysis...")
        
        # Check if rolling window data is provided from frontend
        rolling_windows = behavioral_data.get('rollingWindows', [])
        window_metadata = behavioral_data.get('windowMetadata', {})
        
        if rolling_windows:
            print(f"📊 Rolling windows received from frontend: {len(rolling_windows)} windows")
            print(f"📊 Window metadata: {window_metadata}")
        
        # Enhanced analysis with baseline comparison using cosine similarity
        analysis_result = behavioral_analyzer.analyze_with_baseline_comparison(
            session_id, behavioral_data, baseline_behavior, baseline_metrics
        )
        
        # 📊 STEP 3: ADDITIONAL MAHALANOBIS DISTANCE ANALYSIS IF REQUESTED
        if analysis_type == 'mahalanobis_distance' and rolling_windows:
            print(f"🔬 Performing dedicated Mahalanobis distance analysis...")
            
            # Perform direct Mahalanobis distance analysis with full comparison
            mahalanobis_result = behavioral_analyzer.compare_with_mahalanobis_distance(
                behavioral_data, 
                baseline_behavior,
                distance_threshold=3.0  # 3 standard deviations threshold
            )

            # Merge results, prioritizing Mahalanobis distance
            analysis_result.update({
                'mahalanobis_analysis': mahalanobis_result,
                'rolling_windows_analyzed': len(rolling_windows),
                'window_metadata': window_metadata,
                'primary_analysis': 'mahalanobis_distance'
            })

            # Override authorization based on Mahalanobis distance if it's stricter
            if not mahalanobis_result['is_authorized']:
                analysis_result['is_authorized'] = False
                analysis_result['recommendation'] = mahalanobis_result['recommendation']
        
        user_auth_status = 'Authorized_user' if analysis_result['is_authorized'] else 'Unauthorized_user'
        risk_score = analysis_result.get('anomaly_score', 0)
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
            bot_indicators=analysis_result.get('suspicious_indicators', []),
            bot_fingerprint_score=behavioral_data.get('bot_fingerprint_score', 0),
            suspicious_flag=not analysis_result['is_authorized'],
            suspicious_feature_ratio=risk_score,
            mouse_movement_debug=behavioral_data.get('mouse_movement_debug', {}),
            speed_calculation_debug=behavioral_data.get('speed_calculation_debug', {}),
            post_paste_activity=behavioral_data.get('post_paste_activity', {}),
            keyboard_patterns=behavioral_data.get('keyboard_patterns', []),
            suspicious_patterns=analysis_result.get('suspicious_indicators', []),
            action_count=behavioral_data.get('action_count', 0),
            is_automated_browser=behavioral_data.get('is_automated_browser', False),
            cursor_entropy=behavioral_data.get('cursor_entropy', 0),
            scroll_speeds=behavioral_data.get('scroll_speeds', []),
            scroll_changes=behavioral_data.get('scroll_changes', 0),
            idle_time=behavioral_data.get('idle_time', 0),
            honeypot_value=behavioral_data.get('honeypot_value'),
            tabkeycount=behavioral_data.get('TabKeyCount', 0),
            cursorAngleVariance=behavioral_data.get('cursorAngleVariance', 0),
            mouseJitter=behavioral_data.get('mouseJitter', []),
            micropause=behavioral_data.get('microPauses', []),
            hesitation=behavioral_data.get('hesitationTimes', []),
            devicefingerprint=str(behavioral_data.get('deviceFingerprint', '0')),
            missing_canvas_fingerprint=behavioral_data.get('missingCanvasFingerprint', False),
            canvas_metrics=behavioral_data.get('canvasMetrics', {}),
            unsualscreenresolution=behavioral_data.get('unusualScreenResolution', {}),
            gpu_info=behavioral_data.get('gpuInfo', {}),
            timing_metrics=behavioral_data.get('timingMetrics', {}),
            evasion_signals=behavioral_data.get('evasionSignals', {})
        )
        
        # Update session activity
        session.update_activity()
        

        
        # 🚨 Special handling for unauthorized users
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
                'anomaly_score': analysis_result['anomaly_score'],
                
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
            'anomaly_score': analysis_result['anomaly_score'],
            
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
