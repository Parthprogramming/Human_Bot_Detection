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
    
    def apply_risk_confidence_check(self, analysis_result):
        """
        ROBUST USER IDENTITY VERIFICATION SYSTEM
        Compares current behavior with baseline to verify if it's the same person
        """
        try:
            print(f"🔐 STARTING IDENTITY VERIFICATION...")
            
            # Get baseline data for comparison
            baseline_data = analysis_result.get('baseline_data', {})
            current_behavior = analysis_result.get('current_behavior', {})
            recommendation = analysis_result['recommendation']

            if not baseline_data:
                print(f"⚠️ No baseline available - applying strict new user validation")
                return self._validate_new_user(analysis_result)
            
            # PERFORM BASELINE COMPARISON FOR RETURNING USERS
            print(f"🔬 Performing baseline comparison for returning user...")
            identity_verification = self._verify_user_identity(baseline_data, current_behavior)
            
            if identity_verification['is_same_person']:
                # Same person detected - authorize with confidence
                analysis_result['is_authorized'] = True
                analysis_result['confidence'] = identity_verification['confidence']
                analysis_result['authorization_reason'] = f'IDENTITY_VERIFIED: Same person detected (confidence: {identity_verification["confidence"]:.3f})'
                analysis_result['recommendation'] = 'ALLOW: Verified returning user'
                analysis_result['identity_verification'] = identity_verification
                print(f"✅ IDENTITY VERIFIED: Same person detected - AUTHORIZING")
            else:
                # Different person detected - block access
                analysis_result['is_authorized'] = False
                analysis_result['confidence'] = identity_verification['confidence']
                analysis_result['authorization_reason'] = f'IDENTITY_MISMATCH: Different person detected (confidence: {identity_verification["confidence"]:.3f})'
                analysis_result['recommendation'] = 'BLOCK: Unauthorized user - identity mismatch'
                analysis_result['identity_verification'] = identity_verification
                analysis_result['risk_score'] = 10.0  # High risk for identity theft
                print(f"🚨 IDENTITY MISMATCH: Different person detected - BLOCKING")
            
            return analysis_result

        except Exception as e:
            print(f"❌ Error in identity verification: {str(e)}")
            print(f"🔍 Falling back to strict validation for safety")
            # Fallback to strict validation
            return self._validate_new_user(analysis_result)
    
    def _validate_new_user(self, analysis_result):
        try:
            current_behavior = analysis_result.get('current_behavior', {})
            
            # Count interactions
            cursor_movements = len(current_behavior.get('cursor_movements', []) or current_behavior.get('cursorMovements', []))
            key_presses = len(current_behavior.get('key_press_times', []) or current_behavior.get('keyPressTimes', []))
            clicks = len(current_behavior.get('click_timestamps', []) or current_behavior.get('clickTimestamps', []))
            total_interactions = cursor_movements + key_presses + clicks
            
            # Check for automation signals
            evasion_signals = current_behavior.get('evasion_signals', {})
            automation_count = sum(1 for v in evasion_signals.values() if v) if evasion_signals else 0
            
            # Check for paste behavior
            paste_detected = current_behavior.get('paste_detected', False)
            
            # Calculate interaction rate
            total_time = current_behavior.get('total_time', 0)
            interaction_rate = total_interactions / max(total_time / 1000, 1) if total_time > 0 else 0
            
            # STRICT VALIDATION FOR NEW USERS
            if automation_count >= 3:  # Lowered threshold
                analysis_result['is_authorized'] = False
                analysis_result['confidence'] = 0.9
                analysis_result['authorization_reason'] = f'AUTOMATION_DETECTED: {automation_count} automation signals'
                analysis_result['recommendation'] = 'BLOCK: Automation detected'
                analysis_result['risk_score'] = 8.0
            elif total_interactions < 10:  # Increased minimum
                analysis_result['is_authorized'] = False
                analysis_result['confidence'] = 0.8
                analysis_result['authorization_reason'] = f'INSUFFICIENT_INTERACTION: Only {total_interactions} interactions (minimum: 10)'
                analysis_result['recommendation'] = 'BLOCK: Insufficient interaction data'
                analysis_result['risk_score'] = 6.0
            elif interaction_rate > 25:  # Lowered threshold
                analysis_result['is_authorized'] = False
                analysis_result['confidence'] = 0.8
                analysis_result['authorization_reason'] = f'SUSPICIOUS_SPEED: {interaction_rate:.1f} interactions/sec too fast'
                analysis_result['recommendation'] = 'BLOCK: Suspicious interaction speed'
                analysis_result['risk_score'] = 7.0
            elif paste_detected and total_interactions < 8:
                analysis_result['is_authorized'] = False
                analysis_result['confidence'] = 0.7
                analysis_result['authorization_reason'] = 'PASTE_WITH_LIMITED_INTERACTION: Paste detected with minimal interaction'
                analysis_result['recommendation'] = 'BLOCK: Suspicious paste behavior'
                analysis_result['risk_score'] = 6.5
            else:
                # Approve with moderate confidence for new users
                confidence = min(0.6 + (total_interactions - 10) * 0.02, 0.8)
                analysis_result['is_authorized'] = True
                analysis_result['confidence'] = confidence
                analysis_result['authorization_reason'] = f'NEW_USER_APPROVED: {total_interactions} interactions, no automation signals'
                analysis_result['recommendation'] = 'ALLOW: New user with sufficient interaction data'
                analysis_result['risk_score'] = 2.0
            
            return analysis_result
                
        except Exception as e:
            print(f"❌ Error in new user validation: {str(e)}")
            # Default to blocking for safety
            analysis_result['is_authorized'] = False
            analysis_result['confidence'] = 0.5
            analysis_result['authorization_reason'] = 'VALIDATION_ERROR: Defaulting to block for safety'
            analysis_result['recommendation'] = 'BLOCK: Validation error'
            analysis_result['risk_score'] = 5.0
            return analysis_result
        
    def calculate_behavioral_metrics(self, behavioral_data):
        metrics = {}
        try:
            cursor_movements = behavioral_data.get('cursor_movements', [])
            cursor_speeds = behavioral_data.get('cursor_speeds', [])
            cursor_acceleration = behavioral_data.get('cursor_acceleration', [])
            cursor_curvature = behavioral_data.get('cursor_curvature', [])
            
            if cursor_movements:
                speeds = cursor_speeds if cursor_speeds else []
                accelerations = cursor_acceleration if cursor_acceleration else []
                curvatures = cursor_curvature if cursor_curvature else []
                
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
            micropauses = behavioral_data.get('microPauses', [])
            
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
            
            device_fingerprint = behavioral_data.get('devicefingerprint', '0')
            canvas_metrics = behavioral_data.get('canvas_metrics', {})
            gpu_info = behavioral_data.get('gpu_info', {})
            unusual_screen = behavioral_data.get('unsualscreenresolution', {})
            evasion_signals = behavioral_data.get('evasion_signals', {})
            
            metrics['device_fingerprint_entropy'] = len(str(device_fingerprint))
            metrics['missing_canvas_fingerprint'] = behavioral_data.get('missing_canvas_fingerprint', False)
            
            if canvas_metrics:
                metrics['canvas_geometry_complexity'] = canvas_metrics.get('geometryLength', 0)
                metrics['canvas_text_complexity'] = canvas_metrics.get('textLength', 0)
                metrics['canvas_winding_support'] = 1 if canvas_metrics.get('winding') == 'supported' else 0
            
            if unusual_screen:
                metrics['screen_resolution_suspicious'] = 1 if unusual_screen.get('is_unusual', False) else 0
                metrics['screen_spoofing_detected'] = 1 if unusual_screen.get('spoofedMismatch', False) else 0
                metrics['device_pixel_ratio'] = unusual_screen.get('device_pixel_ratio', 1)
            
            if evasion_signals:
                evasion_count = sum(1 for key, value in evasion_signals.items() if value)
                metrics['evasion_signals_count'] = evasion_count
                metrics['automation_risk_score'] = evasion_count / max(len(evasion_signals), 1)
                
                metrics['webdriver_detected'] = 1 if evasion_signals.get('webdriver', False) else 0
                metrics['automation_detected'] = 1 if evasion_signals.get('automation', False) else 0
                metrics['headless_browser_detected'] = 1 if evasion_signals.get('headless_chrome', False) else 0
                
                print(f"✅ Evasion analysis: {evasion_count} signals detected")
            
            timing_metrics = behavioral_data.get('timing_metrics', {})
            if timing_metrics:
                metrics['mouse_movement_frequency'] = timing_metrics.get('mouseMovementFrequency', 0)
                metrics['key_press_frequency'] = timing_metrics.get('keyPressFrequency', 0)
                metrics['click_frequency'] = timing_metrics.get('clickFrequency', 0)
                metrics['total_idle_time'] = timing_metrics.get('totalIdleTime', 0)
                metrics['page_load_performance'] = timing_metrics.get('pageLoadComplete', 0) - timing_metrics.get('navigationStart', 0)
            
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
            
            keyboard_patterns = behavioral_data.get('keyboard_patterns', [])
            suspicious_patterns = behavioral_data.get('suspicious_patterns', [])
            
            metrics['keyboard_patterns_count'] = len(keyboard_patterns)
            metrics['suspicious_patterns_count'] = len(suspicious_patterns)
            
            if keyboard_patterns:
                pattern_confidences = [p.get('confidence', 0) for p in keyboard_patterns if isinstance(p, dict)]
                metrics['avg_pattern_confidence'] = statistics.mean(pattern_confidences) if pattern_confidences else 0
            
            total_actions = (metrics.get('cursor_movement_count', 0) + 
                           metrics.get('keystroke_count', 0) + 
                           metrics.get('click_count', 0) + 
                           metrics.get('scroll_changes_count', 0))
            
            metrics['total_behavioral_actions'] = total_actions
            metrics['actions_per_second'] = total_actions / max(metrics.get('total_time', 1), 1) * 1000
            
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
                
                # 🖱️ COMPREHENSIVE CLICK FEATURES
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
                
                # 📜 SCROLL BEHAVIOR FEATURES
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
                micropauses = behavioral_data.get('microPauses', [])
                
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
                
                # 🖥️ DEVICE AND FINGERPRINTING FEATURES
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
<<<<<<< HEAD
            

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


    
    def analyze_with_baseline_comparison(self, session_id, current_data, baseline_behavior_or_user_id, baseline_metrics=None):

        try:
            print(f"🔬 COMPREHENSIVE BEHAVIORAL ANALYSIS: Starting multi-domain analysis...")
            print(f"🔍 Session: {session_id}")

