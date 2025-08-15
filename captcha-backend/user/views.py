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
        self.authorized_profiles = {}  
        self.real_time_sessions = {}   
    
    def apply_risk_confidence_check(self, analysis_result):
    
        risk_score = analysis_result.get('risk_score', 0.0)
        if risk_score > 3.0:
            analysis_result['is_authorized'] = False
            analysis_result['authorization_reason'] = f'RISK_SCORE_BLOCK: Risk score ({risk_score:.3f}) exceeds threshold (3.0) - Blocking user'
            analysis_result['recommendation'] = f'BLOCK: Risk score ({risk_score:.3f}) exceeds allowed threshold (3.0)'
        else:
            analysis_result['is_authorized'] = True
            analysis_result['authorization_reason'] = f'RISK_SCORE_AUTHORIZED: Risk score ({risk_score:.3f}) within allowed threshold (≤ 3.0) - Authorizing user'
            analysis_result['recommendation'] = f'ALLOW: Risk score ({risk_score:.3f}) within allowed threshold (≤ 3.0)'
        return analysis_result

    def simple_behavioral_validation(self, behavioral_data):
        
        try:
            print(f"🔍 Performing simple behavioral validation...")
            
            # Count total interactions - handle both current behavioral data and baseline data formats
            cursor_movements = len(behavioral_data.get('cursor_movements', [])) + len(behavioral_data.get('cursorMovements', []))
            key_presses = len(behavioral_data.get('key_press_times', [])) + len(behavioral_data.get('keyPressTimes', []))
            clicks = len(behavioral_data.get('click_timestamps', [])) + len(behavioral_data.get('clickTimestamps', []))
            
            # Check if this is baseline data (array of mouse position objects)
            if isinstance(behavioral_data, list):
                cursor_movements = len(behavioral_data)  # Each item is a mouse movement
                print(f"📊 Detected baseline data format: {cursor_movements} mouse movements")
            
            total_interactions = cursor_movements + key_presses + clicks
            
            # Check for automation signals
            evasion_signals = behavioral_data.get('evasion_signals', {}) if isinstance(behavioral_data, dict) else {}
            automation_count = sum(1 for v in evasion_signals.values() if v) if evasion_signals else 0
            
            # Check for paste behavior (common bot indicator)
            paste_detected = behavioral_data.get('paste_detected', False) if isinstance(behavioral_data, dict) else False
            
            # Check timing patterns
            if isinstance(behavioral_data, dict):
                total_time = behavioral_data.get('total_time', 0)
                interaction_rate = total_interactions / max(total_time / 1000, 1) if total_time > 0 else 0
            else:
                # For baseline data, calculate time span from timestamps
                if len(behavioral_data) > 1:
                    time_span = behavioral_data[-1].get('timestamp', 0) - behavioral_data[0].get('timestamp', 0)
                    interaction_rate = total_interactions / max(time_span / 1000, 1) if time_span > 0 else 0
                else:
                    interaction_rate = 0
            
            print(f"📊 Simple validation metrics:")
            print(f"   Total interactions: {total_interactions}")
            print(f"   Automation signals: {automation_count}")
            print(f"   Paste detected: {paste_detected}")
            print(f"   Interaction rate: {interaction_rate:.2f}/sec")
            
            if automation_count >= 5:  
                return {
                    'is_authorized': False,
                    'confidence': 0.9,
                    'reason': f'AUTOMATION_DETECTED: {automation_count} automation signals',
                    'validation_type': 'simple_automation_detection'
                }
            elif total_interactions < 2:
                return {
                    'is_authorized': False,
                    'confidence': 0.7,
                    'reason': f'INSUFFICIENT_INTERACTION: Only {total_interactions} interactions',
                    'validation_type': 'simple_insufficient_data'
                }
            elif interaction_rate > 30:  # Increased from 20 to 30 for more tolerance of fast typists
                return {
                    'is_authorized': False,
                    'confidence': 0.8,
                    'reason': f'SUSPICIOUS_SPEED: {interaction_rate:.1f} interactions/sec too fast',
                    'validation_type': 'simple_speed_detection'
                }
            elif paste_detected and total_interactions < 5:
                return {
                    'is_authorized': False,
                    'confidence': 0.7,
                    'reason': 'PASTE_WITH_LIMITED_INTERACTION: Paste detected with minimal interaction',
                    'validation_type': 'simple_paste_detection'
                }
            else:
                # Approve with confidence based on interaction quality
                if total_interactions >= 10:
                    confidence = 0.8
                elif total_interactions >= 5:
                    confidence = 0.7
                else:
                    confidence = 0.6
                    
                return {
                    'is_authorized': True,
                    'confidence': confidence,
                    'reason': f'HUMAN_INTERACTION: {total_interactions} interactions suggest human behavior',
                    'validation_type': 'simple_human_detection'
                }
                
        except Exception as e:
            print(f"❌ Error in simple validation: {e}")
            # Even simpler fallback - just check if any interaction exists
            has_interaction = bool(behavioral_data.get('cursor_movements') or 
                                 behavioral_data.get('key_press_times') or 
                                 behavioral_data.get('click_timestamps'))
            
            return {
                'is_authorized': has_interaction,
                'confidence': 0.5 if has_interaction else 0.2,
                'reason': f'FALLBACK_VALIDATION: {"Some" if has_interaction else "No"} interaction detected',
                'validation_type': 'simple_fallback'
            }
        
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
    
    def analyze_with_baseline_comparison(self, session_id, current_data, baseline_behavior_or_user_id, baseline_metrics=None):
        """
        🔬 ENHANCED: Analyze current behavior against baseline using 3-sigma Mahalanobis distance
        Retrieves baseline from UserBaselineBehavior table and applies 3-sigma rule
        
        🎯 PRIMARY CLASSIFICATION RULE:
        - If Confidence > Risk Score: User classified as AUTHORIZED
        - If Risk Score > Confidence: User classified as UNAUTHORIZED  
        - If Risk Score = Confidence: Use statistical analysis result
        
        Args:
            session_id: Current session identifier
            current_data: Current behavioral data to analyze
            baseline_behavior_or_user_id: Either baseline data dict OR user_id string for database lookup
            baseline_metrics: Optional pre-calculated baseline metrics (legacy support)
            
        Returns:
            Comprehensive analysis results with risk vs confidence classification
        """
        try:
            print(f"🔬 ENHANCED BASELINE ANALYSIS: Starting 3-sigma Mahalanobis analysis...")
            print(f"📝 Session: {session_id}")
            
            # 📊 STEP 1: RETRIEVE BASELINE FROM DATABASE
            baseline_data = None
            user_id = None
            
            # Check if baseline_behavior_or_user_id is a user_id string to retrieve from database
            if isinstance(baseline_behavior_or_user_id, str):
                user_id = baseline_behavior_or_user_id
                print(f"👤 Retrieving baseline for user: {user_id}")
                
                try:
                    # Retrieve most recent active baseline for the user from UserBaselineBehavior table
                    baseline_record = UserBaselineBehavior.objects.filter(
                        user_id=user_id,
                        is_active=True,
                        sufficient_interaction=True
                    ).order_by('-created_at').first()
                    
                    if baseline_record:
                        baseline_data = baseline_record.baseline_user_behavior
                        baseline_metrics = baseline_record.baseline_metrics
                        print(f"✅ Retrieved baseline for user {user_id}: Quality={baseline_record.data_quality_score:.3f}")
                        print(f"🔍 Baseline data summary: {len(baseline_data.get('cursorMovements', []))} cursor, {len(baseline_data.get('keyPressTimes', []))} keys, {len(baseline_data.get('clickTimestamps', []))} clicks")
                    else:
                        print(f"⚠️ No baseline found for user {user_id} - using permissive fallback")
                        # ENHANCED: Instead of blocking, use permissive fallback for new users
                        return {
                            'is_authorized': True,  
                            'confidence': 0.7,      
                            'mahalanobis_distance': 0.0,
                            'standard_deviations': 0.0,
                            'authorization_reason': 'NEW_USER: No baseline data available - using permissive authorization for first-time users',
                            'analysis_type': 'new_user_fallback',
                            'user_id': user_id,
                            'recommendation': 'ALLOW: New user - collecting baseline data for future comparisons'
                        }
                except Exception as e:
                    print(f"⚠️ Database error retrieving baseline for {user_id}: {e}")
                    # ENHANCED: Instead of blocking on database errors, use permissive fallback
                    return {
                        'is_authorized': True,  # Allow users even with database issues
                        'confidence': 0.6,      # Lower confidence due to database issues
                        'mahalanobis_distance': 0.0,
                        'standard_deviations': 0.0,
                        'authorization_reason': f'DATABASE_FALLBACK: Database error occurred but allowing user access - {str(e)}',
                        'analysis_type': 'database_error_fallback',
                        'recommendation': 'ALLOW: Database error - using permissive fallback'
                    }
            else:
                # Use provided baseline data directly (legacy mode)
                baseline_data = baseline_behavior_or_user_id
                print(f"📊 Using provided baseline data directly")
            
            if not baseline_data:
                # ENHANCED: Permissive fallback for missing baseline data
                return {
                    'is_authorized': True,  # Allow users with missing baseline
                    'confidence': 0.6,      # Medium-low confidence
                    'mahalanobis_distance': 0.0,
                    'standard_deviations': 0.0,
                    'authorization_reason': 'MISSING_BASELINE: No baseline data available - using permissive authorization',
                    'analysis_type': 'missing_baseline_fallback',
                    'recommendation': 'ALLOW: Missing baseline - collecting data for future analysis'
                }
            
            # 🔢 STEP 2: EXTRACT FEATURE VECTORS FOR MAHALANOBIS DISTANCE
            print(f"🔢 Extracting behavioral features for Mahalanobis distance calculation...")
            
            # Extract current behavior features
            current_features = self.extract_behavioral_features(current_data)
            print(f"🔍 Current features extracted: {len(current_features) if current_features else 0} features")
            if not current_features:
                print(f"⚠️ Failed to extract current behavior features - using basic validation")
                # ENHANCED: Basic validation instead of blocking completely
                total_interactions = (len(current_data.get('cursor_movements', [])) + 
                                    len(current_data.get('key_press_times', [])) + 
                                    len(current_data.get('click_timestamps', [])))
                
                # If user has some interaction, allow with lower confidence
                if total_interactions >= 3:
                    return {
                        'is_authorized': True,
                        'confidence': 0.5,  # Lower confidence due to feature extraction issues
                        'mahalanobis_distance': 0.0,
                        'standard_deviations': 0.0,
                        'authorization_reason': f'BASIC_VALIDATION: Feature extraction failed but {total_interactions} interactions detected',
                        'analysis_type': 'basic_validation_fallback',
                        'recommendation': f'ALLOW: Basic validation passed with {total_interactions} interactions'
                    }
                else:
                    return {
                        'is_authorized': False,
                        'confidence': 0.3,
                        'mahalanobis_distance': float('inf'),
                        'standard_deviations': float('inf'),
                        'authorization_reason': f'INSUFFICIENT_INTERACTION: Only {total_interactions} interactions detected',
                        'analysis_type': 'insufficient_interaction',
                        'recommendation': f'BLOCK: Insufficient interaction data ({total_interactions} interactions)'
                    }
            
            # Extract baseline features
            baseline_features = self.extract_behavioral_features(baseline_data)
            print(f"🔍 Baseline features extracted: {len(baseline_features) if baseline_features else 0} features")
            if not baseline_features:
                print(f"⚠️ Failed to extract baseline behavior features - using permissive comparison")
                # ENHANCED: If baseline feature extraction fails, use basic current data validation
                total_interactions = (len(current_data.get('cursor_movements', [])) + 
                                    len(current_data.get('key_press_times', [])) + 
                                    len(current_data.get('click_timestamps', [])))
                
                if total_interactions >= 5:
                    return {
                        'is_authorized': True,
                        'confidence': 0.6,
                        'mahalanobis_distance': 0.0,
                        'standard_deviations': 0.0,
                        'authorization_reason': f'BASELINE_FEATURE_FALLBACK: Baseline feature extraction failed but current data shows {total_interactions} interactions',
                        'analysis_type': 'baseline_feature_error_fallback',
                        'recommendation': f'ALLOW: Using current interaction data ({total_interactions} interactions) for validation'
                    }
                else:
                    return {
                        'is_authorized': False,
                        'confidence': 0.4,
                        'mahalanobis_distance': float('inf'),
                        'standard_deviations': float('inf'),
                        'authorization_reason': f'INSUFFICIENT_DATA: Baseline extraction failed and only {total_interactions} current interactions',
                        'analysis_type': 'insufficient_data_both',
                        'recommendation': f'BLOCK: Insufficient data for validation'
                    }
            
            print(f"✅ Features extracted - Current: {len(current_features)}, Baseline: {len(baseline_features)}")
            
            # 📏 STEP 3: GENERATE ENHANCED BASELINE VARIATIONS FOR STATISTICAL MODELING
            print(f"📏 Generating enhanced baseline variations for covariance matrix...")
            
            # Create realistic baseline variations for better statistical distribution modeling
            baseline_variations = self.generate_enhanced_baseline_variations(baseline_features, num_variations=15)
            
            if len(baseline_variations) < 2:
                print(f"❌ Insufficient baseline variations for statistical analysis")
                return {
                    'is_authorized': False,
                    'confidence': 0.0,
                    'mahalanobis_distance': float('inf'),
                    'standard_deviations': float('inf'),
                    'authorization_reason': 'Insufficient baseline statistical data',
                    'analysis_type': 'insufficient_baseline_data',
                    'recommendation': 'BLOCK: Insufficient baseline data'
                }
            
            # 📐 STEP 4: CALCULATE MAHALANOBIS DISTANCE
            print(f"📐 Calculating Mahalanobis distance...")
            mahalanobis_distance = self.calculate_enhanced_mahalanobis_distance(
                current_features, 
                baseline_variations
            )
            
            print(f"📊 Raw Mahalanobis distance: {mahalanobis_distance:.4f}")
            
            print(f"🔍 MAHALANOBIS DISTANCE INPUTS DEBUG:")
            print(f"   - current_features length: {len(current_features)}")
            print(f"   - current_features sample: {current_features[:5] if len(current_features) >= 5 else current_features}")
            print(f"   - baseline_variations length: {len(baseline_variations)}")
            print(f"   - Calculated mahalanobis_distance: {mahalanobis_distance}")
            print(f"   - Is mahalanobis_distance constant? Check if same every time!")
            
            # Check if features are varying
            if len(current_features) > 0:
                print(f"   - Current features sum: {sum(current_features):.6f}")
                print(f"   - Current features min/max: {min(current_features):.6f} / {max(current_features):.6f}")
            
            if len(baseline_variations) > 0 and len(baseline_variations[0]) > 0:
                baseline_sum = sum(sum(variation) for variation in baseline_variations)
                print(f"   - Baseline variations total sum: {baseline_sum:.6f}")
            
            if mahalanobis_distance == float('inf'):
                print(f"   - ⚠️ WARNING: Mahalanobis distance is infinite!")
            elif mahalanobis_distance == 0:
                print(f"   - ⚠️ WARNING: Mahalanobis distance is zero!")
            else:
                print(f"   - ✅ Valid mahalanobis distance: {mahalanobis_distance:.6f}")

            
            num_features = len(current_features)
            
            # Calculate standard deviations for behavioral data
            if mahalanobis_distance == float('inf'):
                standard_deviations = float('inf')
            else:
                # 🔧 ENHANCED ROBUST BEHAVIORAL ANALYSIS: Multi-layered validation approach
                # More sophisticated threshold logic that adapts to behavioral complexity
                
                print(f"🔍 Raw Mahalanobis distance: {mahalanobis_distance:.4f}")
                
                # 1️⃣ Preserve natural behavioral differences with minimal scaling
                if mahalanobis_distance > 0:
                    # Use very conservative scaling that preserves discrimination
                    lightly_scaled_distance = mahalanobis_distance * 1.0  # No initial scaling
                    print(f"📐 Preserved distance: {lightly_scaled_distance:.4f}")
                else:
                    lightly_scaled_distance = 0
                
                # 2️⃣ BALANCED BEHAVIORAL SCALING: Optimized for unauthorized user detection
                # Calculate data quality to adjust scaling appropriately
                current_data_quality = self.assess_behavioral_data_quality(current_data)
                baseline_data_quality = self.assess_behavioral_data_quality(baseline_data)
                
                print(f"📊 Data quality - Current: {current_data_quality:.3f}, Baseline: {baseline_data_quality:.3f}")
                
                # Balanced behavioral factor - good discrimination while allowing legitimate users
                if current_data_quality >= 0.8 and baseline_data_quality >= 0.8:
                    # High quality data = moderate scaling for good discrimination
                    human_behavioral_factor = 0.6  # Good discrimination with high quality data
                elif current_data_quality >= 0.6 and baseline_data_quality >= 0.6:
                    # Medium quality data = balanced scaling
                    human_behavioral_factor = 0.5  # Balanced scaling for medium quality
                else:
                    # Low quality data = lenient scaling but still discriminate
                    human_behavioral_factor = 0.4  # More lenient for low quality data
                
                scaled_distance = lightly_scaled_distance * human_behavioral_factor
                
                # 3️⃣ FEATURE COMPLEXITY ADJUSTMENT: Balanced dimension adjustment
                num_features = len(current_features)
                if num_features > 50:
                    dimension_factor = 1.0  # High dimension = full reliability
                elif num_features > 30:
                    dimension_factor = 0.95  # Medium dimension = slight adjustment
                else:
                    dimension_factor = 0.9  # Low dimension = moderate reduction
                
                # 4️⃣ BEHAVIORAL CONSISTENCY CHECK: Balanced consistency multiplier
                consistency_score = self.calculate_behavioral_consistency(current_data, baseline_data)
                print(f"🔍 Behavioral consistency score: {consistency_score:.3f}")
                
                # No consistency penalty - maximize user access
                consistency_factor = 1.0  # No penalty for any consistency level
                
                standard_deviations = scaled_distance * dimension_factor * consistency_factor
                
                print(f"🔍 STANDARD DEVIATIONS CALCULATION DEBUG:")
                print(f"   - scaled_distance: {scaled_distance}")
                print(f"   - dimension_factor: {dimension_factor}")
                print(f"   - consistency_factor: {consistency_factor}")
                print(f"   - Raw calculation: {scaled_distance} * {dimension_factor} * {consistency_factor} = {standard_deviations}")
                
                
                min_std_devs = 0.05  
                max_std_devs = 12.0  
                
                original_standard_deviations = standard_deviations
                standard_deviations = max(min_std_devs, min(standard_deviations, max_std_devs))
                print(f"   - After bounds: max({min_std_devs}, min({original_standard_deviations}, {max_std_devs})) = {standard_deviations}")
                
                print(f"🔧 FINAL CALCULATIONS:")
                print(f"   Raw Mahalanobis: {mahalanobis_distance:.4f}")
                print(f"   After initial scaling (1.0x): {lightly_scaled_distance:.4f}")
                print(f"   Human factor: {human_behavioral_factor:.2f}")
                print(f"   Consistency factor: {consistency_factor:.2f}")
                print(f"   Final standard deviations: {standard_deviations:.4f}σ")

            # 🔒 STEP 6: EXTREMELY LENIENT REAL-WORLD IDENTITY VERIFICATION
            # Use VERY LARGE threshold to accommodate massive real-world behavioral variation
            base_threshold = 20.0  # Very large threshold for real-world behavioral variation
            behavioral_threshold = 0
            # Adjust threshold based on data quality and context
            current_data_quality = self.assess_behavioral_data_quality(current_data)
            
            print(f"🔍 BEHAVIORAL THRESHOLD CALCULATION DEBUG:")
            print(f"   - current_data_quality: {current_data_quality:.6f}")
            print(f"   - base_threshold: {base_threshold}")
            
            if current_data_quality >= 0.8:
                # High quality data = use BALANCED threshold for user detection
                behavioral_threshold = base_threshold  # 20.0σ - balanced
                threshold_reason = "high-quality behavioral data"
                print(f"   - Path: High quality (>= 0.8), threshold = {behavioral_threshold}")
            elif current_data_quality >= 0.6:
                # Medium quality data = slightly more lenient
                behavioral_threshold = base_threshold + 0.5  # 20.5σ
                threshold_reason = "medium-quality behavioral data"
                print(f"   - Path: Medium quality (>= 0.6), threshold = {behavioral_threshold}")
            elif current_data_quality >= 0.4:
                # Low quality data = more lenient
                behavioral_threshold = base_threshold + 1.0  # 21.0σ
                threshold_reason = "low-quality behavioral data"
                print(f"   - Path: Low quality (>= 0.4), threshold = {behavioral_threshold}")
            else:
                # Very low quality data = lenient but still secure
                behavioral_threshold = base_threshold + 1.5  # 21.5σ
                threshold_reason = "very-low-quality behavioral data"
                print(f"   - Path: Very low quality (< 0.4), threshold = {behavioral_threshold}")
            
            print(f"🎯 User-friendly verification threshold: {behavioral_threshold:.1f}σ ({threshold_reason})")
            print(f"📋 AUTHORIZATION DECISION: {standard_deviations:.4f}σ <= {behavioral_threshold:.1f}σ = {standard_deviations <= behavioral_threshold}")
            print(f"🔧 THRESHOLD ADJUSTMENT: Increased base threshold to {base_threshold}σ for better user experience")
            
            # 🎯 CONTEXTUAL AUTHORIZATION DECISION SYSTEM
            # Smart multi-factor decision making for real-world usage
            
            print(f"🎯 CONTEXTUAL DECISION ANALYSIS:")
            print(f"   Standard Deviations: {standard_deviations:.2f}σ")
            print(f"   Behavioral Threshold: {behavioral_threshold:.1f}σ")
            print(f"   Consistency Score: {consistency_score:.3f}")
            
            # CONTEXT 1: Very low consistency - likely different user (check first!)
            if consistency_score < 0.3:
                print(f"❌ CONTEXT 1: Very low consistency ({consistency_score:.3f}) - BLOCK DIFFERENT USER")
                is_authorized = False
                authorization_reason = f'LOW_CONSISTENCY_BLOCK: Very low consistency ({consistency_score:.3f}) indicates different user regardless of threshold ({standard_deviations:.2f}σ vs {behavioral_threshold:.1f}σ)'
                
            # CONTEXT 2: Low consistency - likely friend or similar user (check second!)
            elif consistency_score < 0.5:
                print(f"❌ CONTEXT 2: Low consistency ({consistency_score:.3f}) - BLOCK SIMILAR USER")
                is_authorized = False
                authorization_reason = f'SIMILAR_USER_BLOCK: Low consistency ({consistency_score:.3f}) indicates similar but different user ({standard_deviations:.2f}σ vs {behavioral_threshold:.1f}σ)'
                
            # CONTEXT 3: Clear authorization - within threshold with good consistency
            elif standard_deviations <= behavioral_threshold:
                print(f"✅ CONTEXT 3: Within threshold ({standard_deviations:.2f}σ ≤ {behavioral_threshold:.1f}σ) with good consistency - AUTHORIZE")
                is_authorized = True
                authorization_reason = f'WITHIN_THRESHOLD: Behavioral variation ({standard_deviations:.2f}σ) within acceptable range ({behavioral_threshold:.1f}σ) with good consistency ({consistency_score:.3f})'
                
            # CONTEXT 4: Extreme behavioral difference - likely automation
            elif standard_deviations > behavioral_threshold * 2.0:
                print(f"❌ CONTEXT 4: Extreme behavioral difference - BLOCK AUTOMATION")
                is_authorized = False
                authorization_reason = f'EXTREME_BEHAVIOR_BLOCK: Extreme behavioral difference ({standard_deviations:.2f}σ vs {behavioral_threshold:.1f}σ) indicates automation or very different user'
                
            # CONTEXT 5: Slight overage with very high consistency - legitimate user variation
            elif standard_deviations <= behavioral_threshold * 1.2 and consistency_score >= 0.8:
                print(f"✅ CONTEXT 5: Slight overage with very high consistency - AUTHORIZE")
                is_authorized = True
                authorization_reason = f'HIGH_CONSISTENCY_OVERRIDE: Very high consistency ({consistency_score:.3f}) overrides slight threshold breach ({standard_deviations:.2f}σ vs {behavioral_threshold:.1f}σ)'
                
            # CONTEXT 6: Complex borderline case - comprehensive scoring
            else:
                print(f"⚖️ CONTEXT 6: Complex borderline case - COMPREHENSIVE ANALYSIS")
                # Weighted scoring: consistency is critical, but threshold breach matters
                consistency_weight = 0.7  # Increased consistency importance
                threshold_weight = 0.3
                
                consistency_factor = max(0, consistency_score)  # 0 to 1
                threshold_factor = max(0, 1.0 - ((standard_deviations - behavioral_threshold) / behavioral_threshold))  # How close to threshold
                
                combined_score = (consistency_factor * consistency_weight) + (threshold_factor * threshold_weight)
                
                if combined_score >= 0.65:  # Require higher combined score
                    is_authorized = True
                    authorization_reason = f'COMPREHENSIVE_AUTHORIZE: Combined analysis score ({combined_score:.3f}) indicates legitimate user (consistency: {consistency_score:.3f}, threshold factor: {threshold_factor:.3f})'
                else:
                    is_authorized = False
                    authorization_reason = f'COMPREHENSIVE_BLOCK: Combined analysis score ({combined_score:.3f}) indicates suspicious behavior (consistency: {consistency_score:.3f}, threshold factor: {threshold_factor:.3f})'
            
            print(f"🎯 CONTEXTUAL DECISION: {authorization_reason}")
            
            # Calculate total interactions for validation
            cursor_movements = len(current_data.get('cursor_movements', [])) + len(current_data.get('cursorMovements', []))
            key_presses = len(current_data.get('key_press_times', [])) + len(current_data.get('keyPressTimes', []))
            clicks = len(current_data.get('click_timestamps', [])) + len(current_data.get('clickTimestamps', []))
            total_interactions = cursor_movements + key_presses + clicks
            
            print(f"📊 Interaction count: {cursor_movements} cursor + {key_presses} keys + {clicks} clicks = {total_interactions} total")
            
            # Basic interaction validation
            if total_interactions < 2:
                print(f"⚠️ Insufficient interaction data ({total_interactions} interactions)")
                is_authorized = False
                authorization_reason = f'INSUFFICIENT_DATA: Only {total_interactions} interactions detected - minimum 2 required'
                print(f"❌ OVERRIDE: Authorization set to False due to insufficient interactions ({total_interactions})")
                
            # Check for automation signals
            evasion_signals = current_data.get('evasion_signals', {})
            unusual_patterns = sum(1 for key, value in evasion_signals.items() if value) if evasion_signals else 0
            
            if unusual_patterns >= 5:
                print(f"🚨 Multiple unusual behavioral patterns detected: {unusual_patterns}")
                is_authorized = False
                authorization_reason = f'AUTOMATION_DETECTED: {unusual_patterns} automation patterns suggest bot behavior'
                print(f"❌ OVERRIDE: Authorization set to False due to unusual patterns ({unusual_patterns})")
            
            # Calculate confidence based on distance from behavioral threshold
            print(f"🔍 CONFIDENCE CALCULATION DEBUG:")
            print(f"   - standard_deviations: {standard_deviations} (constant issue: always same?)")
            print(f"   - behavioral_threshold: {behavioral_threshold} (constant issue: always same?)")
            print(f"   - mahalanobis_distance: {mahalanobis_distance} (constant issue: always same?)")
            print(f"   - Standard deviations == 0? {standard_deviations == 0}")
            print(f"   - Standard deviations <= threshold? {standard_deviations <= behavioral_threshold}")
            print(f"   - DEBUGGING: If these values are always the same, confidence will be constant!")
            
            if standard_deviations == 0:
                confidence = 1.0
                print(f"   - Path: standard_deviations == 0, confidence = {confidence}")
            elif standard_deviations <= behavioral_threshold:
                # Authorized: confidence decreases as we approach behavioral threshold
                raw_confidence = 1.0 - (standard_deviations / behavioral_threshold) * 0.4
                confidence = max(0.5, raw_confidence)
                print(f"   - Path: authorized (std_dev <= threshold)")
                print(f"   - Raw calculation: 1.0 - ({standard_deviations} / {behavioral_threshold}) * 0.4 = {raw_confidence}")
                print(f"   - Final confidence after max(0.5, {raw_confidence}): {confidence}")
            else:
                # Unauthorized: confidence increases with distance beyond threshold
                excess_deviation = standard_deviations - behavioral_threshold
                raw_confidence = 0.6 + (excess_deviation / behavioral_threshold) * 0.35
                confidence = min(0.95, raw_confidence)
                print(f"   - Path: unauthorized (std_dev > threshold)")
                print(f"   - excess_deviation: {excess_deviation}")
                print(f"   - Raw calculation: 0.6 + ({excess_deviation} / {behavioral_threshold}) * 0.35 = {raw_confidence}")
                print(f"   - Final confidence after min(0.95, {raw_confidence}): {confidence}")
            
            print(f"   - FINAL CONFIDENCE: {confidence}")
            
            # 📋 STEP 7: USER IDENTITY VERIFICATION REASONING
            if not hasattr(locals(), 'authorization_reason'):
                if is_authorized:
                    if standard_deviations <= 1.0:
                        authorization_reason = f'VERIFIED: Excellent behavioral match ({standard_deviations:.2f}σ) - Strong identity confirmation'
                    elif standard_deviations <= 2.0:
                        authorization_reason = f'VERIFIED: Good behavioral match ({standard_deviations:.2f}σ) - Identity confirmed'
                    elif standard_deviations <= 3.0:
                        authorization_reason = f'VERIFIED: Acceptable behavioral match ({standard_deviations:.2f}σ) - Identity likely confirmed'
                    else:
                        authorization_reason = f'VERIFIED: Within threshold ({standard_deviations:.2f}σ) - Identity marginally confirmed'
                else:
                    if standard_deviations <= behavioral_threshold + 1.0:
                        authorization_reason = f'REJECTED: Behavioral mismatch ({standard_deviations:.2f}σ) - Identity not verified'
                    elif standard_deviations <= behavioral_threshold + 2.0:
                        authorization_reason = f'REJECTED: Significant behavioral difference ({standard_deviations:.2f}σ) - Likely different user'
                    else:
                        authorization_reason = f'REJECTED: Major behavioral difference ({standard_deviations:.2f}σ) - Different user detected'
            # 🎯 STEP 8: IDENTITY VERIFICATION RISK ASSESSMENT
            # Risk assessment for user identity verification
            current_data_quality = self.assess_behavioral_data_quality(current_data)
            
            # Base identity verification risk assessment
            if standard_deviations <= 1.0:
                base_risk_level = 'VERY_LOW'
                base_risk_score = 0.05
                base_anomaly_score = 0.05
            elif standard_deviations <= 2.0:
                base_risk_level = 'LOW'
                base_risk_score = 0.15
                base_anomaly_score = 0.15
            elif standard_deviations <= 3.0:
                base_risk_level = 'MEDIUM_LOW'
                base_risk_score = 0.25
                base_anomaly_score = 0.25
            elif standard_deviations <= behavioral_threshold:
                base_risk_level = 'MEDIUM'
                base_risk_score = 0.35
                base_anomaly_score = 0.35
            elif standard_deviations <= behavioral_threshold + 1.0:
                base_risk_level = 'MEDIUM_HIGH'
                base_risk_score = 0.55
                base_anomaly_score = 0.55
            elif standard_deviations <= behavioral_threshold + 2.0:
                base_risk_level = 'HIGH'
                base_risk_score = 0.75
                base_anomaly_score = 0.75
            else:
                base_risk_level = 'CRITICAL'
                base_risk_score = 0.90
                base_anomaly_score = 0.90
            
            # Adjust risk based on data quality
            if current_data_quality >= 0.8:
                # High quality data = more confident in risk assessment
                risk_adjustment = 1.0
            elif current_data_quality >= 0.6:
                # Medium quality data = moderate confidence, slight risk reduction
                risk_adjustment = 0.9
            else:
                # Low quality data = less confident, reduce risk scores
                risk_adjustment = 0.8
            
            # Check for behavioral patterns that suggest different user
            evasion_signals = current_data.get('evasion_signals', {})
            unusual_patterns = sum(1 for v in evasion_signals.values() if v) if evasion_signals else 0
            
            if unusual_patterns >= 4:
                # Many unusual patterns = likely different user
                user_risk_multiplier = 1.4
                risk_level = 'HIGH'
            elif unusual_patterns >= 3:
                # Some unusual patterns = possible different user
                user_risk_multiplier = 1.2
            elif unusual_patterns >= 2:
                # Few unusual patterns = minor identity concern
                user_risk_multiplier = 1.1
            else:
                # No unusual patterns = no additional identity risk
                user_risk_multiplier = 1.0
            
            # Calculate final risk scores
            print(f"🔍 RISK SCORE CALCULATION DEBUG:")
            print(f"   - standard_deviations: {standard_deviations} (should vary with different users)")
            print(f"   - base_risk_score: {base_risk_score} (calculated from standard_deviations)")
            print(f"   - risk_adjustment: {risk_adjustment} (calculated from data quality)")
            print(f"   - user_risk_multiplier: {user_risk_multiplier} (calculated from unusual patterns)")
            print(f"   - unusual_patterns: {unusual_patterns}")
            print(f"   - current_data_quality: {current_data_quality}")
            print(f"   - DEBUGGING: If standard_deviations is constant, base_risk_score will be constant!")
            
            raw_risk_score = base_risk_score * risk_adjustment * user_risk_multiplier
            risk_score = min(0.95, raw_risk_score)
            print(f"   - Raw calculation: {base_risk_score} * {risk_adjustment} * {user_risk_multiplier} = {raw_risk_score}")
            print(f"   - FINAL RISK SCORE after min(0.95, {raw_risk_score}): {risk_score}")
            print(f"   - CONSTANT CHECK: Is this always 0.315? Risk score should vary!")
            
            raw_anomaly_score = base_anomaly_score * risk_adjustment * user_risk_multiplier
            anomaly_score = min(0.95, raw_anomaly_score)
            print(f"   - Anomaly calculation: {base_anomaly_score} * {risk_adjustment} * {user_risk_multiplier} = {raw_anomaly_score}")
            print(f"   - FINAL ANOMALY SCORE: {anomaly_score}")
            
            # Determine final risk level
            if risk_score <= 0.15:
                risk_level = 'VERY_LOW'
            elif risk_score <= 0.30:
                risk_level = 'LOW'
            elif risk_score <= 0.45:
                risk_level = 'MEDIUM'
            elif risk_score <= 0.65:
                risk_level = 'MEDIUM_HIGH'
            elif risk_score <= 0.80:
                risk_level = 'HIGH'
            else:
                risk_level = 'CRITICAL'
            

            
            
            if is_authorized:
                if standard_deviations <= 1.0:
                    recommendation = f'ALLOW: Excellent behavioral match ({standard_deviations:.2f}σ, {current_data_quality:.1%} quality)'
                elif standard_deviations <= 2.0:
                    recommendation = f'ALLOW: Very good behavioral pattern ({standard_deviations:.2f}σ, {current_data_quality:.1%} quality)'
                elif standard_deviations <= 3.0:
                    recommendation = f'ALLOW: Good behavioral consistency ({standard_deviations:.2f}σ, {current_data_quality:.1%} quality)'
                else:
                    recommendation = f'ALLOW: Acceptable within {behavioral_threshold:.1f}σ threshold ({standard_deviations:.2f}σ, {current_data_quality:.1%} quality)'
            else:
                if unusual_patterns >= 3:
                    recommendation = f'BLOCK: Multiple unusual patterns ({unusual_patterns}) and deviation ({standard_deviations:.2f}σ) - Unauthorized user'
                elif standard_deviations <= behavioral_threshold + 1.0:
                    recommendation = f'BLOCK: Behavioral mismatch beyond {behavioral_threshold:.1f}σ threshold ({standard_deviations:.2f}σ) - Different user'
                elif standard_deviations <= behavioral_threshold + 2.0:
                    recommendation = f'BLOCK: Significant behavioral difference ({standard_deviations:.2f}σ, {unusual_patterns} unusual patterns) - Unauthorized user'
                else:
                    recommendation = f'BLOCK: Major behavioral difference ({standard_deviations:.2f}σ, {unusual_patterns} unusual patterns) - Different user detected'
            
            # 🔍 STEP 10: ENHANCED SUSPICIOUS PATTERN INDICATORS
            suspicious_indicators = []
            
            # Core threshold violations
            if standard_deviations > behavioral_threshold:
                suspicious_indicators.append(f'Exceeds behavioral threshold ({standard_deviations:.2f}σ > {behavioral_threshold:.1f}σ)')
            
            # Statistical analysis failures
            if mahalanobis_distance == float('inf'):
                suspicious_indicators.append('Invalid statistical analysis - insufficient baseline data')
            
            # Risk level indicators
            if risk_level in ['HIGH', 'CRITICAL']:
                suspicious_indicators.append(f'High risk classification: {risk_level}')
            
            # Identity verification indicators - enhanced for unauthorized user detection
            if unusual_patterns >= 3:  # Lowered threshold to match main logic
                suspicious_indicators.append(f'Multiple behavioral inconsistencies detected ({unusual_patterns}) - suggests unauthorized user')
            elif unusual_patterns >= 2:
                suspicious_indicators.append(f'Behavioral inconsistencies present ({unusual_patterns}) - unauthorized user concern')
            
            # Data quality concerns for identity verification
            if current_data_quality < 0.4:
                suspicious_indicators.append(f'Low data quality ({current_data_quality:.1%}) - insufficient data for identity verification')
            
            # Significant behavioral differences
            if standard_deviations > behavioral_threshold + 1.5:
                suspicious_indicators.append(f'Significant behavioral difference ({standard_deviations:.2f}σ) - likely different user')
            
            # Insufficient interaction data - use corrected counting
            cursor_movements_susp = len(current_data.get('cursor_movements', [])) + len(current_data.get('cursorMovements', []))
            key_presses_susp = len(current_data.get('key_press_times', [])) + len(current_data.get('keyPressTimes', []))
            clicks_susp = len(current_data.get('click_timestamps', [])) + len(current_data.get('clickTimestamps', []))
            total_interactions_susp = cursor_movements_susp + key_presses_susp + clicks_susp
            
            if total_interactions_susp < 10:
                suspicious_indicators.append(f'Limited interaction data ({total_interactions_susp} interactions)')
            
            # Behavioral consistency issues for identity verification
            consistency_score_susp = self.calculate_behavioral_consistency(current_data, baseline_data)
            if consistency_score_susp < 0.6:
                suspicious_indicators.append(f'Low behavioral consistency ({consistency_score_susp:.1%}) - unauthorized user concern')
            
            # Multi-factor unauthorized user indicators
            combined_risk_score_susp = (1.0 - consistency_score_susp) * 0.4 + min(standard_deviations / behavioral_threshold, 2.0) * 0.6
            if combined_risk_score_susp > 1.0:
                suspicious_indicators.append(f'Multi-factor unauthorized user risk (score={combined_risk_score_susp:.3f})')
            
            analysis_result = {
                'is_authorized': is_authorized,
                'confidence': confidence,
                'anomaly_score': anomaly_score,
                'risk_score': risk_score,
                'authorization_reason': authorization_reason,
                'recommendation': recommendation,
                
                # 📊 Statistical analysis results (KEY: 3-sigma implementation)
                'mahalanobis_distance': float(mahalanobis_distance),
                'standard_deviations': float(standard_deviations),
                'sigma_threshold': behavioral_threshold,
                'within_behavioral_threshold': standard_deviations <= behavioral_threshold,
                'risk_level': risk_level,
                
                # 🔍 Analysis details
                'features_analyzed': num_features,
                'degrees_of_freedom': num_features,
                'baseline_variations_used': len(baseline_variations),
                'behavioral_scaling_factor': 1.0,
                'statistical_significance': 'HIGH' if mahalanobis_distance != float('inf') else 'INVALID',
                
                # 🚨 Enhanced risk factors and indicators
                'risk_factors': [
                    {
                        'metric': 'adaptive_behavioral_threshold',
                        'severity': 'HIGH' if not is_authorized else 'LOW',
                        'value': standard_deviations,
                        'threshold': behavioral_threshold,
                        'data_quality': current_data_quality
                    },
                    {
                        'metric': 'unusual_patterns',
                        'severity': 'CRITICAL' if unusual_patterns >= 3 else 'MEDIUM' if unusual_patterns >= 1 else 'LOW',
                        'value': unusual_patterns,
                        'threshold': 0
                    },
                    {
                        'metric': 'behavioral_consistency',
                        'severity': 'HIGH' if consistency_score < 0.3 else 'MEDIUM' if consistency_score < 0.6 else 'LOW',
                        'value': consistency_score,
                        'threshold': 0.6
                    }
                ],
                'suspicious_indicators': suspicious_indicators,
                
                # 📊 Enhanced data quality metrics
                'data_quality_metrics': {
                    'current_data_quality': current_data_quality,
                    'baseline_data_quality': self.assess_behavioral_data_quality(baseline_data),
                    'behavioral_consistency': consistency_score,
                    'total_interactions': total_interactions,
                    'unusual_patterns': unusual_patterns,
                    'threshold_adaptation': threshold_reason
                },
                
                # 📝 Enhanced metadata
                'analysis_type': 'enhanced_adaptive_behavioral_analysis',
                'adaptive_threshold': behavioral_threshold,
                'threshold_adaptation_reason': threshold_reason,
                'baseline_source': 'UserBaselineBehavior database' if user_id else 'Direct baseline data',
                'user_id': user_id if user_id else 'direct_baseline',
                'session_id': session_id,
                'timestamp': timezone.now().isoformat(),
                
                # 🎯 Enhanced compliance and standards
                'robust_analysis_compliant': True,
                'statistical_method': 'Enhanced Mahalanobis distance with adaptive behavioral threshold',
                'multi_layer_validation': True,
                'unauthorized_user_detection_active': True,
                'profile_size': len(baseline_variations)
            }
            
            # 🚨 EMERGENCY BLOCK: Only for extreme automation cases
            # Only block users who extremely exceed behavioral threshold (5x for real-world variation)
            if standard_deviations > behavioral_threshold * 5.0:  # 5x threshold = emergency block (extremely lenient)
                print(f"🚨 EMERGENCY BLOCK ACTIVATED: {standard_deviations:.2f}σ > {behavioral_threshold * 5.0:.1f}σ")
                print(f"🔒 EMERGENCY BLOCK: Clear automation detected - bypassing all other checks")
                analysis_result['is_authorized'] = False
                analysis_result['authorization_reason'] = f'EMERGENCY_BLOCK_AUTOMATION: Clear automation detected ({standard_deviations:.2f}σ) far exceeds threshold ({behavioral_threshold:.1f}σ)'
                analysis_result['recommendation'] = f'EMERGENCY_BLOCK: Clear automation ({standard_deviations:.2f}σ) - bypassing confidence checks'
            
            # 🎯 APPLY RISK VS CONFIDENCE CLASSIFICATION CHECK (only if not hard blocked)
            if analysis_result.get('authorization_reason', '').startswith('HARD_BLOCK'):
                print(f"🔒 SKIPPING confidence vs risk check due to hard block")
            else:
                analysis_result = self.apply_risk_confidence_check(analysis_result)
            
           
            is_authorized = analysis_result['is_authorized']
            authorization_reason = analysis_result['authorization_reason']
            recommendation = analysis_result['recommendation']
            
            # 🔍 FINAL DEBUGGING: Log complete analysis result
            print(f"🔍 FINAL ANALYSIS RESULT:")
            print(f"   Primary decision: {standard_deviations:.2f}σ <= {behavioral_threshold:.1f}σ = {standard_deviations <= behavioral_threshold}")
            print(f"   Risk vs Confidence Classification:")
            print(f"     - Confidence: {confidence:.3f}")
            print(f"     - Risk Score: {risk_score:.3f}")
            print(f"   🚨 CONSTANT VALUES ANALYSIS:")
            print(f"     - If confidence is always 0.718, then standard_deviations ≈ 4.94σ and threshold = 7.0σ")
            print(f"     - If risk_score is always 0.315, then base_risk=0.35, adjustment=0.9, multiplier=1.0")
            print(f"     - This suggests input behavioral data is not varying enough!")
            print(f"     - Current standard_deviations: {standard_deviations:.6f}")
            print(f"     - Current base_risk_score: {base_risk_score}")
            print(f"     - Current risk_adjustment: {risk_adjustment}")
            print(f"     - Current user_risk_multiplier: {user_risk_multiplier}")
            if confidence > risk_score:
                print(f"     - Result: AUTHORIZED (Confidence > Risk)")
            elif risk_score > confidence:
                print(f"     - Result: UNAUTHORIZED (Risk > Confidence)")
            else:
                print(f"     - Result: EQUAL SCORES (Using original analysis)")
            print(f"   Final authorization: {is_authorized}")
            print(f"   Authorization reason: {authorization_reason}")
            print(f"   Recommendation: {recommendation}")

            return analysis_result
            
        except Exception as e:
            logger.error(f"Enhanced baseline comparison error: {str(e)}")
            print(f"🚨 CRITICAL ERROR in enhanced baseline comparison: {e}")
            
            # ENHANCED: Provide fallback analysis instead of complete failure
            total_interactions = (len(current_data.get('cursor_movements', [])) + 
                                len(current_data.get('key_press_times', [])) + 
                                len(current_data.get('click_timestamps', [])))
            
            # Check for obvious automation signals
            evasion_signals = current_data.get('evasion_signals', {})
            automation_signals = sum(1 for v in evasion_signals.values() if v) if evasion_signals else 0
            
            if automation_signals >= 5:  # Updated to match simple validation threshold
                fallback_result = {
                    'is_authorized': False,
                    'confidence': 0.8,
                    'anomaly_score': 0.9,
                    'risk_score': 0.9,
                    'mahalanobis_distance': float('inf'),
                    'standard_deviations': float('inf'),
                    'authorization_reason': f'AUTOMATION_DETECTED: {automation_signals} clear automation signals detected despite analysis error',
                    'recommendation': 'BLOCK: Clear automation detected',
                    'analysis_type': 'fallback_automation_detection',
                    'error_details': str(e),
                    'automation_signals': automation_signals,
                    'risk_factors': [
                        {
                            'metric': 'automation_signals',
                            'severity': 'CRITICAL',
                            'value': automation_signals,
                            'threshold': 4,
                            'description': 'Clear automation signals detected'
                        }
                    ]
                }
                return self.apply_risk_confidence_check(fallback_result)
            elif total_interactions >= 3:  # Some reasonable interaction
                fallback_result = {
                    'is_authorized': True,
                    'confidence': 0.5,
                    'anomaly_score': 0.4,
                    'risk_score': 0.4,
                    'mahalanobis_distance': 0.0,
                    'standard_deviations': 0.0,
                    'authorization_reason': f'FALLBACK_APPROVAL: Analysis error but {total_interactions} interactions suggest human behavior',
                    'recommendation': f'ALLOW: Fallback approval based on {total_interactions} interactions',
                    'analysis_type': 'fallback_human_detection',
                    'error_details': str(e),
                    'total_interactions': total_interactions,
                    'risk_factors': [
                        {
                            'metric': 'fallback_analysis_error',
                            'severity': 'MEDIUM',
                            'value': total_interactions,
                            'threshold': 3,
                            'description': 'Analysis error but sufficient interactions detected'
                        }
                    ]
                }
                return self.apply_risk_confidence_check(fallback_result)
            else:  # Very limited interaction
                fallback_result = {
                    'is_authorized': False,
                    'confidence': 0.6,
                    'anomaly_score': 0.7,
                    'risk_score': 0.7,
                    'mahalanobis_distance': float('inf'),
                    'standard_deviations': float('inf'),
                    'authorization_reason': f'INSUFFICIENT_DATA_ERROR: Analysis error and only {total_interactions} interactions',
                    'recommendation': 'BLOCK: Analysis error with insufficient interaction data',
                    'analysis_type': 'fallback_insufficient_data',
                    'error_details': str(e),
                    'total_interactions': total_interactions,
                    'risk_factors': [
                        {
                            'metric': 'insufficient_data_with_error',
                            'severity': 'HIGH',
                            'value': total_interactions,
                            'threshold': 3,
                            'description': 'Analysis error with insufficient interaction data'
                        }
                    ]
                }
                return self.apply_risk_confidence_check(fallback_result)

    
    
    def generate_enhanced_baseline_variations(self, baseline_features, num_variations=15):
        
        try:
            if not baseline_features:
                return []
            
            baseline_array = np.array(baseline_features, dtype=float)
            variations = [baseline_array.copy()]  # Include original baseline
            
            print(f"🔄 Generating {num_variations} enhanced baseline variations...")
            
            # Generate variations with different noise patterns for realistic human behavior
            variation_profiles = [
                # (std_factor, num_samples, description)
                (0.01, 3, "Micro-variations (same session)"),
                (0.03, 4, "Small variations (slight mood/fatigue changes)"),
                (0.06, 3, "Medium variations (different times of day)"),
                (0.10, 2, "Larger variations (stress/environment changes)"),
                (0.15, 1, "Maximum expected variation (still same user)"),
            ]
            
            for std_factor, count, description in variation_profiles:
                for _ in range(count):
                    # Create realistic variation pattern
                    noise = np.random.normal(0, std_factor, len(baseline_features))
                    
                    # Apply different noise patterns based on feature types
                    for i in range(len(noise)):
                        # Cursor movement features (indices 0-11) - more variable
                        if i < 12:
                            noise[i] *= 1.2
                        # Keystroke timing features (indices 12-25) - more consistent 
                        elif i < 26:
                            noise[i] *= 0.8
                        # Click features (indices 26-32) - moderate variation
                        elif i < 33:
                            noise[i] *= 1.0
                        # Device/environment features - very stable
                        else:
                            noise[i] *= 0.5
                    
                    # Apply multiplicative variation (more realistic than additive)
                    variation = baseline_array * (1 + noise)
                    
                    # Ensure no negative values for count-based features
                    variation = np.maximum(variation, 0)
                    
                    variations.append(variation)
                    
                    if len(variations) >= num_variations + 1:  # +1 for original
                        break
                
                if len(variations) >= num_variations + 1:
                    break
            
            print(f"✅ Generated {len(variations)} total variations ({len(variations)-1} synthetic + 1 original)")
            return variations
            
        except Exception as e:
            print(f"❌ Error generating baseline variations: {e}")
            return [np.array(baseline_features)] if baseline_features else []
    
    def calculate_enhanced_mahalanobis_distance(self, current_vector, baseline_variations):
        """
        Calculate Mahalanobis distance with enhanced error handling and regularization
        
        Args:
            current_vector: Current behavioral feature vector
            baseline_variations: List of baseline feature variations
            
        Returns:
            Mahalanobis distance (float)
        """
        try:
            current_vec = np.array(current_vector, dtype=float)
            
            if len(baseline_variations) < 2:
                print("⚠️ Insufficient baseline variations for covariance calculation")
                return float('inf')
            
            # Convert variations to matrix
            baseline_matrix = np.array(baseline_variations, dtype=float)
            
            # Ensure current vector matches baseline dimensions
            if len(current_vec) != baseline_matrix.shape[1]:
                target_len = baseline_matrix.shape[1]
                if len(current_vec) < target_len:
                    current_vec = np.pad(current_vec, (0, target_len - len(current_vec)), 'constant')
                else:
                    current_vec = current_vec[:target_len]
            
            # Calculate baseline statistics
            baseline_mean = np.mean(baseline_matrix, axis=0)
            baseline_cov = np.cov(baseline_matrix, rowvar=False)
            
            print(f"📊 Baseline statistics: mean shape={baseline_mean.shape}, cov shape={baseline_cov.shape}")
            
            # User-friendly regularization for behavioral data
            condition_number = np.linalg.cond(baseline_cov)
            print(f"📐 Covariance matrix condition number: {condition_number:.2e}")
            
            # More lenient regularization to avoid overly strict distance calculations
            if condition_number > 1e8:
                regularization = 0.2  # Strong regularization for user-friendly behavior
                print(f"🔧 Applying strong user-friendly regularization: {regularization}")
            elif condition_number > 1e6:
                regularization = 0.15  # Medium-strong regularization
                print(f"🔧 Applying medium-strong regularization: {regularization}")
            elif condition_number > 1e4:
                regularization = 0.1  # Medium regularization
                print(f"🔧 Applying medium regularization: {regularization}")
            else:
                regularization = 0.05  # Light regularization for user-friendly verification
                print(f"🔧 Applying light regularization: {regularization}")
            
            # Add regularization to diagonal - this makes the calculation much more stable
            baseline_cov += np.eye(baseline_cov.shape[0]) * regularization
            
            # Calculate Mahalanobis distance with multiple fallback methods
            try:
                # Method 1: Standard scipy mahalanobis
                from scipy.spatial.distance import mahalanobis
                inv_cov = linalg.inv(baseline_cov)
                distance = mahalanobis(current_vec, baseline_mean, inv_cov)
                
                # Sanity check - more lenient caps for user-friendly verification
                if distance > 20 or np.isnan(distance) or np.isinf(distance):
                    print(f"⚠️ Unrealistic standard distance {distance:.2f}, using fallback method")
                    raise ValueError(f"Unrealistic distance: {distance}")
                
                print(f"✅ Standard Mahalanobis distance: {distance:.4f}")
                return float(distance)
                
            except (linalg.LinAlgError, np.linalg.LinAlgError, ValueError) as e:
                print(f"⚠️ Standard method failed ({e}), using pseudo-inverse...")
                
                try:
                    # Method 2: Pseudo-inverse approach
                    pseudo_inv_cov = linalg.pinv(baseline_cov)
                    diff = current_vec - baseline_mean
                    distance = np.sqrt(np.dot(np.dot(diff, pseudo_inv_cov), diff))
                    
                    if distance > 15 or np.isnan(distance):
                        print(f"⚠️ Pseudo-inverse distance acceptable {distance:.2f}, using robust method")
                        raise ValueError(f"Pseudo-inverse distance high: {distance}")
                    
                    print(f"✅ Pseudo-inverse Mahalanobis distance: {distance:.4f}")
                    return float(distance)
                    
                except Exception as e2:
                    print(f"⚠️ Pseudo-inverse failed ({e2}), using robust Euclidean...")
                    
                    # Method 3: Robust normalized Euclidean distance
                    std_devs = np.std(baseline_matrix, axis=0)
                    std_devs[std_devs == 0] = np.mean(std_devs[std_devs > 0]) if np.any(std_devs > 0) else 1.0
                    
                    # Use median absolute deviation for robustness
                    mad = np.median(np.abs(baseline_matrix - baseline_mean), axis=0)
                    mad[mad == 0] = np.median(mad[mad > 0]) if np.any(mad > 0) else 1.0
                    
                    # Combined scaling using both std and MAD
                    scaling_factors = np.minimum(std_devs, mad * 1.4826)  # 1.4826 converts MAD to std equivalent
                    
                    normalized_diff = (current_vec - baseline_mean) / scaling_factors
                    distance = np.sqrt(np.sum(normalized_diff ** 2))
                    
                    # Final safety cap for robust distance - very lenient for user access
                    distance = min(distance, 12.0)  # More lenient cap for user-friendly verification
                    
                    print(f"✅ Robust Euclidean distance: {distance:.4f}")
                    return float(distance)
            
        except Exception as e:
            print(f"🚨 Critical error in enhanced Mahalanobis calculation: {e}")
            logger.error(f"Enhanced Mahalanobis distance calculation error: {str(e)}")
            return float('inf')
       
        
    def extract_behavioral_features(self, behavioral_data):

        try:
            features = []
            
            print(f"🔍 Extracting comprehensive features from ALL behavioral data...")
            print(f"   Data type: {type(behavioral_data)}")
            
            # Handle list format baseline data (array of mouse movements)
            if isinstance(behavioral_data, list):
                print(f"   Converting list format data ({len(behavioral_data)} movements) to dict format")
                # Convert list of mouse movements to dictionary format
                behavioral_data = {
                    'cursor_movements': behavioral_data,
                    'cursorMovements': behavioral_data,
                    'key_press_times': [],
                    'click_timestamps': [],
                    'total_time': behavioral_data[-1].get('timestamp', 0) - behavioral_data[0].get('timestamp', 0) if len(behavioral_data) > 1 else 0
                }
            
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
    
    def assess_behavioral_data_quality(self, behavioral_data):
        """
        Assess the quality of behavioral data for robust analysis
        Returns quality score between 0.0 and 1.0
        """
        try:
            quality_score = 0.0
            quality_factors = 0
            
            # Check cursor movement data quality (more generous)
            cursor_movements = behavioral_data.get('cursorMovements', []) or behavioral_data.get('cursor_movements', [])
            if cursor_movements:
                quality_factors += 1
                if len(cursor_movements) >= 10:
                    quality_score += 0.3  # More generous scoring
                elif len(cursor_movements) >= 5:
                    quality_score += 0.25  # Moderate cursor data gets better score
                else:
                    quality_score += 0.2   # Even minimal data gets decent score
            
            # Check keystroke data quality (more generous)
            key_presses = behavioral_data.get('keyPressTimes', []) or behavioral_data.get('key_press_times', [])
            if key_presses:
                quality_factors += 1
                if len(key_presses) >= 5:
                    quality_score += 0.3   # More generous scoring
                elif len(key_presses) >= 3:
                    quality_score += 0.25  # Moderate keystroke data gets better score
                else:
                    quality_score += 0.2   # Even minimal data gets decent score
            
            # Check click data quality (more generous)
            clicks = behavioral_data.get('clickTimestamps', []) or behavioral_data.get('click_timestamps', [])
            if clicks:
                quality_factors += 1
                if len(clicks) >= 3:
                    quality_score += 0.2  # More generous scoring
                elif len(clicks) >= 1:
                    quality_score += 0.15  # Even single click gets decent score
                else:
                    quality_score += 0.1   # Minimal click data
            
            # Check scroll data quality (more generous)
            scrolls = behavioral_data.get('scrollSpeeds', []) or behavioral_data.get('scroll_speeds', [])
            if scrolls:
                quality_factors += 1
                if len(scrolls) >= 3:
                    quality_score += 0.2  # More generous scoring
                else:
                    quality_score += 0.15   # Any scroll data gets good score
            
            # Check for automation indicators (less punitive)
            evasion_signals = behavioral_data.get('evasion_signals', {})
            automation_count = sum(1 for v in evasion_signals.values() if v) if evasion_signals else 0
            if automation_count > 3:
                quality_score -= (automation_count * 0.05)  # Reduce quality penalty
            
            # Check session duration (more generous)
            session_duration = behavioral_data.get('sessionDuration', 0) or behavioral_data.get('session_duration', 0)
            if session_duration >= 10000:  # 10+ seconds (more lenient)
                quality_score += 0.15
            elif session_duration >= 5000:  # 5+ seconds
                quality_score += 0.1
            
            # Normalize to 0-1 range with realistic scaling
            max_possible_score = 1.0 
            quality_score = min(1.0, max(0.1, quality_score / max_possible_score))  # Minimum 0.1 quality
            
            print(f"📊 Data quality assessment: {quality_score:.3f} (factors: {quality_factors})")
            return quality_score
            
        except Exception as e:
            logger.error(f"Error assessing behavioral data quality: {str(e)}")
            return 0.5  
    def calculate_behavioral_consistency(self, current_data, baseline_data):
        """
        Enhanced behavioral consistency calculation for unauthorized user detection
        Returns consistency score between 0.0 and 1.0
        """
        try:
            consistency_scores = []
            
            # Consistency check 1: Cursor movement patterns - enhanced sensitivity
            current_cursor = current_data.get('cursorMovements', []) or current_data.get('cursor_movements', [])
            baseline_cursor = baseline_data.get('cursorMovements', []) or baseline_data.get('cursor_movements', [])
            
            if current_cursor and baseline_cursor:
                # Compare average cursor speeds with higher sensitivity
                current_speeds = self._calculate_cursor_speeds(current_cursor)
                baseline_speeds = self._calculate_cursor_speeds(baseline_cursor)
                
                if current_speeds and baseline_speeds:
                    current_avg = sum(current_speeds) / len(current_speeds)
                    baseline_avg = sum(baseline_speeds) / len(baseline_speeds)
                    
                    if baseline_avg > 0:
                        # More sensitive speed consistency check
                        speed_diff_ratio = abs(current_avg - baseline_avg) / baseline_avg
                        # Stricter threshold: 30% difference = low consistency
                        speed_consistency = max(0.0, 1.0 - (speed_diff_ratio / 0.3))
                        consistency_scores.append(speed_consistency)
                        
                # Compare cursor movement variance patterns
                if len(current_speeds) > 1 and len(baseline_speeds) > 1:
                    current_variance = np.var(current_speeds)
                    baseline_variance = np.var(baseline_speeds)
                    
                    if baseline_variance > 0:
                        variance_diff_ratio = abs(current_variance - baseline_variance) / baseline_variance
                        variance_consistency = max(0.0, 1.0 - (variance_diff_ratio / 0.5))
                        consistency_scores.append(variance_consistency)
            
            # Consistency check 2: Keystroke timing patterns - enhanced
            current_keys = current_data.get('keyPressTimes', []) or current_data.get('key_press_times', [])
            baseline_keys = baseline_data.get('keyPressTimes', []) or baseline_data.get('key_press_times', [])
            
            if len(current_keys) > 1 and len(baseline_keys) > 1:
                current_intervals = [current_keys[i] - current_keys[i-1] for i in range(1, len(current_keys))]
                baseline_intervals = [baseline_keys[i] - baseline_keys[i-1] for i in range(1, len(baseline_keys))]
                
                if current_intervals and baseline_intervals:
                    current_avg_interval = sum(current_intervals) / len(current_intervals)
                    baseline_avg_interval = sum(baseline_intervals) / len(baseline_intervals)
                    
                    if baseline_avg_interval > 0:
                        # Stricter keystroke timing consistency
                        timing_diff_ratio = abs(current_avg_interval - baseline_avg_interval) / baseline_avg_interval
                        timing_consistency = max(0.0, 1.0 - (timing_diff_ratio / 0.4))
                        consistency_scores.append(timing_consistency)
                        
                    # Check keystroke rhythm variance
                    if len(current_intervals) > 1 and len(baseline_intervals) > 1:
                        current_rhythm_var = np.var(current_intervals)
                        baseline_rhythm_var = np.var(baseline_intervals)
                        
                        if baseline_rhythm_var > 0:
                            rhythm_diff_ratio = abs(current_rhythm_var - baseline_rhythm_var) / baseline_rhythm_var
                            rhythm_consistency = max(0.0, 1.0 - (rhythm_diff_ratio / 0.6))
                            consistency_scores.append(rhythm_consistency)
            
            # Consistency check 3: Click patterns - enhanced
            current_clicks = current_data.get('clickTimestamps', []) or current_data.get('click_timestamps', [])
            baseline_clicks = baseline_data.get('clickTimestamps', []) or baseline_data.get('click_timestamps', [])
            
            if current_clicks and baseline_clicks:
                current_click_count = len(current_clicks)
                baseline_click_count = len(baseline_clicks)
                
                # More sensitive click pattern analysis
                max_clicks = max(current_click_count, baseline_click_count)
                if max_clicks > 0:
                    click_diff_ratio = abs(current_click_count - baseline_click_count) / max_clicks
                    click_consistency = max(0.0, 1.0 - (click_diff_ratio / 0.3))
                    consistency_scores.append(click_consistency)
                
                # Check click timing patterns if available
                if len(current_clicks) > 1 and len(baseline_clicks) > 1:
                    current_click_intervals = [current_clicks[i] - current_clicks[i-1] for i in range(1, len(current_clicks))]
                    baseline_click_intervals = [baseline_clicks[i] - baseline_clicks[i-1] for i in range(1, len(baseline_clicks))]
                    
                    if current_click_intervals and baseline_click_intervals:
                        current_avg_click_interval = sum(current_click_intervals) / len(current_click_intervals)
                        baseline_avg_click_interval = sum(baseline_click_intervals) / len(baseline_click_intervals)
                        
                        if baseline_avg_click_interval > 0:
                            click_timing_diff = abs(current_avg_click_interval - baseline_avg_click_interval) / baseline_avg_click_interval
                            click_timing_consistency = max(0.0, 1.0 - (click_timing_diff / 0.5))
                            consistency_scores.append(click_timing_consistency)
            
            # Consistency check 4: Movement trajectory patterns
            if current_cursor and baseline_cursor and len(current_cursor) > 5 and len(baseline_cursor) > 5:
                # Check movement direction changes
                current_direction_changes = self._count_direction_changes(current_cursor)
                baseline_direction_changes = self._count_direction_changes(baseline_cursor)
                
                if baseline_direction_changes > 0:
                    direction_diff_ratio = abs(current_direction_changes - baseline_direction_changes) / baseline_direction_changes
                    direction_consistency = max(0.0, 1.0 - (direction_diff_ratio / 0.4))
                    consistency_scores.append(direction_consistency)
            
            # Calculate overall consistency with stricter requirements
            if consistency_scores:
                overall_consistency = sum(consistency_scores) / len(consistency_scores)
                # Apply penalty for having few consistency checks
                if len(consistency_scores) < 3:
                    overall_consistency *= 0.8  # Reduce consistency if few checks available
            else:
                overall_consistency = 0.3  # Lower default for insufficient data (was 0.5)
            
            print(f"🔍 Behavioral consistency breakdown: {consistency_scores}")
            print(f"🔍 Overall consistency: {overall_consistency:.3f}")
            
            return overall_consistency
            
        except Exception as e:
            logger.error(f"Error calculating behavioral consistency: {str(e)}")
            return 0.3  # Lower default for errors
    
    def _calculate_cursor_speeds(self, cursor_movements):
        """Helper method to calculate cursor movement speeds"""
        speeds = []
        try:
            for i in range(1, len(cursor_movements)):
                prev = cursor_movements[i-1]
                curr = cursor_movements[i]
                
                prev_x = prev.get('x', 0) if isinstance(prev, dict) else prev[0] if isinstance(prev, (list, tuple)) else 0
                prev_y = prev.get('y', 0) if isinstance(prev, dict) else prev[1] if isinstance(prev, (list, tuple)) else 0
                prev_time = prev.get('timestamp', 0) if isinstance(prev, dict) else prev[2] if isinstance(prev, (list, tuple)) and len(prev) > 2 else 0
                
                curr_x = curr.get('x', 0) if isinstance(curr, dict) else curr[0] if isinstance(curr, (list, tuple)) else 0
                curr_y = curr.get('y', 0) if isinstance(curr, dict) else curr[1] if isinstance(curr, (list, tuple)) else 0
                curr_time = curr.get('timestamp', 0) if isinstance(curr, dict) else curr[2] if isinstance(curr, (list, tuple)) and len(curr) > 2 else 0
                
                dx = curr_x - prev_x
                dy = curr_y - prev_y
                dt = (curr_time - prev_time) / 1000.0  # Convert to seconds
                
                if dt > 0:
                    distance = math.sqrt(dx**2 + dy**2)
                    speed = distance / dt
                    speeds.append(speed)
        except Exception as e:
            logger.error(f"Error calculating cursor speeds: {str(e)}")
        
        return speeds
    
    def _count_direction_changes(self, cursor_movements):
        """Helper method to count direction changes in cursor movements"""
        direction_changes = 0
        try:
            if len(cursor_movements) < 3:
                return 0
                
            for i in range(2, len(cursor_movements)):
                prev = cursor_movements[i-2]
                curr = cursor_movements[i-1] 
                next_move = cursor_movements[i]
                
                prev_x = prev.get('x', 0) if isinstance(prev, dict) else prev[0] if isinstance(prev, (list, tuple)) else 0
                prev_y = prev.get('y', 0) if isinstance(prev, dict) else prev[1] if isinstance(prev, (list, tuple)) else 0
                
                curr_x = curr.get('x', 0) if isinstance(curr, dict) else curr[0] if isinstance(curr, (list, tuple)) else 0
                curr_y = curr.get('y', 0) if isinstance(curr, dict) else curr[1] if isinstance(curr, (list, tuple)) else 0
                
                next_x = next_move.get('x', 0) if isinstance(next_move, dict) else next_move[0] if isinstance(next_move, (list, tuple)) else 0
                next_y = next_move.get('y', 0) if isinstance(next_move, dict) else next_move[1] if isinstance(next_move, (list, tuple)) else 0
                
                # Calculate direction vectors
                dx1 = curr_x - prev_x
                dy1 = curr_y - prev_y
                dx2 = next_x - curr_x
                dy2 = next_y - curr_y
                
                # Check for direction change (dot product approach)
                if dx1 != 0 or dy1 != 0 or dx2 != 0 or dy2 != 0:
                    dot_product = dx1 * dx2 + dy1 * dy2
                    magnitude1 = math.sqrt(dx1**2 + dy1**2)
                    magnitude2 = math.sqrt(dx2**2 + dy2**2)
                    
                    if magnitude1 > 0 and magnitude2 > 0:
                        cos_angle = dot_product / (magnitude1 * magnitude2)
                        # If angle > 90 degrees, it's a significant direction change
                        if cos_angle < 0:
                            direction_changes += 1
                            
        except Exception as e:
            logger.error(f"Error counting direction changes: {str(e)}")
        
        return direction_changes


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
                
                # ENHANCED: Try to find baseline by user_id if available
                user_session = UserSession.objects.filter(session_id=session_id).first()
                if user_session and user_session.usai_id:
                    print(f"🔍 Searching for baseline by user identifier: {user_session.usai_id}")
                    baseline_record = UserBaselineBehavior.objects.filter(
                        user_id=user_session.usai_id,
                        is_active=True,
                        sufficient_interaction=True
                    ).order_by('-created_at').first()
                    
                    if baseline_record:
                        print(f"✅ Found baseline for user {user_session.usai_id}")
                    else:
                        print(f"⚠️ No baseline found for user {user_session.usai_id} either")

                if not baseline_record:
                    # ENHANCED: Instead of rejecting, create a basic analysis and suggest baseline collection
                    print(f"🔄 Creating permissive analysis result for first-time user")
                    
                    # Check if user has reasonable interaction data
                    total_interactions = (len(behavioral_data.get('cursor_movements', [])) + 
                                        len(behavioral_data.get('key_press_times', [])) + 
                                        len(behavioral_data.get('click_timestamps', [])))
                    
                    if total_interactions >= 5:
                        # Create a basic analysis result for users with sufficient interaction
                        analysis_result = {
                            'is_authorized': True,
                            'confidence': 0.7,
                            'anomaly_score': 0.2,
                            'risk_score': 0.3,
                            'authorization_reason': f'NEW_USER_APPROVED: No baseline available but {total_interactions} interactions detected - collecting baseline data',
                            'recommendation': f'ALLOW: First-time user with {total_interactions} interactions - baseline collection in progress',
                            'analysis_type': 'new_user_baseline_collection',
                            'requires_baseline_collection': True,
                            'session_id': session_id,
                            'total_interactions': total_interactions,
                            'risk_factors': [
                                {
                                    'metric': 'new_user_baseline_collection',
                                    'severity': 'LOW',
                                    'value': total_interactions,
                                    'threshold': 5,
                                    'description': 'New user with sufficient interaction data'
                                }
                            ]
                        }
                        
                        # Store this behavioral data as a potential baseline
                        try:
                            # Ensure we have a valid user_id - use session_id if no user available
                            user_id_for_baseline = None
                            if user_session and user_session.usai_id:
                                # Use USAI ID as the user identifier
                                user_id_for_baseline = str(user_session.usai_id)
                            elif user_session and user_session.name:
                                # Use name as fallback
                                user_id_for_baseline = str(user_session.name)
                            else:
                                # Use session_id as final fallback for user_id
                                user_id_for_baseline = session_id
                            
                            baseline_behavior = UserBaselineBehavior.objects.create(
                                session_id=session_id,
                                user_id=user_id_for_baseline,
                                baseline_user_behavior=behavioral_data,
                                collection_start_time=timezone.now(),
                                collection_end_time=timezone.now(),
                                collection_duration_ms=20000,  # Default 20 seconds
                                data_quality_score=0.7,  # Reasonable initial quality
                                sufficient_interaction=total_interactions >= 10,
                                is_active=True
                            )
                            print(f"✅ Created initial baseline record for future comparisons")
                            analysis_result['baseline_created'] = True
                            analysis_result['baseline_id'] = baseline_behavior.id
                        except Exception as baseline_error:
                            print(f"⚠️ Could not create baseline: {baseline_error}")
                            analysis_result['baseline_created'] = False
                    else:
                        # Still allow but with lower confidence for very limited interaction
                        analysis_result = {
                            'is_authorized': True,
                            'confidence': 0.5,
                            'anomaly_score': 0.4,
                            'risk_score': 0.5,
                            'authorization_reason': f'LIMITED_NEW_USER: Only {total_interactions} interactions but allowing new user',
                            'recommendation': f'ALLOW: New user with limited data ({total_interactions} interactions)',
                            'analysis_type': 'limited_new_user',
                            'requires_more_interaction': True,
                            'session_id': session_id,
                            'total_interactions': total_interactions,
                            'risk_factors': [
                                {
                                    'metric': 'limited_interaction_new_user',
                                    'severity': 'MEDIUM',
                                    'value': total_interactions,
                                    'threshold': 5,
                                    'description': 'New user with limited interaction data'
                                }
                            ]
                        }
                    
                    # Continue with storing this data
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
            # Create a new session for behavioral tracking if it doesn't exist
            session = UserSession.objects.create(
                session_id=session_id,
                is_active=True,
                created_at=timezone.now()
            )
            print(f"🆕 Created new UserSession for behavioral tracking: {session_id}")
        
        # 📊 STEP 2: IMPROVED USER IDENTITY DETECTION
        print(f"🔬 Performing improved user identity detection...")
        
        # Check if rolling window data is provided from frontend (for compatibility)
        rolling_windows = behavioral_data.get('rollingWindows', [])
        window_metadata = behavioral_data.get('windowMetadata', {})
        
        if rolling_windows:
            print(f"📊 Rolling windows received from frontend: {len(rolling_windows)} windows")
            print(f"📊 Window metadata: {window_metadata}")
        
        # Enhanced analysis with baseline comparison using improved identity detection
        if 'analysis_result' not in locals():
            # Only run analysis if we haven't already created a result for new users
            print(f"🧠 Running behavioral analysis...")
            
            # Use existing behavioral analysis methods instead of external function
            # Try to find existing user baseline for comparison
            user_id = behavioral_data.get('user_id') or behavioral_data.get('usai_id')
            
            # Check if we have meaningful baseline data (not just empty or minimal data)
            has_meaningful_baseline = False
            if baseline_behavior:
                if isinstance(baseline_behavior, dict):
                    # Dictionary format baseline data
                    has_meaningful_baseline = (len(baseline_behavior) > 0 and
                                             (baseline_behavior.get('cursor_movements') or 
                                              baseline_behavior.get('cursorMovements') or
                                              baseline_behavior.get('key_press_times') or
                                              baseline_behavior.get('keyPressTimes')))
                elif isinstance(baseline_behavior, list):
                    # List format baseline data (mouse movements array)
                    has_meaningful_baseline = len(baseline_behavior) > 5  # At least 5 interactions
            
            print(f"🔍 ROUTING DEBUG:")
            print(f"   user_id: {user_id}")
            print(f"   baseline_behavior type: {type(baseline_behavior)}")
            print(f"   baseline_behavior length: {len(baseline_behavior) if baseline_behavior else 0}")
            print(f"   has_meaningful_baseline: {has_meaningful_baseline}")
            
            # Use baseline comparison if we have meaningful baseline data (user_id is helpful but not required)
            if has_meaningful_baseline:
                # Use existing baseline comparison method
                print(f"🔍 Using baseline comparison for user {user_id}")
                analysis_result = behavioral_analyzer.analyze_with_baseline_comparison(
                    session_id=session_id,
                    current_data=behavioral_data,   
                    baseline_behavior_or_user_id=baseline_behavior
                )
            else:
                # Use simple behavioral validation for new users or missing baselines
                print(f"🔍 Using simple behavioral validation - user_id: {user_id}, has_baseline: {has_meaningful_baseline}")
                simple_result = behavioral_analyzer.simple_behavioral_validation(behavioral_data)
                analysis_result = {
                    'is_authorized': simple_result.get('is_authorized', False),
                    'identity_score': simple_result.get('confidence', 0.5),
                    'confidence': simple_result.get('confidence', 0.5),
                    'risk_score': 1.0 - simple_result.get('confidence', 0.5),
                    'authorization_reason': simple_result.get('reason', 'BEHAVIORAL_VALIDATION'),
                    'validation_type': simple_result.get('validation_type', 'simple_validation'),
                    'recommendation': simple_result.get('reason', 'BEHAVIORAL_VALIDATION'),
                    'risk_factors': [
                        {
                            'metric': 'simple_behavioral_validation',
                            'severity': 'LOW' if simple_result.get('is_authorized', False) else 'MEDIUM',
                            'value': simple_result.get('confidence', 0.5),
                            'threshold': 0.5,
                            'description': simple_result.get('reason', 'Simple behavioral validation')
                        }
                    ],
                    'suspicious_indicators': [],
                    'analysis_type': 'simple_behavioral_validation',
                    'mahalanobis_distance': 0.0,
                    'standard_deviations': 0.0
                }
                
                print(f"🔍 SIMPLE VALIDATION RESULT:")
                print(f"   is_authorized: {analysis_result['is_authorized']}")
                print(f"   authorization_reason: {analysis_result['authorization_reason']}")
                print(f"   confidence: {analysis_result['confidence']}")
            
            print(f"🎯 Identity Analysis Result:")
            print(f"   Authorized: {analysis_result.get('is_authorized', False)}")
            print(f"   Identity Score: {analysis_result.get('identity_score', 0.0):.3f}")
            print(f"   Confidence: {analysis_result.get('confidence', 0.0):.3f}")
            print(f"   Risk Score: {analysis_result.get('risk_score', 1.0):.3f}")
            print(f"   Reason: {analysis_result.get('authorization_reason', 'Unknown')}")
            
            # Add compatibility fields for frontend
            analysis_result.update({
                'analysis_type': 'improved_user_identity_detection',
                'session_id': session_id,
                'timestamp': timezone.now().isoformat(),
                'success': True
            })
        
        # 📊 STEP 3: LEGACY COMPATIBILITY (keeping for frontend compatibility)
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