=======

    
    def analyze_with_baseline_comparison(self, session_id, current_data, baseline_behavior_or_user_id, baseline_metrics=None):
        try:
            print(f"🔬 ENHANCED BASELINE ANALYSIS: Starting 3-sigma Mahalanobis analysis...")
            print(f"🔍 Session: {session_id}")

            # 📊 STEP 1: RETRIEVE BASELINE FROM DATABASE
>>>>>>> 94e632f46c91c13fdea348e461634f568aeb697c
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
                    return {
                        'is_authorized': True,
                        'confidence': 0.6,
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
                return {
                    'is_authorized': True,
                    'confidence': 0.6,
                    'mahalanobis_distance': 0.0,
                    'standard_deviations': 0.0,
                    'authorization_reason': 'MISSING_BASELINE: No baseline data available - using permissive authorization',
                    'analysis_type': 'missing_baseline_fallback',
                    'recommendation': 'ALLOW: Missing baseline - collecting data for future analysis'
                }

<<<<<<< HEAD
            # 🚨 CRITICAL: Check for immediate red flags (honeypot, evasion)
            immediate_red_flags = self._check_immediate_red_flags(current_data)
            if immediate_red_flags['blocked']:
                return {
                    'is_authorized': False,
                    'confidence': 0.95,
                    'authorization_reason': f'IMMEDIATE_BLOCK: {immediate_red_flags["reason"]}',
                    'analysis_type': 'immediate_red_flag',
                    'recommendation': 'BLOCK: Critical security violation detected'
                }

            # 🔬 STEP 1: TIME-SERIES METRICS ANALYSIS (Dynamic behaviors)
            print(f"📊 STEP 1: Analyzing time-series metrics...")
            time_series_score = self._analyze_time_series_metrics(current_data, baseline_data)
            print(f"   ✅ Time-series similarity score: {time_series_score:.3f}")

            # 📈 STEP 2: STATISTICAL/CONTINUOUS METRICS ANALYSIS
            print(f"📈 STEP 2: Analyzing statistical/continuous metrics...")
            statistical_score = self._analyze_statistical_metrics(current_data, baseline_data)
            print(f"   ✅ Statistical similarity score: {statistical_score:.3f}")

            # 🚦 STEP 3: BOOLEAN/CATEGORICAL SIGNALS ANALYSIS
            print(f"🚦 STEP 3: Analyzing boolean/categorical signals...")
            boolean_score = self._analyze_boolean_signals(current_data, baseline_data)
            print(f"   ✅ Boolean risk score: {boolean_score:.3f}")

            # 🖥️ STEP 4: DEVICE/ENVIRONMENT FINGERPRINT ANALYSIS
            print(f"🖥️ STEP 4: Analyzing device/environment fingerprints...")
            device_score = self._analyze_device_fingerprints(current_data, baseline_data)
            print(f"   ✅ Device/environment score: {device_score:.3f}")

            # 🔗 STEP 5: FUSION ACROSS ALL DOMAINS
            print(f"🔗 STEP 5: Fusing scores across all domains...")
            final_score = self._fuse_domain_scores(time_series_score, statistical_score, boolean_score, device_score)
            print(f"   ✅ Final fused score: {final_score:.3f}")

            # 🎯 FINAL AUTHORIZATION DECISION
            is_authorized = final_score >= 0.6  # 60% threshold
            confidence = final_score
            recommendation = 'ALLOW: Behavioral analysis passed' if is_authorized else 'BLOCK: Behavioral analysis failed'

            # 📊 COMPREHENSIVE ANALYSIS RESULT
            analysis_result = {
                'is_authorized': is_authorized,
                'confidence': confidence,
                'final_score': final_score,
                'authorization_reason': f'COMPREHENSIVE_ANALYSIS: Final score {final_score:.3f} {"≥" if is_authorized else "<"} 0.6 threshold',
                'analysis_type': 'comprehensive_multi_domain',
                'recommendation': recommendation,
                
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


        
        def _extract_time_series_values(self, data, metric):
            try:
                if metric == 'cursor_movements':
                    # Handle multiple possible keys for cursor movements
                    values = (data.get('cursor_movements', []) or 
                             data.get('cursorMovements', []))

                elif metric == 'cursor_speeds':
                    values = data.get('cursor_speeds', [])

                elif metric == 'key_press_times':
                    # Handle multiple possible keys for key press times
                    values = (data.get('key_press_times', []) or 
                             data.get('keyPressTimes', []))

                elif metric == 'key_hold_times':
                    # Handle multiple possible keys for key hold times
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
            try:
                # Define time-series metrics to analyze
                time_series_metrics = [
                    'cursor_movements', 'cursor_speeds', 'key_press_times', 
                    'key_hold_times', 'scroll_speeds', 'mouseJitter', 
                    'micropause', 'hesitation'
                ]

                total_score = 0
                valid_metrics = 0

                for metric in time_series_metrics:
                    # Extract current values with multiple key variations
                    current_values = self._extract_time_series_values(current_data, metric)
                    baseline_values = self._extract_time_series_values(baseline_data, metric)

                    if not current_values or not baseline_values:
                        continue

                    # Extract statistical descriptors
                    current_stats = self._extract_statistical_descriptors(current_values)
                    baseline_stats = self._extract_statistical_descriptors(baseline_values)

                    if current_stats and baseline_stats:
                        # Compare distributions using Wasserstein distance approximation
                        distribution_similarity = self._compare_distributions(current_stats, baseline_stats)

                        # Compare sequence rhythm (simplified DTW)
                        rhythm_similarity = self._compare_sequence_rhythm(current_values, baseline_values)

                        # Combined similarity for this metric
                        metric_score = (distribution_similarity + rhythm_similarity) / 2
                        total_score += metric_score
                        valid_metrics += 1

                return total_score / max(valid_metrics, 1)

            except Exception as e:
                print(f"Error in time-series analysis: {e}")
                return 0.5  # Default neutral score
        
        def _analyze_statistical_metrics(self, current_data, baseline_data):
            """Extracts key metrics and applies Mahalanobis distance for distribution comparison, returning a normalized similarity score."""
            try:
                import numpy as np
                from scipy.spatial.distance import mahalanobis

                metrics = [
                    'cursor_entropy', 'cursorAngleVariance', 'total_time',
                    'idle_time', 'suspicious_feature_ratio', 'action_count'
                ]

                # Extract metric values
                current_vec = np.array([float(current_data.get(m, 0)) for m in metrics])
                baseline_vec = np.array([float(baseline_data.get(m, 0)) for m in metrics])

                # Covariance matrix (identity if not enough data)
                cov = np.eye(len(metrics))
                try:
                    # If you have multiple baseline samples, use np.cov(baseline_samples, rowvar=False)
                    # Here, we use identity for simplicity
                    dist = mahalanobis(current_vec, baseline_vec, np.linalg.inv(cov))
                except Exception as e:
                    print(f"Mahalanobis calculation error: {e}")
                    dist = np.linalg.norm(current_vec - baseline_vec)

                # Normalize Mahalanobis distance to similarity score (higher is more similar)
                # You can tune the denominator for sensitivity
                similarity = math.exp(-dist / 10)
                return similarity
            except Exception as e:
                print(f"Error in statistical analysis: {e}")
                return 0.5

        def _analyze_boolean_signals(self, current_data, baseline_data):
            """Analyze boolean/categorical signals using rule-based penalties"""
            try:
                boolean_metrics = [
                    'paste_detected', 'is_automated_browser', 'missing_canvas_fingerprint', 
                    'suspicious_flag', 'evasion_signals'
                ]
                
                total_score = 1.0  # Start with perfect score
                
                for metric in boolean_metrics:
                    current_value = current_data.get(metric, False)
                    
                    if metric == 'paste_detected' and current_value:
                        total_score -= 0.2  # Paste detection penalty
                    elif metric == 'is_automated_browser' and current_value:
                        total_score -= 0.5  # Automation penalty
                    elif metric == 'missing_canvas_fingerprint' and current_value:
                        total_score -= 0.3  # Missing fingerprint penalty
                    elif metric == 'suspicious_flag' and current_value:
                        total_score -= 0.4  # Suspicious flag penalty
                    elif metric == 'evasion_signals' and current_value:
                        # Check specific evasion signals
                        evasion_data = current_data.get('evasion_signals', {})
                        if evasion_data.get('webdriver', False):
                            total_score -= 0.6
                        if evasion_data.get('languages_spoofed', False):
                            total_score -= 0.3
                        if evasion_data.get('plugins_spoofed', False):
                            total_score -= 0.3
                
                return max(0.0, total_score)  # Ensure non-negative
                
            except Exception as e:
                print(f"Error in boolean analysis: {e}")
                return 0.5

        def _analyze_device_fingerprints(self, current_data, baseline_data):
            """Analyze device/environment fingerprints using exact matching and partial scoring"""
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
                    
                    if not current_value or not baseline_value:
                        continue
                    
                    if metric == 'devicefingerprint':
                        # Exact matching for device fingerprint
                        if str(current_value) == str(baseline_value):
                            total_score += 1.0
                        else:
                            total_score += 0.0  # Different device
                    
                    elif metric == 'gpu_info':
                        # GPU vendor and renderer matching
                        current_vendor = str(current_value.get('vendor', '')).lower()
                        baseline_vendor = str(baseline_value.get('vendor', '')).lower()
                        
                        if current_vendor == baseline_vendor:
                            total_score += 1.0
                        elif current_vendor and baseline_vendor:
                            total_score += 0.7  # Partial match
                        else:
                            total_score += 0.3  # No match
                    
                    elif metric == 'canvas_metrics':
                        # Canvas dimensions and hash matching
                        current_hash = current_value.get('hash', '')
                        baseline_hash = baseline_value.get('hash', '')
                        
                        if current_hash == baseline_hash:
                            total_score += 1.0
                        elif current_hash and baseline_hash:
                            total_score += 0.6  # Partial match
                        else:
                            total_score += 0.2  # No match
                    
                    elif metric == 'unsualscreenresolution':
                        # Screen resolution matching
                        current_res = f"{current_value.get('width', 0)}x{current_value.get('height', 0)}"
                        baseline_res = f"{baseline_value.get('width', 0)}x{baseline_value.get('height', 0)}"
                        
                        if current_res == baseline_res:
                            total_score += 1.0
                        elif current_res and baseline_res:
                            total_score += 0.8  # Partial match
                        else:
                            total_score += 0.4  # No match
                    
                    valid_metrics += 1
                
                return total_score / max(valid_metrics, 1)
                
            except Exception as e:
                print(f"Error in device analysis: {e}")
                return 0.5

        def _fuse_domain_scores(self, time_series_score, statistical_score, boolean_score, device_score):
            """Fuse scores across all domains using weighted combination"""
            try:
                # Weighted fusion as specified
                final_score = (
                    0.35 * time_series_score +
                    0.30 * statistical_score +
                    0.20 * boolean_score +
                    0.15 * device_score
                )
                
                return max(0.0, min(1.0, final_score))  # Clamp to [0, 1]
                
            except Exception as e:
                print(f"Error in score fusion: {e}")
                return 0.5

        def _extract_statistical_descriptors(self, values):
            """Extract statistical descriptors from a list of values"""
            try:
                if not values or len(values) < 2:
                    return None
                
                numeric_values = [float(v) for v in values if isinstance(v, (int, float)) and not math.isnan(v)]
                if len(numeric_values) < 2:
                    return None
                
                return {
                    'mean': np.mean(numeric_values),
                    'std': np.std(numeric_values),
                    'variance': np.var(numeric_values),
                    'min': np.min(numeric_values),
                    'max': np.max(numeric_values),
                    'entropy': self._calculate_entropy(numeric_values)
                }
                
            except Exception as e:
                print(f"Error extracting statistical descriptors: {e}")
                return None

        def _compare_distributions(self, current_stats, baseline_stats):
            """Compare distributions using statistical measures"""
            try:
                # Simple distribution similarity based on mean and std
                mean_diff = abs(current_stats['mean'] - baseline_stats['mean']) / max(baseline_stats['mean'], 1)
                std_diff = abs(current_stats['std'] - baseline_stats['std']) / max(baseline_stats['std'], 1)
                
                # Combined similarity (lower difference = higher similarity)
                similarity = math.exp(-(mean_diff + std_diff))
                return max(0.0, min(1.0, similarity))
                
            except Exception as e:
                print(f"Error comparing distributions: {e}")
                return 0.5

        def _compare_sequence_rhythm(self, current_values, baseline_values):
            """Compare sequence rhythm using simplified DTW approach"""
            try:
                if len(current_values) < 2 or len(baseline_values) < 2:
                    return 0.5
                
                # Extract timing patterns
                current_timings = self._extract_timing_patterns(current_values)
                baseline_timings = self._extract_timing_patterns(baseline_values)
                
                if not current_timings or not baseline_timings:
                    return 0.5
                
                # Compare timing patterns
                timing_similarity = self._compare_timing_patterns(current_timings, baseline_timings)
                return timing_similarity
                
            except Exception as e:
                print(f"Error comparing sequence rhythm: {e}")
                return 0.5

        def _extract_timing_patterns(self, values):
            """Extract timing patterns from values"""
            try:
                if len(values) < 2:
                    return None
                
                # Extract timestamps or create synthetic timing
                timestamps = []
                for i, val in enumerate(values):
                    if isinstance(val, dict) and 'timestamp' in val:
                        timestamps.append(val['timestamp'])
                    else:
                        # Create synthetic timing if no timestamp
                        timestamps.append(i * 100)  # 100ms intervals
                
                # Calculate intervals
                intervals = []
                for i in range(1, len(timestamps)):
                    intervals.append(timestamps[i] - timestamps[i-1])
                
                return intervals
                
            except Exception as e:
                print(f"Error extracting timing patterns: {e}")
                return None

        def _compare_timing_patterns(self, current_timings, baseline_timings):
            """Compare timing patterns using correlation"""
            try:
                if len(current_timings) < 2 or len(baseline_timings) < 2:
                    return 0.5
                
                # Resample to same length for comparison
                min_length = min(len(current_timings), len(baseline_timings))
                current_resampled = current_timings[:min_length]
                baseline_resampled = baseline_timings[:min_length]
                
                # Calculate correlation coefficient
                correlation = np.corrcoef(current_resampled, baseline_resampled)[0, 1]
                
                # Convert correlation to similarity score
                if math.isnan(correlation):
                    return 0.5
                
                similarity = (correlation + 1) / 2  # Convert [-1, 1] to [0, 1]
                return max(0.0, min(1.0, similarity))
                
            except Exception as e:
                print(f"Error comparing timing patterns: {e}")
                return 0.5

        def _calculate_entropy(self, values):
            """Calculate entropy of a list of values"""
            try:
                if len(values) < 2:
                    return 0.0
                
                # Discretize values into bins
                bins = np.histogram(values, bins=min(10, len(values)//2))[0]
                bins = bins[bins > 0]  # Remove empty bins
                
                if len(bins) < 2:
                    return 0.0
                
                # Calculate Shannon entropy
                probabilities = bins / np.sum(bins)
                entropy = -np.sum(probabilities * np.log2(probabilities))
                
                return entropy
                
            except Exception as e:
                print(f"Error calculating entropy: {e}")
                return 0.0

        def _get_time_series_breakdown(self, current_data, baseline_data):
            """Get detailed breakdown of time-series analysis"""
            try:
                return {
                    'cursor_movements_similarity': self._compare_metric_arrays(
                        current_data.get('cursor_movements', []), 
                        baseline_data.get('cursorMovements', [])
                    ),
                    'key_press_times_similarity': self._compare_metric_arrays(
                        current_data.get('key_press_times', []), 
                        baseline_data.get('keyPressTimes', [])
                    ),
                    'click_timestamps_similarity': self._compare_metric_arrays(
                        current_data.get('click_timestamps', []), 
                        baseline_data.get('clickTimestamps', [])
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
                        current_data.get('cursor_entropy', 0) - baseline_data.get('cursorEntropy', 0)
                    ),
                    'action_count_diff': abs(
                        current_data.get('action_count', 0) - baseline_data.get('actionCount', 0)
                    ),
                    'total_time_diff': abs(
                        current_data.get('total_time', 0) - baseline_data.get('totalTimeToSubmit', 0)
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
                    'suspicious_flag': current_data.get('suspicious_flag', False)
                }
            except Exception as e:
                print(f"Error getting boolean breakdown: {e}")
                return {}

        def _get_device_breakdown(self, current_data, baseline_data):
            """Get detailed breakdown of device analysis"""
            try:
                return {
                    'device_fingerprint_match': str(current_data.get('devicefingerprint', '')) == str(baseline_data.get('deviceFingerprint', '')),
                    'gpu_vendor_match': str(current_data.get('gpu_info', {}).get('vendor', '')).lower() == str(baseline_data.get('gpuInformation', {}).get('vendor', '')).lower(),
                    'screen_resolution_match': f"{current_data.get('unsualscreenresolution', {}).get('width', 0)}x{current_data.get('unsualscreenresolution', {}).get('height', 0)}" == f"{baseline_data.get('unusualScreenResolution', {}).get('width', 0)}x{baseline_data.get('unusualScreenResolution', {}).get('height', 0)}"
                }
            except Exception as e:
                print(f"Error getting device breakdown: {e}")
                return {}

        def _compare_metric_arrays(self, current_array, baseline_array):
            """Compare two arrays of metrics"""
            try:
                if not current_array or not baseline_array:
                    return 0.5
                
                # Simple length-based similarity
                length_similarity = 1.0 - abs(len(current_array) - len(baseline_array)) / max(len(current_array), len(baseline_array), 1)
                
                # Value-based similarity (if arrays contain numeric values)
                if len(current_array) > 0 and len(baseline_array) > 0:
                    try:
                        current_numeric = [float(v) for v in current_array if isinstance(v, (int, float))]
                        baseline_numeric = [float(v) for v in baseline_array if isinstance(v, (int, float))]
                        
                        if current_numeric and baseline_numeric:
                            current_mean = np.mean(current_numeric)
                            baseline_mean = np.mean(baseline_numeric)
                            value_similarity = 1.0 - abs(current_mean - baseline_mean) / max(baseline_mean, 1)
                            return (length_similarity + value_similarity) / 2
                    except:
                        pass
                
                return length_similarity
                
            except Exception as e:
                print(f"Error comparing metric arrays: {e}")
                return 0.5

        def _fallback_analysis(self, current_data, error_message):
            """Fallback analysis when comprehensive analysis fails"""
            try:
                # Basic interaction count validation
                total_interactions = (
                    len(current_data.get('cursor_movements', [])) + 
                    len(current_data.get('key_press_times', [])) + 
                    len(current_data.get('click_timestamps', []))
                )
                
                if total_interactions >= 5:
=======
            # Extract current features
            current_features = self.extract_behavioral_features(current_data)
            if not current_features:
                print(f"⚠️ Failed to extract current behavior features - using basic validation")
                # ENHANCED: Basic validation instead of blocking completely
                total_interactions = (len(current_data.get('cursor_movements', [])) + 
                                    len(current_data.get('key_press_times', [])) + 
                                    len(current_data.get('click_timestamps', [])))

                # If user has some interaction, allow with lower confidence
                if total_interactions >= 3:
>>>>>>> 94e632f46c91c13fdea348e461634f568aeb697c
                    return {
                        'is_authorized': True,
                        'confidence': 0.4,
                        'authorization_reason': f'FALLBACK: Analysis error but {total_interactions} interactions detected',
                        'analysis_type': 'fallback_analysis',
                        'recommendation': 'ALLOW: Fallback approval due to analysis error'
                    }
                else:
                    return {
                        'is_authorized': False,
                        'confidence': 0.3,
                        'authorization_reason': f'FALLBACK_BLOCK: Analysis error and insufficient interactions ({total_interactions})',
                        'analysis_type': 'fallback_analysis',
                        'recommendation': 'BLOCK: Fallback rejection due to analysis error and insufficient data'
                    }
<<<<<<< HEAD
                    
            except Exception as e:
                print(f"Error in fallback analysis: {e}")
=======

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

            baseline_variations = self.generate_enhanced_baseline_variations(baseline_features, num_variations=15)

            if len(baseline_variations) < 2:
                print(f"❌ Insufficient baseline variations for statistical analysis")
>>>>>>> 94e632f46c91c13fdea348e461634f568aeb697c
                return {
                    'is_authorized': False,
                    'confidence': 0.2,
                    'authorization_reason': 'CRITICAL_ERROR: Fallback analysis also failed',
                    'analysis_type': 'critical_error',
                    'recommendation': 'BLOCK: Critical system error'
                }
<<<<<<< HEAD
=======

            # 🔍 STEP 4: CALCULATE MAHALANOBIS DISTANCE
            print(f"🔍 Calculating Mahalanobis distance...")
            mahalanobis_distance = self.calculate_enhanced_mahalanobis_distance(
                current_features, 
                baseline_variations
            )

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
            


                
                

                num_features = len(current_features)
                if num_features > 50:
                    dimension_factor = 1.0  # High dimension = full reliability
                elif num_features > 30:
                    dimension_factor = 0.95  # Medium dimension = slight adjustment
                else:
                    dimension_factor = 0.9  # Low dimension = moderate reduction

                # 4️⃣ BEHAVIORAL CONSISTENCY CHECK: Balanced consistency multiplier

                consistency_factor = 1.0  # No penalty for any consistency level


                min_std_devs = 0.05  
                max_std_devs = 12.0  
                standard_deviations = 0
                original_standard_deviations = standard_deviations
                standard_deviations = max(min_std_devs, min(standard_deviations, max_std_devs))
                print(f"   - After bounds: max({min_std_devs}, min({original_standard_deviations}, {max_std_devs})) = {standard_deviations}")

            base_threshold = 20.0  
            behavioral_threshold = base_threshold
            

            

           

            safe_threshold = behavioral_threshold if behavioral_threshold and behavioral_threshold > 0 else 1e-6
            threshold_factor = max(0, 1.0 - ((standard_deviations - behavioral_threshold) / safe_threshold))  # How close to threshold

            # Default authorization decision based on sigma threshold
            is_authorized = standard_deviations <= behavioral_threshold

            # Default reasons and risk modifiers
            threshold_reason = 'DEFAULT: Fixed behavioral threshold'
            risk_adjustment = 1.0
            consistency_score_susp = 1.0


            # Calculate total interactions for validation
            cursor_movements = len(current_data.get('cursor_movements', [])) + len(current_data.get('cursorMovements', []))
            key_presses = len(current_data.get('key_press_times', [])) + len(current_data.get('keyPressTimes', []))
            clicks = len(current_data.get('click_timestamps', [])) + len(current_data.get('clickTimestamps', []))
            total_interactions = cursor_movements + key_presses + clicks

           
            if total_interactions < 2:
                print(f"⚠️ Insufficient interaction data ({total_interactions} interactions)")
                is_authorized = False
                authorization_reason = f'INSUFFICIENT_DATA: Only {total_interactions} interactions detected - minimum 2 required'
                print(f"❌ OVERRIDE: Authorization set to False due to insufficient interactions ({total_interactions})")

            evasion_signals = current_data.get('evasion_signals', {})
            unusual_patterns = sum(1 for key, value in evasion_signals.items() if value) if evasion_signals else 0

            if unusual_patterns >= 5:
                print(f"🚨 Multiple unusual behavioral patterns detected: {unusual_patterns}")
                is_authorized = False
                authorization_reason = f'AUTOMATION_DETECTED: {unusual_patterns} automation patterns suggest bot behavior'
                print(f"❌ OVERRIDE: Authorization set to False due to unusual patterns ({unusual_patterns})")

            # Calculate confidence based on standard deviations
            if standard_deviations == 0:
                confidence = 1.0
                print(f"   - Path: standard_deviations == 0, confidence = {confidence}")
            elif standard_deviations <= behavioral_threshold:
                # Authorized: confidence decreases as we approach behavioral threshold
                raw_confidence = 1.0 - (standard_deviations / safe_threshold) * 0.4
                confidence = max(0.5, raw_confidence)
            else:
                # Unauthorized: confidence increases with distance beyond threshold
                excess_deviation = standard_deviations - behavioral_threshold
                raw_confidence = 0.6 + (excess_deviation / safe_threshold) * 0.35
                confidence = min(0.95, raw_confidence)

            # Set authorization reason if not already set
            if 'authorization_reason' not in locals():
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
                        authorization_reason = f'REJECTED: Behavioral mismatch beyond {behavioral_threshold:.1f}σ threshold ({standard_deviations:.2f}σ) - Identity not verified'
                    elif standard_deviations <= behavioral_threshold + 2.0:
                        authorization_reason = f'REJECTED: Significant behavioral difference ({standard_deviations:.2f}σ) - Likely different user'
                    else:
                        authorization_reason = f'REJECTED: Major behavioral difference ({standard_deviations:.2f}σ) - Different user detected'

            

            # Determine risk level and scores
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
            if consistency_score_susp < 0.6:
                suspicious_indicators.append(f'Low behavioral consistency ({consistency_score_susp:.1%}) - unauthorized user concern')

            # Multi-factor unauthorized user indicators
            combined_risk_score_susp = (1.0 - consistency_score_susp) * 0.4 + min(standard_deviations / safe_threshold, 2.0) * 0.6
            if combined_risk_score_susp > 1.0:
                suspicious_indicators.append(f'Multi-factor unauthorized user risk (score={combined_risk_score_susp:.3f})')

            analysis_result = {
                'is_authorized': is_authorized,
                'confidence': confidence,
                'anomaly_score': anomaly_score,
                'risk_score': risk_score,
                'authorization_reason': authorization_reason,
                'recommendation': recommendation,

                # 🔍 IDENTITY VERIFICATION DATA (NEW)
                'current_behavior': current_data,  # Current behavioral data for identity verification
                'baseline_data': baseline_data,   # Baseline data for comparison

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
                            
                        },
                        {
                            'metric': 'unusual_patterns',
                            'severity': 'CRITICAL' if unusual_patterns >= 3 else 'MEDIUM' if unusual_patterns >= 1 else 'LOW',
                            'value': unusual_patterns,
                            'threshold': 0
                        },
                        {
                            'metric': 'behavioral_consistency',
                            'threshold': 0.6
                        }
                    ],
                    'suspicious_indicators': suspicious_indicators,

                    # 📊 Enhanced data quality metrics
                    'data_quality_metrics': {
                        
                        
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



            if analysis_result.get('authorization_reason', '').startswith('HARD_BLOCK'):
                print(f"🔒 SKIPPING confidence vs risk check due to hard block")
            else:
                analysis_result = self.apply_risk_confidence_check(analysis_result)


                is_authorized = analysis_result['is_authorized']
                authorization_reason = analysis_result['authorization_reason']
                recommendation = analysis_result['recommendation']


                if confidence > risk_score:
                    print(f"     - Result: AUTHORIZED (Confidence > Risk)")
                elif risk_score > confidence:
                    print(f"     - Result: UNAUTHORIZED (Risk > Confidence)")
                else:
                    print(f"     - Result: EQUAL SCORES (Using original analysis)")


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

                    # 🔐 IDENTITY VERIFICATION DATA (NEW)
                    'current_behavior': current_data,  # Current behavioral data
                    'baseline_data': {},              # No baseline available in fallback

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

                    # 🔐 IDENTITY VERIFICATION DATA (NEW)
                    'current_behavior': current_data,  # Current behavioral data
                    'baseline_data': {},              # No baseline available in fallback

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

                    # 🔐 IDENTITY VERIFICATION DATA (NEW)
                    'current_behavior': current_data,  # Current behavioral data
                    'baseline_data': {},              # No baseline available in fallback

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


        

        def _calculate_cursor_speeds(self, cursor_movements):

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
>>>>>>> 94e632f46c91c13fdea348e461634f568aeb697c


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
                            
                            # 🔐 IDENTITY VERIFICATION DATA (NEW)
                            'current_behavior': behavioral_data,  # Current behavioral data
                            'baseline_data': {},                 # No baseline yet for new users
                            
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
                            'recommendation': f'NEW_USER_APPROVED: New user with limited data ({total_interactions} interactions)',
                            'analysis_type': 'limited_new_user',
                            'requires_more_interaction': True,
                            'session_id': session_id,
                            'total_interactions': total_interactions,
                            
                            # 🔐 IDENTITY VERIFICATION DATA (NEW)
                            'current_behavior': behavioral_data,  # Current behavioral data
                            'baseline_data': {},                 # No baseline yet for new users
                            
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