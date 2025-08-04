import traceback
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
# from .models import UserBehaviordata
import numpy as np
import logging
import json , sys
import csv
import math
from scipy.stats import entropy as shannon_entropy
import os
import re
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from .models import UserBehavior_v3
import datetime
from joblib import load
from sklearn.impute import SimpleImputer
from model.preprocessing import extract_features 
import os
import pandas as pd
import joblib



# Load the trained ML model once
MODEL_PATH = os.path.join(settings.BASE_DIR, 'model', 'model.pkl')
ml_model = load(MODEL_PATH)

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def predict_user_type(request):             
    try:
        request_body = json.loads(request.body.decode('utf-8'))
        behavior = request_body.get("behavior", {})

        
        row = {
            "cursor_movements": behavior.get("cursorMovements", []),
            "cursor_speeds": behavior.get("cursorSpeeds", []),
            "cursor_curvature": behavior.get("cursorCurvature", []),
            "cursor_acceleration": behavior.get("cursorAcceleration", []),
            "key_press_times": behavior.get("keyPressTimes", []),
            "key_hold_times": behavior.get("keyHoldTimes", []),
            "click_timestamps": behavior.get("clickTimestamps", []),
            "click_intervals": behavior.get("clickIntervals", []),

            "keyboard_patterns": behavior.get("keyboardPatterns", []),
            "human_indicators": behavior.get("humanIndicators", []),
            "bot_indicators": behavior.get("botIndicators", []),

           "mouse_movement_debug": behavior.get("mouseMovementDebug", {}),

            "post_paste_activity": behavior.get("postPasteActivity", {}),
            "speed_calculation_debug": behavior.get("speedCalculationDebug", {}),

            "scroll_speeds": behavior.get("scrollSpeeds", []),
            "idle_time": behavior.get("idleTime", 2000),  # default: average pause
            "total_time": behavior.get("total_time", behavior.get("totalTimeToSubmit", 8000)),
            "scroll_changes": behavior.get("scroll_changes", behavior.get("scrollChanges", 1)),
            "paste_detected": behavior.get("paste_detected", behavior.get("pasteDetected", 0)),
            "action_count": behavior.get("action_count", behavior.get("actionCount", 0)),
            "bot_fingerprint_score": behavior.get("bot_fingerprint_score", behavior.get("botFingerprintScore", 0.5)),
            "tab_key_count": behavior.get("tabkeycount", behavior.get("tabKeyCount", 0)),
            "cursor_entropy": behavior.get("cursor_entropy", behavior.get("cursorEntropy", 0.5)),
            "cursor_angle_variance": behavior.get("cursorAngleVariance", 1.0),
            "is_automated_browser": behavior.get("isAutomatedBrowser", False),
            "human_score": behavior.get("human_score", 0.5),
            "bot_score": behavior.get("bot_score", 0.5),
            "mouse_jitter" : behavior.get("mouseJitter", np.nan),
            "micro_pauses" : behavior.get("microPauses", np.nan),
            "hesitation_times" : behavior.get("hesitationTimes", np.nan)

        }
        
        print("📦 Raw behavior input keys:", list(behavior.keys()))
        print("🎯 cursorMovements length:", len(behavior.get("cursorMovements", [])))
        print("🎯 keyPressTimes length:", len(behavior.get("keyPressTimes", [])))

        features_df = extract_features(row).drop("label", errors="ignore")

        # Step 2: Manual inject
        manual_fields = [
            "cursor_entropy", "human_score", "bot_score", "tab_key_count", "cursor_angle_variance",
            "is_automated_browser", "paste_detected", "bot_fingerprint_score", "action_count",
            "total_time", "scroll_changes" , "idle_time"
        ]
        for field in manual_fields:
            features_df[field] = row.get(field, np.nan)

        # Strictly align features: drop extras, add missing, enforce order
        expected_features = joblib.load(os.path.join(settings.BASE_DIR, "model", "model.joblib"))
        if not isinstance(expected_features, list):
            expected_features = list(expected_features)
        features_df = features_df.reindex(columns=expected_features, fill_value=np.nan)
        features_df = features_df.loc[:, expected_features]  # Drop any extra columns, enforce order

        # Debug: print missing features if any
        missing_features = [f for f in expected_features if f not in features_df.columns or features_df[f].isnull().all()]
        if missing_features:
            print("⚠️ Missing features at prediction time:", missing_features)
            # Fill missing features with np.nan (should already be handled by reindex, but double-check)
            for f in missing_features:
                features_df[f] = np.nan

        # No imputer or clip bounds for simple model
        # Debug: print final columns and shape
        print("Final features_df columns:", list(features_df.columns))
        print("Expected features:", expected_features)
        print(len(expected_features))
        print("Shape of features_df:", features_df.shape)

        # Final debug logs
        print("🧪 Runtime input stats:")
        print(features_df.describe())
        print("🔍 Number of NaN features:", features_df.isna().sum().sum())
        print("📉 NaN counts per feature:")
        print(features_df.isna().sum()[features_df.isna().sum() > 0])
        print(features_df.describe())
        print(features_df.iloc[0].to_dict())
        proba = ml_model.predict_proba(features_df)[0][1]
        confidence = round(proba * 100, 2)
        classification = "Human ✅" if proba >= 0.5 else "Bot ❌"

        return JsonResponse({
            "success": True,
            "classification": classification,
            "confidence": float(confidence)
        })
    
    except Exception as e:
        traceback.print_exc()
        exc_type, _, exc_tb = sys.exc_info()
        return JsonResponse({
            "success": False,
            "message": f"Prediction failed: {str(e)} (Line: {exc_tb.tb_lineno})"
        })




def compute_cursor_angle_variance(cursorangle):
    """Compute standard deviation from angle list"""
    if not isinstance(cursorangle, list) or len(cursorangle) < 5:
        return None  # Not enough data
    try:
        cleaned = [float(a) for a in cursorangle if isinstance(a, (int, float))]
        return float(np.std(cleaned))
    except Exception as e:
        print("Error computing angle variance:", e)
        return None



@csrf_exempt
@require_http_methods(["POST"])
def analyze_user(request):
    try:
        data = json.loads(request.body)
        logger.info("\n=== NEW USER ANALYSIS START ===")
        # Get behavior data
        behavior = data.get("behavior", {})
        
        bot_fingerprint_score = behavior.get("botFingerprintScore", 0)
        suspicious_feature_ratio = behavior.get("suspiciousFeatureRatio", 0)
        suspicious_flag = behavior.get("suspiciousFlag", False)
        click_intervals = behavior.get("clickIntervals",0)
        mouseJitter = behavior.get("mouseJitter",[])
        micropause = behavior.get("microPauses",[])
        hesitation = behavior.get("hesitationTimes",[])
        
        
        # Initialize scoring with stricter base values
        human_score = 0.0 # Start neutral
        bot_score = 0.0    # Start neutral
        bot_indicators = []
        human_indicators = []
        has_human_behavior = False  # Ensure this is always initialized at the start
        
        # Strict user agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if any(tool in user_agent for tool in ['phantomjs', 'headless', 'selenium', 'puppeteer', 'playwright', 'cypress']):
            if not any(browser in user_agent for browser in ['chrome', 'firefox', 'safari', 'edge']):
                return JsonResponse({
                    "status": "rejected",
                    "message": "Automated browser detected! Access denied.",
                    "classification": "Bot",
                    "reason": "Known automation tool detected"
                }, status=200)
        
        # Calculate metrics with stricter thresholds
        cursor_movements = behavior.get("cursorMovements", [])
        key_press_times = behavior.get("keyPressTimes", [])
        key_hold_times = behavior.get("keyHoldTimes", [])
        click_timestamps = behavior.get("clickTimestamps", [])
        cursor_speeds = behavior.get("cursorSpeeds", [])
        cursor_acceleration = behavior.get("cursorAcceleration", [])
        cursor_curvature = behavior.get("cursorCurvature", [])
        total_time = behavior.get("totalTimeToSubmit", 0)
        click_intervals = behavior.get("clickIntervals",[])
        mouse_movement_debug = behavior.get("mouseMovementDebug", {})
        speed_calculation_debug = behavior.get("speedCalculationDebug", {})
        post_paste_activity = behavior.get("postPasteActivity", {})
        keyboard_patterns = behavior.get("keyboardPatterns", [])
        suspicious_patterns = behavior.get("suspiciousPatterns", [])
        action_count = behavior.get("actionCount", 0)
        is_automated_browser = behavior.get("isAutomatedBrowser", False)
        cursor_entropy = behavior.get("cursorEntropy", 0)
        scroll_speeds = behavior.get("scrollSpeeds", [])
        scroll_changes = behavior.get("scrollChanges", 0)
        idle_time = behavior.get("idleTime", 0)
        honeypot_value = behavior.get("honeypotValue", "")
        tabKeyCount = behavior.get("tabkeyCount", 0)
        cursorangle = behavior.get("cursorAngle" , [])
        mouseJitter = behavior.get("mouseJitter",[])
        micropause = behavior.get("microPauses",[])
        hesitation = behavior.get("hesitationTimes",[])
        devicefingerprint = behavior.get("deviceFingerprint",0)
        missing_canvas_fingerprint = behavior.get("missingCanvasFingerprint",False)
        canvas_metrics = behavior.get("canvas_metrics",{})
        unsualscreenresolution = behavior.get("unusualScreenResolution",{})
        gpu_info = behavior.get("gpuInformation",{})
        timing_metrics = behavior.get("timingMetrics",{})
        evasion_signals = behavior.get("evasionSignals",{})


        if mouse_movement_debug:
            dist = mouse_movement_debug.get("distance", None)
            if dist is not None and dist > 0:
                human_score += 0.01
                human_indicators.append("mouse_movement_debug_present")
   
        if speed_calculation_debug:
            raw_speed = speed_calculation_debug.get("rawSpeed", None)
            # Handle both list and single value cases with proper null checking
            if raw_speed is not None:
                if isinstance(raw_speed, list) and len(raw_speed) > 0:
                    # Check if list has any positive values
                    if any(speed > 0 for speed in raw_speed if isinstance(speed, (int, float)) and speed is not None):
                        human_score += 0.01
                        human_indicators.append("speed_calculation_debug_present")
                elif isinstance(raw_speed, (int, float)) and raw_speed > 0:
                    human_score += 0.01
                    human_indicators.append("speed_calculation_debug_present")

        if post_paste_activity:
            actions = post_paste_activity.get("actionsAfterPaste", [])
            if actions and len(actions) > 0:
                human_score += 0.01
                human_indicators.append("post_paste_activity_present")
  
        if keyboard_patterns and len(keyboard_patterns) > 3:
            human_score += 0.01
            human_indicators.append("keyboard_patterns_present")
      
        if suspicious_patterns and len(suspicious_patterns) > 0:
            bot_score += 0.01
            bot_indicators.append("suspicious_patterns_present")
        
        if action_count and action_count > 10:
            human_score += 0.01
            human_indicators.append("action_count_present")
        
        if tabKeyCount and tabKeyCount > 2:
            human_score += 0.01
            human_indicators.append("tabKeyCount_present")
        
        if mouseJitter and isinstance(mouseJitter, list) and sum(mouseJitter) > 0:
            human_score += 0.01
            human_indicators.append("mouseJitter_present")
        
        if micropause and isinstance(micropause, list) and sum(micropause) > 0:
            human_score += 0.01
            human_indicators.append("micropause_present")
        
        if hesitation and isinstance(hesitation, list) and sum(hesitation) > 0:
            human_score += 0.01
            human_indicators.append("hesitation_present")
       
        if devicefingerprint:
            human_score += 0.01
            human_indicators.append("devicefingerprint_present")
        
        if canvas_metrics and canvas_metrics.get("width", 0) > 0 and canvas_metrics.get("height", 0) > 0:
            human_score += 0.01
            human_indicators.append("canvas_metrics_present")
        
        if unsualscreenresolution:
            # Check actual screen resolution properties with proper null handling
            width_height = unsualscreenresolution.get("width_height", "")
            inner_width = unsualscreenresolution.get("inner_width", 0)
            device_pixel_ratio = unsualscreenresolution.get("device_pixel_ratio", 0)
            is_unusual = unsualscreenresolution.get("is_unusual", False)
            spoofed_mismatch = unsualscreenresolution.get("spoofedMismatch", False)
            aspect_ratio = unsualscreenresolution.get("aspectRatio", 0)
            
            # Convert None values to 0 for proper comparison
            device_pixel_ratio = device_pixel_ratio if device_pixel_ratio is not None else 0
            aspect_ratio = aspect_ratio if aspect_ratio is not None else 0
            inner_width = inner_width if inner_width is not None else 0
            
            # Flag suspicious screen resolution indicators
            if is_unusual:
                human_score += 0.01
                human_indicators.append("unusual_screen_detected")
            if spoofed_mismatch:
                bot_score += 0.08
                bot_indicators.append("screen_spoofed_mismatch")
            if device_pixel_ratio < 0.5 or device_pixel_ratio > 5:  # Very unusual pixel ratio
                bot_score += 0.06
                bot_indicators.append("suspicious_pixel_ratio")
            if aspect_ratio < 0.5 or aspect_ratio > 5:  # Very unusual aspect ratio
                bot_score += 0.05
                bot_indicators.append("suspicious_aspect_ratio")
            if inner_width > 0 and inner_width < 300:  # Very small inner width
                bot_score += 0.07
                bot_indicators.append("suspicious_inner_width")
            
            # Reward normal screen properties
            if width_height and inner_width > 800 and 0.8 <= device_pixel_ratio <= 3.0 and 1.0 <= aspect_ratio <= 2.5:
                human_score += 0.01
                human_indicators.append("normal_screen_properties")
        
        if gpu_info:
            vendor = str(gpu_info.get("vendor", "")).lower()
            if vendor and vendor not in ["microsoft", "llvmpipe", "swiftshader", "mesa", "google", "virtualbox", "vmware", "parallels"]:
                human_score += 0.01
                human_indicators.append("gpu_info_present")
        
        if timing_metrics:
            human_score += 0.01
            human_indicators.append("timing_metrics_present")
        
        if evasion_signals and any(evasion_signals.values()):
            bot_score += 0.01
            bot_indicators.append("evasion_signals_present")
    
        cursor_angle_variance = compute_cursor_angle_variance(cursorangle)  
        behavior["cursor_angle_variance"] = cursor_angle_variance

        if cursor_angle_variance is not None:
            if cursor_angle_variance > 20:  # Good variance threshold
                human_score += 0.15
                human_indicators.append("varied_cursor_angles")
                has_human_behavior = True
            elif cursor_angle_variance > 10:  # Moderate variance
                human_score += 0.10
                human_indicators.append("moderate_cursor_variation")
                has_human_behavior = True
            elif cursor_angle_variance > 5:  # Some variance
                human_score += 0.05
                human_indicators.append("some_cursor_variation")
                has_human_behavior = True
            else:
                # Penalize very low variance - could indicate bot-like straight paths
                bot_score += 0.10  # Balanced penalty
                bot_indicators.append("static_cursor_path")
        
        cursor_movement_count = len(cursor_movements) if cursor_movements else 0
        if cursor_movement_count > 5:  # Normal cursor movement users - BALANCED
            logger.info(f"=== BALANCED NORMAL CURSOR MOVEMENT ANALYSIS: {cursor_movement_count} movements ===")
            
            # Reasonable boost for cursor activity
            human_score += 0.18  # Good base reward
            has_human_behavior = True
            human_indicators.append("active_cursor_movement")
            logger.info(f"ACTIVE CURSOR MOVEMENT: {cursor_movement_count} movements")
            
            # Additional boosts for other activity
            if key_press_times and len(key_press_times) > 0:
                human_score += 0.15  # Good reward
                has_human_behavior = True
                human_indicators.append("keyboard_with_cursor_normal")
                logger.info("KEYBOARD + CURSOR ACTIVITY")
                
            if click_timestamps and len(click_timestamps) > 0:
                human_score += 0.15  # Good reward
                has_human_behavior = True
                human_indicators.append("clicking_with_cursor_normal")
                logger.info("CLICKING + CURSOR ACTIVITY")
                
            # Good boost for diverse activity
            if (key_press_times and len(key_press_times) > 0) and (click_timestamps and len(click_timestamps) > 0):
                human_score += 0.20  # Good reward for comprehensive activity
                has_human_behavior = True
                human_indicators.append("comprehensive_normal_activity")
                logger.info("COMPREHENSIVE NORMAL ACTIVITY")
                
            # Moderate boost for natural interaction patterns
            if scroll_speeds and len(scroll_speeds) > 0:
                human_score += 0.12  # Good reward
                has_human_behavior = True
                human_indicators.append("scroll_activity_normal")
                logger.info("SCROLL + CURSOR ACTIVITY")
                
            # Scaled boosts for active cursor users
            if cursor_movement_count >= 20:  # Very active users
                human_score += 0.12
                human_indicators.append("very_active_cursor_movement")
                logger.info("VERY ACTIVE CURSOR MOVEMENT")
            elif cursor_movement_count >= 10:  # Moderately active
                human_score += 0.08
                human_indicators.append("moderate_cursor_movement")
                logger.info("MODERATE CURSOR MOVEMENT")
                
            # Reasonable timing bonus
            if total_time > 500:  # Any reasonable time
                human_score += 0.10
                has_human_behavior = True
                human_indicators.append("reasonable_timing_normal")
                logger.info(f"REASONABLE TIMING FOR NORMAL USER: {total_time}ms")
        
        # 1. Balanced Typing Analysis - reasonable thresholds
        if key_press_times and len(key_press_times) >= 2:
            typing_intervals = [key_press_times[i] - key_press_times[i-1] for i in range(1, len(key_press_times))]
            avg_typing = sum(typing_intervals) / len(typing_intervals)
            std_typing = np.std(typing_intervals) if len(typing_intervals) > 1 else 0
            
            # Reasonable typing speed ranges
            if 30 <= avg_typing <= 1000:  # Good human typing range
                human_score += 0.18  # Good reward
                has_human_behavior = True
                human_indicators.append("natural_typing")
                logger.info(f"NATURAL TYPING: avg={avg_typing:.1f}ms, std={std_typing:.1f}")
                
                # Bonus for variance
                if std_typing > 8:  # Good variance
                    human_score += 0.12  # Good bonus for variance
                    human_indicators.append("typing_variance")
                elif std_typing > 3:  # Some variance
                    human_score += 0.08
                    human_indicators.append("minimal_typing_variance")
                    
            elif avg_typing < 5:  # Very fast typing is suspicious
                bot_score += 0.20  # Meaningful penalty
                bot_indicators.append("superhuman_typing_speed")
                logger.info(f"SUSPICIOUS TYPING SPEED: avg={avg_typing:.1f}ms")
            elif avg_typing > 3000:  # Very slow typing is suspicious
                bot_score += 0.15  # Meaningful penalty
                bot_indicators.append("unnaturally_slow_typing")
            elif 5 <= avg_typing < 30:  # Fast but potentially human
                human_score += 0.12
                has_human_behavior = True
                human_indicators.append("fast_typing")
            else:  # Other reasonable cases
                human_score += 0.10
                has_human_behavior = True
                human_indicators.append("acceptable_typing")

        # 2. Balanced Cursor Movement Analysis
        if cursor_movements and len(cursor_movements) >= 2:
            movement_times = [m["timestamp"] for m in cursor_movements]
            movement_durations = [movement_times[i] - movement_times[i-1] for i in range(1, len(movement_times))]
            avg_duration = sum(movement_durations) / len(movement_durations)
            std_duration = np.std(movement_durations) if len(movement_durations) > 1 else 0
            
            # Reasonable movement patterns
            if 2 <= avg_duration <= 2000:  # Good movement speed range
                human_score += 0.15  # Good reward
                has_human_behavior = True
                human_indicators.append("natural_movement")
                logger.info(f"NATURAL MOVEMENT: avg={avg_duration:.1f}ms, std={std_duration:.1f}")
                
                # Bonus for variance
                if std_duration > 5:  # Good variance
                    human_score += 0.10  # Good bonus for variance
                    human_indicators.append("movement_variance")
                elif std_duration > 1:  # Some variance
                    human_score += 0.06
                    human_indicators.append("minimal_movement_variance")
                    
            elif avg_duration < 0.5:  # Very fast movement is suspicious
                bot_score += 0.15  # Meaningful penalty
                bot_indicators.append("superhuman_movement_speed")
            elif avg_duration > 5000:  # Very slow movement is suspicious
                bot_score += 0.12  # Meaningful penalty
                bot_indicators.append("unnaturally_slow_movement")
            elif 0.5 <= avg_duration < 2:  # Fast but potentially human
                human_score += 0.10
                has_human_behavior = True
                human_indicators.append("fast_movement")
            else:  # Other reasonable cases
                human_score += 0.08
                has_human_behavior = True
                human_indicators.append("acceptable_movement")

        # 3. Balanced Click Analysis
        if click_timestamps and len(click_timestamps) >= 2:
            click_intervals = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
            avg_click = sum(click_intervals) / len(click_intervals)
            std_click = np.std(click_intervals) if len(click_intervals) > 1 else 0
            
            # Reasonable clicking patterns
            if 50 <= avg_click <= 8000:  # Good click timing range
                human_score += 0.15  # Good reward
                has_human_behavior = True
                human_indicators.append("natural_clicking")
                logger.info(f"NATURAL CLICKING: avg={avg_click:.1f}ms, std={std_click:.1f}")
                
                # Bonus for variance
                if std_click > 20:  # Good variance
                    human_score += 0.10  # Good bonus for variance
                    human_indicators.append("clicking_variance")
                elif std_click > 5:  # Some variance
                    human_score += 0.06
                    human_indicators.append("minimal_clicking_variance")
                    
            elif avg_click < 20:  # Very fast clicking is suspicious
                bot_score += 0.18  # Meaningful penalty
                bot_indicators.append("superhuman_clicking_speed")
            elif avg_click > 15000:  # Very slow clicking is suspicious
                bot_score += 0.12  # Meaningful penalty
                bot_indicators.append("unnaturally_slow_clicking")
            elif 20 <= avg_click < 50:  # Fast but potentially human
                human_score += 0.10
                has_human_behavior = True
                human_indicators.append("fast_clicking")
            else:  # Other reasonable cases
                human_score += 0.08
                has_human_behavior = True
                human_indicators.append("acceptable_clicking")
        elif click_timestamps and len(click_timestamps) == 1:
            # Single click gets good credit
            human_score += 0.12
            has_human_behavior = True
            human_indicators.append("single_click")

        # 4. Balanced Timing Analysis
        if total_time > 0:
            # Reasonable timing expectations
            if 1000 <= total_time <= 180000:  # 1 second to 3 minutes is reasonable
                human_score += 0.18  # Good reward
                has_human_behavior = True
                human_indicators.append("natural_timing")
                logger.info(f"NATURAL TIMING: {total_time}ms")
            elif 500 <= total_time <= 300000:  # Extended reasonable range
                human_score += 0.15
                has_human_behavior = True
                human_indicators.append("acceptable_timing")
                logger.info(f"ACCEPTABLE TIMING: {total_time}ms")
            elif total_time < 200:  # Very fast completion is suspicious
                bot_score += 0.15  # Meaningful penalty
                bot_indicators.append("suspiciously_fast_timing")
            elif total_time > 600000:  # Very slow completion is suspicious
                bot_score += 0.10  # Moderate penalty
                bot_indicators.append("suspiciously_slow_timing")
            else:
                # Other reasonable times get some credit
                human_score += 0.10
                has_human_behavior = True
                human_indicators.append("basic_timing")
        
        # 5. Enhanced Curvature Analysis - More human-friendly
        if cursor_curvature:
            avg_curvature = sum(cursor_curvature) / len(cursor_curvature)
            curvature_std = np.std(cursor_curvature) if len(cursor_curvature) > 1 else 0
            
            logger.info(f"CURVATURE ANALYSIS: avg={avg_curvature:.3f}, std={curvature_std:.3f}")
            
            # Much more generous curvature thresholds
            if 0.2 <= avg_curvature <= 4.0 and curvature_std > 0.08:  # Very wide natural curvature range
                human_score += 0.18  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_curvature")
                logger.info("NATURAL CURVATURE DETECTED")
            elif 0.1 <= avg_curvature <= 6.0 and curvature_std > 0.04:  # Even more generous
                human_score += 0.15
                has_human_behavior = True
                human_indicators.append("acceptable_curvature")
                logger.info("ACCEPTABLE CURVATURE DETECTED")
            elif avg_curvature > 0.05 and curvature_std > 0.01:  # Any reasonable variance
                human_score += 0.12
                has_human_behavior = True
                human_indicators.append("basic_curvature")
            else:
                # Penalize extreme cases (perfectly straight lines or impossible curves)
                if avg_curvature < 0.005 or avg_curvature > 15.0:
                    bot_score += 0.06
                    bot_indicators.append("unnatural_curvature")

        # 6. Enhanced Key Hold Analysis - More human-friendly
        if key_hold_times:
            avg_hold = sum(key_hold_times) / len(key_hold_times)
            std_hold = np.std(key_hold_times) if len(key_hold_times) > 1 else 0
            
            logger.info(f"KEY HOLD ANALYSIS: avg={avg_hold:.1f}ms, std={std_hold:.1f}")
            
            # Much more generous key hold patterns
            if 8 <= avg_hold <= 2000 and std_hold > 2:  # Very wide range for natural key holds
                human_score += 0.18  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_key_hold")
                logger.info("NATURAL KEY HOLD DETECTED")
            elif 5 <= avg_hold <= 3000 and (std_hold > 1 or len(key_hold_times) == 1):  # Single key hold or minimal variance
                human_score += 0.15
                has_human_behavior = True
                human_indicators.append("acceptable_key_hold")
                logger.info("ACCEPTABLE KEY HOLD DETECTED")
            elif 3 <= avg_hold <= 5000:  # Any reasonable key hold time
                human_score += 0.12
                has_human_behavior = True
                human_indicators.append("basic_key_hold")
            elif avg_hold < 2 or avg_hold > 10000 or (avg_hold > 5000 and std_hold < 0.5):  # Penalize extreme cases
                bot_score += 0.08
                bot_indicators.append("unnatural_key_hold")
            else:
                # Default: any key hold activity gets some credit
                human_score += 0.10
                has_human_behavior = True
                human_indicators.append("minimal_key_hold")
        
        # 7. Enhanced Speed and Acceleration Analysis - More balanced
        if cursor_speeds and len(cursor_speeds) > 1:
            avg_speed = np.mean(cursor_speeds)
            speed_std = np.std(cursor_speeds)
            max_speed = max(cursor_speeds)
            
            # More generous speed thresholds
            if 10 <= avg_speed <= 2000 and speed_std > 5:  # Natural human speed variation
                human_score += 0.12
                has_human_behavior = True
                human_indicators.append("natural_cursor_speed")
                logger.info(f"NATURAL CURSOR SPEED: avg={avg_speed:.1f}, std={speed_std:.1f}")
            elif avg_speed > 5 and speed_std > 2:  # Any reasonable variation
                human_score += 0.08
                has_human_behavior = True
                human_indicators.append("varied_cursor_speed")
            elif avg_speed > 8000 or speed_std < 0.2:  # Penalize extreme speed patterns
                bot_score += 0.06
                bot_indicators.append("unnatural_cursor_speed")
        
        if cursor_acceleration and len(cursor_acceleration) > 1:
            acceleration_std = np.std(cursor_acceleration)
            
            # Any acceleration variation is human-like
            if acceleration_std > 10:  # Natural acceleration patterns
                human_score += 0.10
                has_human_behavior = True
                human_indicators.append("natural_acceleration")
            elif acceleration_std > 2:  # Minimal variation
                human_score += 0.06
                has_human_behavior = True
                human_indicators.append("basic_acceleration")
        
        # 8. Additional Human Behavior Boosts
        if honeypot_value == "":  # Correct honeypot behavior
            human_score += 0.05
            has_human_behavior = True
            human_indicators.append("correct_honeypot")
        elif honeypot_value:  # Incorrect honeypot (bot-like)
            bot_score += 0.15
            bot_indicators.append("honeypot_filled")
        
        if idle_time > 0:  # Any idle time suggests human thinking
            if 100 <= idle_time <= 30000:  # Reasonable thinking time
                human_score += 0.08
                has_human_behavior = True
                human_indicators.append("natural_idle_time")
            elif idle_time > 30000:  # Extended thinking (still human)
                human_score += 0.05
                has_human_behavior = True
                human_indicators.append("extended_idle_time")
        
        # Enhanced activity diversity bonus - More balanced
        activity_count = 0
        if cursor_movements and len(cursor_movements) > 0: activity_count += 1
        if key_press_times and len(key_press_times) > 0: activity_count += 1
        if click_timestamps and len(click_timestamps) > 0: activity_count += 1
        if scroll_speeds and len(scroll_speeds) > 0: activity_count += 1
        if key_hold_times and len(key_hold_times) > 0: activity_count += 1
        
        if activity_count >= 4:  # Multiple types of interaction
            human_score += 0.15
            has_human_behavior = True
            human_indicators.append("comprehensive_interaction")
            logger.info("COMPREHENSIVE HUMAN INTERACTION DETECTED")
        elif activity_count >= 3:
            human_score += 0.12
            has_human_behavior = True
            human_indicators.append("diverse_interaction")
            logger.info("DIVERSE HUMAN INTERACTION DETECTED")
        elif activity_count >= 2:
            human_score += 0.08
            has_human_behavior = True
            human_indicators.append("basic_interaction")
            logger.info("BASIC HUMAN INTERACTION DETECTED")
        elif activity_count == 1:  # Only one type of activity - often normal
            # Only penalize if it's extremely minimal activity
            total_activity = (len(cursor_movements or []) + len(key_press_times or []) + 
                            len(click_timestamps or []) + len(scroll_speeds or []) + len(key_hold_times or []))
            if total_activity < 2:  # Extremely minimal activity
                bot_score += 0.02  # Very reduced penalty
                bot_indicators.append("very_limited_activity")
        elif activity_count == 0:  # No meaningful activity - may be bot
            bot_score += 0.05  # Much reduced penalty
            bot_indicators.append("no_meaningful_interaction")
            
        # Advanced bot pattern detection - balanced penalties
        # 1. Perfect timing patterns (automation signature) - reasonable detection
        if key_press_times and len(key_press_times) >= 10:  # Reasonable threshold
            typing_intervals = [key_press_times[i] - key_press_times[i-1] for i in range(1, len(key_press_times))]
            typing_std = np.std(typing_intervals)
            if typing_std < 2:  # Reasonable consistency requirement
                bot_score += 0.15  # Meaningful penalty
                bot_indicators.append("perfect_typing_timing")
                logger.info(f"PERFECT TYPING TIMING DETECTED: std={typing_std:.1f}")
                
        # 2. Perfect click intervals - reasonable detection
        if click_timestamps and len(click_timestamps) >= 8:  # Reasonable threshold
            click_intervals = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
            click_std = np.std(click_intervals)
            if click_std < 5:  # Reasonable consistency requirement
                bot_score += 0.12  # Meaningful penalty
                bot_indicators.append("perfect_click_intervals")
                logger.info(f"PERFECT CLICK INTERVALS DETECTED: std={click_std:.1f}")
                
        # 3. Lack of human micro-behaviors - balanced approach
        micro_behavior_count = 0
        if mouseJitter and isinstance(mouseJitter, list) and sum(mouseJitter) > 0:
            micro_behavior_count += 1
        if micropause and isinstance(micropause, list) and sum(micropause) > 0:
            micro_behavior_count += 1
        if hesitation and isinstance(hesitation, list) and sum(hesitation) > 0:
            micro_behavior_count += 1
            
        # Penalize lack of micro-behaviors with significant activity
        if micro_behavior_count == 0 and (
            (key_press_times and len(key_press_times) > 20) or 
            (cursor_movements and len(cursor_movements) > 30) or 
            (click_timestamps and len(click_timestamps) > 10)
        ):
            bot_score += 0.12  # Meaningful penalty
            bot_indicators.append("no_micro_behaviors")
            logger.info("NO MICRO BEHAVIORS WITH SIGNIFICANT ACTIVITY - POTENTIAL BOT")
            
        # 4. Entropy-based detection - balanced threshold
        if cursor_entropy is not None and cursor_entropy < 0.01:  # Reasonable threshold
            bot_score += 0.12  # Meaningful penalty
            bot_indicators.append("low_entropy")
            logger.info(f"LOW ENTROPY DETECTED: {cursor_entropy}")
            
        # 5. Linear movement patterns - more reasonable
        if cursor_movements and len(cursor_movements) >= 15:  # Higher threshold
            linear_movements = 0
            for i in range(2, len(cursor_movements)):
                if ('x' in cursor_movements[i] and 'y' in cursor_movements[i] and 
                    'x' in cursor_movements[i-1] and 'y' in cursor_movements[i-1] and
                    'x' in cursor_movements[i-2] and 'y' in cursor_movements[i-2]):
                    
                    # Check if three consecutive points are collinear
                    x1, y1 = cursor_movements[i-2]['x'], cursor_movements[i-2]['y']
                    x2, y2 = cursor_movements[i-1]['x'], cursor_movements[i-1]['y']
                    x3, y3 = cursor_movements[i]['x'], cursor_movements[i]['y']
                    
                    # Calculate cross product to check collinearity
                    cross_product = abs((y2 - y1) * (x3 - x1) - (y3 - y1) * (x2 - x1))
                    if cross_product < 0.5:  # More strict collinearity check
                        linear_movements += 1
                        
            linear_ratio = linear_movements / len(cursor_movements)
            if linear_ratio > 0.9:  # Higher threshold - only very linear movement
                bot_score += 0.10  # Reduced penalty
                bot_indicators.append("excessive_linear_movements")
                logger.info(f"EXCESSIVE LINEAR MOVEMENTS: {linear_ratio:.2f}")
                
        # 6. Impossible speed consistency - more reasonable
        if cursor_speeds and len(cursor_speeds) >= 8:  # Higher threshold
            speed_std = np.std(cursor_speeds)
            speed_mean = np.mean(cursor_speeds)
            if speed_std < speed_mean * 0.02 and speed_mean > 200:  # More strict consistency check
                bot_score += 0.08  # Reduced penalty
                bot_indicators.append("impossible_speed_consistency")
                logger.info(f"IMPOSSIBLE SPEED CONSISTENCY: mean={speed_mean:.1f}, std={speed_std:.1f}")
                
        # 7. No variance in measured metrics - more reasonable
        zero_variance_count = 0
        if key_press_times and len(key_press_times) > 5:  # Higher threshold
            typing_intervals = [key_press_times[i] - key_press_times[i-1] for i in range(1, len(key_press_times))]
            if np.var(typing_intervals) < 0.5:  # More strict variance check
                zero_variance_count += 1
                
        if cursor_speeds and len(cursor_speeds) > 5:  # Higher threshold
            if np.var(cursor_speeds) < 0.5:  # More strict variance check
                zero_variance_count += 1
                
        if key_hold_times and len(key_hold_times) > 5:  # Higher threshold
            if np.var(key_hold_times) < 0.5:  # More strict variance check
                zero_variance_count += 1
                
        if zero_variance_count >= 3:  # Require more evidence
            bot_score += 0.15  # Reduced penalty
            bot_indicators.append("multiple_zero_variance_metrics")
            logger.info(f"MULTIPLE ZERO VARIANCE METRICS: {zero_variance_count}")
        elif zero_variance_count >= 2:
            bot_score += 0.08  # Reduced penalty
            bot_indicators.append("zero_variance_metric")

        # --- NEW METRICS INTEGRATION ---
        # 10. GPU Info Analysis - More balanced
        if gpu_info:
            vendor = str(gpu_info.get("vendor", "")).lower()
            renderer = str(gpu_info.get("renderer", "")).lower()
            # Only flag clearly suspicious/VM GPU vendors - not legitimate ones
            definitely_suspicious_vendors = ["llvmpipe", "swiftshader", "virtualbox", "vmware", "parallels"]
            if any(v in vendor for v in definitely_suspicious_vendors) or any(v in renderer for v in definitely_suspicious_vendors):
                bot_score += 0.08  # Reduced penalty
                bot_indicators.append("suspicious_gpu_vendor")
            elif vendor and renderer:
                human_score += 0.05
                human_indicators.append("normal_gpu_info")

        # 11. Missing Canvas Fingerprint
        if missing_canvas_fingerprint:
            bot_score += 0.15
            bot_indicators.append("missing_canvas_fingerprint")
        else:
            human_score += 0.03
            human_indicators.append("canvas_fingerprint_present")

        # 12. Timing Metrics (performance timing analysis)
        if timing_metrics:
            # Check for suspicious timing values
            ttfb = timing_metrics.get("ttfb", None)
            dom_interactive = timing_metrics.get("domInteractive", None)
            dom_content_loaded = timing_metrics.get("domContentLoaded", None)
            load_time = timing_metrics.get("loadTime", None)
            xhr_fetch_time = timing_metrics.get("xhrFetchTime", None)
            rtt = timing_metrics.get("rtt", None)
            jitter = timing_metrics.get("jitter", None)
            eval_math_timing = timing_metrics.get("evalMathTiming", None)
            clock_skew = timing_metrics.get("clockSkew", None)
            
            # Flag suspicious timing values
            if ttfb is not None and (ttfb < 0 or ttfb > 5000):
                bot_score += 0.08
                bot_indicators.append("suspicious_ttfb")
            if dom_interactive is not None and (dom_interactive < 0 or dom_interactive > 10000):
                bot_score += 0.08
                bot_indicators.append("suspicious_dom_interactive")
            if load_time is not None and (load_time < -2000000000000 or load_time > 60000):  # Very negative or very high
                bot_score += 0.08
                bot_indicators.append("suspicious_load_time")
            if xhr_fetch_time is not None and (xhr_fetch_time < 0 or xhr_fetch_time > 5000):
                bot_score += 0.08
                bot_indicators.append("suspicious_xhr_fetch_time")
            if clock_skew is not None and abs(clock_skew) > 1000:  # Very high clock skew
                bot_score += 0.08
                bot_indicators.append("suspicious_clock_skew")
                
            # Reward normal timing metrics
            normal_timing_count = 0
            if ttfb is not None and 0 <= ttfb <= 2000: normal_timing_count += 1
            if dom_interactive is not None and 0 <= dom_interactive <= 5000: normal_timing_count += 1
            if xhr_fetch_time is not None and 0 <= xhr_fetch_time <= 1000: normal_timing_count += 1
            if normal_timing_count >= 2:
                human_score += 0.05
                human_indicators.append("normal_timing_metrics")

        # 13. Evasion Signals - Check for actual evasion patterns
        if evasion_signals:
            # Check for bot evasion indicators with proper null handling
            idle_resume_jerk = evasion_signals.get("idleResumeAngularJerk", 0)
            thermal_hover_noise = evasion_signals.get("thermalHoverNoise", 0)
            hover_positions = evasion_signals.get("hoverPositions", [])
            deviation_angle = evasion_signals.get("deviation_angle", 0)
            acceleration_variance = evasion_signals.get("acceleration_variance", 0)
            path_entropy = evasion_signals.get("path_entropy", 0)
            cursor_micro_jitter = evasion_signals.get("cursor_micro_jitter", 0)
            
            # Convert None values to 0 for proper comparison
            idle_resume_jerk = idle_resume_jerk if idle_resume_jerk is not None else 0
            thermal_hover_noise = thermal_hover_noise if thermal_hover_noise is not None else 0
            deviation_angle = deviation_angle if deviation_angle is not None else 0
            acceleration_variance = acceleration_variance if acceleration_variance is not None else 0
            path_entropy = path_entropy if path_entropy is not None else 0
            cursor_micro_jitter = cursor_micro_jitter if cursor_micro_jitter is not None else 0
            
            # Flag suspicious evasion patterns
            if idle_resume_jerk > 0.5:  # High angular jerk indicates bot-like movement
                bot_score += 0.12
                bot_indicators.append("high_idle_resume_jerk")
            if thermal_hover_noise > 0.3:  # Thermal noise patterns
                bot_score += 0.10
                bot_indicators.append("thermal_hover_noise_detected")
            if isinstance(hover_positions, list) and len(hover_positions) > 50:  # Too many hover positions
                bot_score += 0.08
                bot_indicators.append("excessive_hover_positions")
            if deviation_angle > 2.0:  # High deviation angle
                bot_score += 0.10
                bot_indicators.append("high_deviation_angle")
            if acceleration_variance < 0.01 and acceleration_variance > 0:  # Too consistent acceleration
                bot_score += 0.12
                bot_indicators.append("low_acceleration_variance")
            if path_entropy < 0.1 and path_entropy > 0:  # Very low path entropy
                bot_score += 0.15
                bot_indicators.append("low_path_entropy")
            if cursor_micro_jitter < 0.05 and cursor_micro_jitter >= 0:  # No micro jitter
                bot_score += 0.10
                bot_indicators.append("no_cursor_micro_jitter")
                
            # Reward natural evasion patterns (human-like variability)
            natural_patterns = 0
            if 0.1 <= idle_resume_jerk <= 0.5: natural_patterns += 1
            if 0.05 <= thermal_hover_noise <= 0.3: natural_patterns += 1
            if 0.1 <= path_entropy <= 2.0: natural_patterns += 1
            if cursor_micro_jitter >= 0.05: natural_patterns += 1
            
            if natural_patterns >= 2:
                human_score += 0.04
                human_indicators.append("natural_evasion_patterns")

        # 14. Canvas Metrics (optional, e.g. check for missing or default values)
        if canvas_metrics:
            # Example: check for default/empty canvas metrics (bots may not render properly)
            if canvas_metrics.get("width", 0) == 0 or canvas_metrics.get("height", 0) == 0:
                bot_score += 0.07
                bot_indicators.append("empty_canvas_metrics")
            else:
                human_score += 0.03
                human_indicators.append("canvas_metrics_present")

        # 15. Unusual Screen Resolution
        if unsualscreenresolution:
            # Example: check for very small/large or common bot resolutions
            width = unsualscreenresolution.get("width", 0)
            height = unsualscreenresolution.get("height", 0)
            if width < 400 or height < 300 or width > 8000 or height > 4000:
                bot_score += 0.09
                bot_indicators.append("unusual_screen_resolution")
            elif width and height:
                human_score += 0.02
                human_indicators.append("normal_screen_resolution")


        #----------------NO cursor movement---------------------
        # Detect zero cursor movement scenarios for keyboard-only users - HUMAN DETECTION ONLY
        
        is_no_cursor = cursor_movement_count == 0
        
        if is_no_cursor:
            logger.info("=== ULTRA-GENEROUS ZERO CURSOR MOVEMENT HUMAN DETECTION ===")
            
            # ULTRA-GENEROUS human evidence scoring system
            primary_evidence = 0    
            supporting_evidence = 0 
            interaction_quality = 0 
            
            
            if key_press_times and len(key_press_times) >= 1:  # Even single keypress counts
                if len(key_press_times) >= 2:
                    typing_intervals = [key_press_times[i] - key_press_times[i-1] for i in range(1, len(key_press_times))]
                    interval_std = np.std(typing_intervals)
                    interval_variance = np.var(typing_intervals)
                    avg_typing = np.mean(typing_intervals)
                    
                    # TIER 1: Reasonable typing gets moderate evidence
                    if avg_typing >= 8:  # Reasonable typing speed
                        primary_evidence += 3  # Reduced evidence
                        human_score += 0.15  # Much lower reward
                        has_human_behavior = True
                        human_indicators.append("excellent_typing_zero_cursor")
                        interaction_quality += 2  # Moderate quality score
                        logger.info(f"EXCELLENT TYPING: avg={avg_typing:.1f}ms, std={interval_std:.1f}")
                        
                        # Bonus for variance
                        if interval_variance > 1:
                            primary_evidence += 1
                            human_score += 0.08
                            human_indicators.append("typing_variance_zero_cursor")
                    
                    # TIER 2: Fast typing gets reduced evidence
                    elif avg_typing >= 3:
                        primary_evidence += 2
                        human_score += 0.12
                        has_human_behavior = True
                        human_indicators.append("natural_typing_zero_cursor")
                        interaction_quality += 1
                        logger.info(f"NATURAL TYPING: avg={avg_typing:.1f}ms")
                    
                    # TIER 3: Very fast typing is suspicious
                    else:
                        primary_evidence += 1
                        human_score += 0.08
                        has_human_behavior = True
                        human_indicators.append("basic_typing_zero_cursor")
                        interaction_quality += 1
                        logger.info(f"BASIC TYPING DETECTED: avg={avg_typing:.1f}ms")
                
                else:  # Single keypress - moderate human evidence
                    primary_evidence += 2
                    human_score += 0.12
                    has_human_behavior = True
                    human_indicators.append("single_keypress_zero_cursor")
                    interaction_quality += 1
                    logger.info("SINGLE KEYPRESS - Moderate human evidence")
                
                # Reduced bonus for typing pattern
                if len(key_press_times) >= 2:
                    typing_consistency = len(set([round(t/50)*50 for t in typing_intervals])) / len(typing_intervals)
                    # Moderate consistency bonus
                    supporting_evidence += 1
                    human_score += 0.08
                    human_indicators.append("typing_pattern_zero_cursor")
            
            # 2. Balanced key hold analysis - reasonable key hold evidence
            if key_hold_times and len(key_hold_times) >= 1:
                avg_hold = np.mean(key_hold_times)
                std_hold = np.std(key_hold_times) if len(key_hold_times) > 1 else 0
                
                # Reasonable key hold gets moderate evidence
                if avg_hold >= 5:  # Reasonable hold time
                    primary_evidence += 2  # Reduced evidence
                    human_score += 0.12  # Lower reward
                    has_human_behavior = True
                    human_indicators.append("excellent_key_holds_zero_cursor")
                    interaction_quality += 1  # Moderate quality
                    logger.info(f"KEY HOLD DETECTED: avg={avg_hold:.1f}ms, std={std_hold:.1f}")
                    
                    # Moderate bonus for variance
                    if std_hold > 1:
                        primary_evidence += 1
                        human_score += 0.06
                        human_indicators.append("key_hold_variance_zero_cursor")
                
                elif avg_hold >= 1:  # Even very short holds get reduced evidence
                    primary_evidence += 1  # Much reduced evidence
                    human_score += 0.08  # Much lower reward
                    has_human_behavior = True
                    human_indicators.append("natural_key_holds_zero_cursor")
                    interaction_quality += 1  # Reduced quality
                    logger.info(f"SHORT KEY HOLD: avg={avg_hold:.1f}ms")
                
                else:  # Minimal key hold activity 
                    primary_evidence += 1  # Minimal evidence
                    human_score += 0.05  # Very low reward
                    has_human_behavior = True
                    human_indicators.append("minimal_key_holds_zero_cursor")
                    logger.info("MINIMAL KEY HOLD ACTIVITY")
                
                logger.info(f"KEY HOLD ANALYSIS: avg={avg_hold:.1f}ms, std={std_hold:.1f}")
            
            # 3. Reduced human activity indicators - balanced scoring
            if scroll_speeds and len(scroll_speeds) > 0:
                scroll_variance = np.var(scroll_speeds) if len(scroll_speeds) > 1 else 0
                if scroll_variance > 100:
                    primary_evidence += 2  # Reduced evidence
                    human_score += 0.12  # Much lower reward
                    interaction_quality += 1  # Reduced quality
                    human_indicators.append("varied_scroll_zero_cursor")
                elif scroll_variance > 20:
                    primary_evidence += 1
                    human_score += 0.08
                    human_indicators.append("moderate_scroll_zero_cursor")
                else:
                    supporting_evidence += 1
                    human_score += 0.05
                    human_indicators.append("basic_scroll_zero_cursor")
                has_human_behavior = True
                logger.info(f"SCROLL ACTIVITY: speeds={len(scroll_speeds)}, variance={scroll_variance:.1f}")
            
            if behavior.get("pasteDetected", False):
                primary_evidence += 2  # Reduced evidence
                human_score += 0.10  # Much lower reward
                has_human_behavior = True
                interaction_quality += 1  # Reduced quality
                human_indicators.append("paste_activity_zero_cursor")
                logger.info("PASTE ACTIVITY")
            
            if tabKeyCount >= 1:
                tab_score = min(tabKeyCount, 3)  # Lower cap for scoring
                primary_evidence += 1 + tab_score
                human_score += 0.08 + (tab_score * 0.02)  # Much lower reward
                has_human_behavior = True
                interaction_quality += 1
                human_indicators.append("tab_navigation_zero_cursor")
                logger.info(f"TAB NAVIGATION: {tabKeyCount} presses")
            
            # 4. Reduced micro-behavior analysis
            if hesitation and isinstance(hesitation, list) and sum(hesitation) > 0:
                avg_hesitation = np.mean(hesitation)
                hesitation_count = len([h for h in hesitation if h > 0])
                
                if 100 <= avg_hesitation <= 3000 and hesitation_count >= 2:
                    primary_evidence += 1  # Reduced evidence
                    human_score += 0.08  # Much lower reward
                    human_indicators.append("excellent_hesitation_zero_cursor")
                elif 50 <= avg_hesitation <= 5000:
                    supporting_evidence += 1
                    human_score += 0.05
                    human_indicators.append("natural_hesitation_zero_cursor")
                else:
                    supporting_evidence += 1
                    human_score += 0.03
                    human_indicators.append("basic_hesitation_zero_cursor")
                has_human_behavior = True
                logger.info(f"HESITATION ANALYSIS: avg={avg_hesitation:.1f}ms, count={hesitation_count}")
            
            if micropause and isinstance(micropause, list) and sum(micropause) > 0:
                micropause_count = len([m for m in micropause if m > 0])
                avg_micropause = np.mean([m for m in micropause if m > 0]) if micropause_count > 0 else 0
                
                if micropause_count >= 3 and 20 <= avg_micropause <= 800:
                    supporting_evidence += 1  # Reduced evidence
                    human_score += 0.06  # Much lower reward
                    human_indicators.append("excellent_micropause_zero_cursor")
                elif micropause_count >= 1:
                    supporting_evidence += 1
                    human_score += 0.04
                    human_indicators.append("natural_micropause_zero_cursor")
                has_human_behavior = True
                logger.info(f"MICROPAUSE ANALYSIS: count={micropause_count}, avg={avg_micropause:.1f}ms")
            
            # 5. Reduced timing and interaction context
            timing_score = 0
            if 500 <= total_time <= 300000:  # 0.5 to 5 minutes - optimal range
                timing_score = 1  # Reduced score
                human_score += 0.08  # Much lower reward
                human_indicators.append("optimal_timing_zero_cursor")
            elif 200 <= total_time <= 600000:  # Extended acceptable range
                timing_score = 1
                human_score += 0.06
                human_indicators.append("reasonable_timing_zero_cursor")
            elif total_time > 0:  # Any time is better than none
                timing_score = 1
                human_score += 0.04
                human_indicators.append("minimal_timing_zero_cursor")
            
            supporting_evidence += timing_score
            has_human_behavior = True
            logger.info(f"TIMING ANALYSIS: {total_time}ms, score={timing_score}")
            
            # 6. Reduced additional interaction signals
            if mouseJitter and isinstance(mouseJitter, list) and sum(mouseJitter) > 0:
                jitter_count = len([j for j in mouseJitter if j > 0])
                if jitter_count >= 2:
                    supporting_evidence += 1  # Reduced evidence
                    human_score += 0.06  # Much lower reward
                    human_indicators.append("mouse_jitter_zero_cursor")
                elif jitter_count >= 1:
                    supporting_evidence += 1
                    human_score += 0.04
                    human_indicators.append("minimal_jitter_zero_cursor")
                has_human_behavior = True
            
            if click_timestamps and len(click_timestamps) > 0:
                click_count = len(click_timestamps)
                if click_count >= 3:
                    primary_evidence += 2  # Reduced evidence
                    human_score += 0.10  # Much lower reward
                    interaction_quality += 1  # Reduced quality
                    human_indicators.append("multiple_clicks_zero_cursor")
                elif click_count >= 1:
                    primary_evidence += 1
                    human_score += 0.08
                    human_indicators.append("click_activity_zero_cursor")
                has_human_behavior = True
                logger.info(f"CLICK ANALYSIS: {click_count} clicks")
            
            # 7. Reduced contextual behavior indicators
            if behavior.get("keyboardPatterns", []) and len(behavior.get("keyboardPatterns", [])) >= 2:
                supporting_evidence += 1  # Reduced evidence
                human_score += 0.04  # Much lower reward
                human_indicators.append("keyboard_patterns_zero_cursor")
            
            if behavior.get("scrollChanges", 0) > 0:
                supporting_evidence += 1
                human_score += 0.04
                human_indicators.append("scroll_changes_zero_cursor")
            
            # Strict progressive scoring - much higher thresholds required
            total_evidence = primary_evidence + supporting_evidence
            
            if primary_evidence >= 6 and interaction_quality >= 3:  # Much higher thresholds
                human_score += 0.12  # Much lower bonuses
                human_indicators.append("strong_zero_cursor_human")
                logger.info(f"STRONG ZERO CURSOR HUMAN: primary={primary_evidence}, quality={interaction_quality}")
            elif primary_evidence >= 4 and total_evidence >= 8:  # Higher thresholds
                human_score += 0.10
                human_indicators.append("verified_zero_cursor_human") 
                logger.info(f"VERIFIED ZERO CURSOR HUMAN: primary={primary_evidence}, total={total_evidence}")
            elif primary_evidence >= 3 and total_evidence >= 6:  # Higher thresholds
                human_score += 0.08
                human_indicators.append("probable_zero_cursor_human")
                logger.info(f"PROBABLE ZERO CURSOR HUMAN: primary={primary_evidence}, total={total_evidence}")
            elif primary_evidence >= 2 and total_evidence >= 4:  # Higher thresholds
                human_score += 0.06
                has_human_behavior = True
                human_indicators.append("basic_zero_cursor_human")
                logger.info(f"BASIC ZERO CURSOR HUMAN: primary={primary_evidence}, total={total_evidence}")
            elif primary_evidence >= 1 and total_evidence >= 2:  # Higher thresholds
                human_score += 0.04
                has_human_behavior = True
                human_indicators.append("minimal_zero_cursor_human")
                logger.info(f"MINIMAL ZERO CURSOR HUMAN: primary={primary_evidence}, total={total_evidence}")
            else:
                # No bonus for insufficient evidence
                logger.info(f"INSUFFICIENT ZERO CURSOR EVIDENCE: primary={primary_evidence}, total={total_evidence}")
            
            logger.info(f"ZERO CURSOR FINAL ANALYSIS: primary={primary_evidence}, supporting={supporting_evidence}, quality={interaction_quality}, total_boost={human_score:.3f}")
        #-------------------------------------------------------
        #------------------Low cursor movements-----------------
        # Detect low cursor movement scenarios (1-5 movements) - HUMAN DETECTION ONLY
        is_low_cursor = 1 <= cursor_movement_count <= 5
        
        if is_low_cursor:
            logger.info(f"=== ULTRA-GENEROUS LOW CURSOR MOVEMENT HUMAN DETECTION: {cursor_movement_count} movements ===")
            
            # ULTRA-GENEROUS evidence scoring for low cursor scenarios
            movement_evidence = 0      
            interaction_evidence = 0   
            behavioral_evidence = 0    
            efficiency_bonus = 0       
            
            # 1. ULTRA-GENEROUS movement quality analysis - ANY movement is human
            if cursor_movements and len(cursor_movements) >= 1:
                movement_distances = []
                meaningful_movements = 0
                movement_timing_intervals = []
                cursor_path_length = 0
                
                for i in range(1, len(cursor_movements)):
                    if 'x' in cursor_movements[i] and 'y' in cursor_movements[i]:
                        prev_x = cursor_movements[i-1].get('x', 0)
                        prev_y = cursor_movements[i-1].get('y', 0)
                        curr_x = cursor_movements[i].get('x', 0)
                        curr_y = cursor_movements[i].get('y', 0)
                        
                        distance = math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
                        movement_distances.append(distance)
                        cursor_path_length += distance
                        
                        if distance >= 1:  # ANY movement is meaningful
                            meaningful_movements += 1
                        
                        # ANY movement timing is natural
                        if 'timestamp' in cursor_movements[i] and 'timestamp' in cursor_movements[i-1]:
                            time_diff = cursor_movements[i]['timestamp'] - cursor_movements[i-1]['timestamp']
                            if time_diff > 0:  # Any timing is reasonable
                                movement_timing_intervals.append(time_diff)
                
                if movement_distances:
                    avg_distance = np.mean(movement_distances)
                    max_distance = max(movement_distances)
                    movement_variance = np.var(movement_distances) if len(movement_distances) > 1 else 0
                    
                    # ULTRA-GENEROUS movement quality assessment
                    if meaningful_movements >= 1:  # ANY meaningful movement gets max evidence
                        movement_evidence += 8  # Increased evidence
                        human_score += 0.50  # Much higher reward
                        efficiency_bonus += 3  # Higher bonus
                        has_human_behavior = True
                        human_indicators.append("excellent_movements_low_cursor")
                        logger.info(f"EXCELLENT MOVEMENTS: count={meaningful_movements}, avg={avg_distance:.1f}px")
                        
                        # Extra bonus for ANY variance
                        if movement_variance > 0.1:
                            movement_evidence += 2
                            human_score += 0.20
                            human_indicators.append("movement_variance_low_cursor")
                    
                    else:  # Even minimal movement gets strong evidence
                        movement_evidence += 6
                        human_score += 0.45
                        efficiency_bonus += 2
                        has_human_behavior = True
                        human_indicators.append("minimal_movements_low_cursor")
                        logger.info(f"MINIMAL MOVEMENTS: avg={avg_distance:.1f}px")
                
                # Movement timing analysis - ANY timing is natural
                if len(movement_timing_intervals) >= 1:  # Even single timing interval
                    timing_variance = np.var(movement_timing_intervals) if len(movement_timing_intervals) > 1 else 0
                    timing_std = np.std(movement_timing_intervals) if len(movement_timing_intervals) > 1 else 0
                    
                    # ANY timing gets strong evidence
                    behavioral_evidence += 4  # Increased evidence
                    human_score += 0.30  # Higher reward
                    has_human_behavior = True
                    human_indicators.append("natural_movement_timing_low_cursor")
                    logger.info(f"NATURAL TIMING: intervals={len(movement_timing_intervals)}")
                    
                    # Extra bonus for ANY variance
                    if timing_variance > 1:
                        behavioral_evidence += 2
                        human_score += 0.15
                        human_indicators.append("timing_variance_low_cursor")
                        logger.info(f"NATURAL MOVEMENT TIMING: var={timing_variance:.1f}, std={timing_std:.1f}")
                    elif timing_variance >= 1000:
                        behavioral_evidence += 2
                        human_score += 0.15
                        human_indicators.append("varied_timing_low_cursor")
                
                has_human_behavior = True
            
            # 2. Enhanced keyboard interaction analysis
            if key_press_times and len(key_press_times) >= 1:
                key_count = len(key_press_times)
                
                if key_count >= 5:
                    interaction_evidence += 2  # Reduced evidence
                    human_score += 0.10  # Much lower reward
                    efficiency_bonus += 1  # Reduced bonus
                    human_indicators.append("extensive_keyboard_low_cursor")
                elif key_count >= 3:
                    interaction_evidence += 2
                    human_score += 0.08
                    human_indicators.append("moderate_keyboard_low_cursor")
                elif key_count >= 1:
                    interaction_evidence += 1
                    human_score += 0.06
                    human_indicators.append("basic_keyboard_low_cursor")
                
                has_human_behavior = True
                logger.info(f"KEYBOARD INTERACTION: {key_count} key presses")
                
                # Enhanced typing pattern analysis
                if len(key_press_times) >= 3:
                    typing_intervals = [key_press_times[i] - key_press_times[i-1] 
                                      for i in range(1, len(key_press_times))]
                    
                    if typing_intervals:
                        typing_variance = np.var(typing_intervals)
                        typing_std = np.std(typing_intervals)
                        avg_typing = np.mean(typing_intervals)
                        
                        # Reduced levels of typing quality
                        if 100 <= typing_variance <= 400000 and typing_std >= 20 and 50 <= avg_typing <= 800:
                            interaction_evidence += 1  # Much reduced evidence
                            human_score += 0.08  # Much lower reward
                            human_indicators.append("excellent_typing_low_cursor")
                            logger.info(f"EXCELLENT TYPING: var={typing_variance:.1f}, std={typing_std:.1f}, avg={avg_typing:.1f}")
                        elif typing_variance >= 50 and typing_std >= 15:
                            interaction_evidence += 1
                            human_score += 0.06
                            human_indicators.append("natural_typing_low_cursor")
                            logger.info(f"NATURAL TYPING: var={typing_variance:.1f}, std={typing_std:.1f}")
                        elif typing_variance >= 20:
                            interaction_evidence += 1
                            human_score += 0.04
                            human_indicators.append("basic_typing_low_cursor")
                        else:
                            # Minimal typing variance gets minimal credit
                            human_score += 0.02
                            human_indicators.append("minimal_typing_low_cursor")
            
            # 3. Enhanced click interaction analysis
            if click_timestamps and len(click_timestamps) >= 1:
                click_count = len(click_timestamps)
                
                if click_count >= 4:
                    interaction_evidence += 5
                    human_score += 0.30
                    efficiency_bonus += 2
                    human_indicators.append("multiple_clicks_low_cursor")
                elif click_count >= 2:
                    interaction_evidence += 4
                    human_score += 0.25
                    efficiency_bonus += 1
                    human_indicators.append("dual_clicks_low_cursor")
                else:
                    interaction_evidence += 3
                    human_score += 0.20
                    human_indicators.append("single_click_low_cursor")
                
                has_human_behavior = True
                logger.info(f"CLICK INTERACTION: {click_count} clicks")
                
                # Click-to-movement efficiency analysis
                if cursor_movement_count > 0:
                    click_efficiency = click_count / cursor_movement_count
                    if 0.5 <= click_efficiency <= 10.0:  # Good click-to-movement ratio
                        efficiency_bonus += 2
                        human_score += 0.15
                        human_indicators.append("efficient_clicking_low_cursor")
                        logger.info(f"EFFICIENT CLICKING: ratio={click_efficiency:.2f}")
            
            # 4. Enhanced behavioral evidence analysis
            if scroll_speeds and len(scroll_speeds) > 0:
                scroll_count = len(scroll_speeds)
                scroll_variance = np.var(scroll_speeds) if len(scroll_speeds) > 1 else 0
                
                if scroll_count >= 3 and scroll_variance > 150:
                    behavioral_evidence += 6
                    human_score += 0.35
                    efficiency_bonus += 3
                    human_indicators.append("excellent_scroll_low_cursor")
                elif scroll_count >= 2 and scroll_variance > 50:
                    behavioral_evidence += 5
                    human_score += 0.30
                    efficiency_bonus += 2
                    human_indicators.append("varied_scroll_low_cursor")
                elif scroll_count >= 1:
                    behavioral_evidence += 4
                    human_score += 0.25
                    efficiency_bonus += 1
                    human_indicators.append("basic_scroll_low_cursor")
                
                has_human_behavior = True
                logger.info(f"SCROLL BEHAVIOR: count={scroll_count}, variance={scroll_variance:.1f}")
            
            if hesitation and isinstance(hesitation, list) and sum(hesitation) > 0:
                hesitation_count = len([h for h in hesitation if h > 0])
                avg_hesitation = np.mean([h for h in hesitation if h > 0]) if hesitation_count > 0 else 0
                
                if hesitation_count >= 3 and 80 <= avg_hesitation <= 2500:
                    behavioral_evidence += 4
                    human_score += 0.25
                    human_indicators.append("excellent_hesitation_low_cursor")
                elif hesitation_count >= 1 and 50 <= avg_hesitation <= 5000:
                    behavioral_evidence += 3
                    human_score += 0.20
                    human_indicators.append("natural_hesitation_low_cursor")
                else:
                    behavioral_evidence += 2
                    human_score += 0.15
                    human_indicators.append("basic_hesitation_low_cursor")
                
                has_human_behavior = True
                logger.info(f"HESITATION: count={hesitation_count}, avg={avg_hesitation:.1f}ms")
            
            if micropause and isinstance(micropause, list) and sum(micropause) > 0:
                micropause_count = len([m for m in micropause if m > 0])
                
                if micropause_count >= 3:
                    behavioral_evidence += 3
                    human_score += 0.20
                    human_indicators.append("multiple_micropause_low_cursor")
                elif micropause_count >= 1:
                    behavioral_evidence += 2
                    human_score += 0.15
                    human_indicators.append("basic_micropause_low_cursor")
                
                has_human_behavior = True
                logger.info(f"MICROPAUSE: count={micropause_count}")
            
            # 5. Enhanced timing and context analysis
            timing_quality = 0
            if 300 <= total_time <= 180000:  # 0.3 to 3 minutes - optimal for focused interaction
                timing_quality = 4
                human_score += 0.25
                efficiency_bonus += 2
                human_indicators.append("optimal_timing_low_cursor")
            elif 200 <= total_time <= 600000:  # Extended reasonable range
                timing_quality = 3
                human_score += 0.20
                efficiency_bonus += 1
                human_indicators.append("reasonable_timing_low_cursor")
            elif total_time >= 100:  # Any meaningful time
                timing_quality = 2
                human_score += 0.15
                human_indicators.append("minimal_timing_low_cursor")
            
            behavioral_evidence += timing_quality
            has_human_behavior = True
            logger.info(f"TIMING ANALYSIS: {total_time}ms, quality={timing_quality}")
            
            # 6. Activity diversity and efficiency analysis
            activity_types = 0
            activity_quality = 0
            
            if len(cursor_movements) > 0: 
                activity_types += 1
                activity_quality += min(cursor_movement_count, 3)
            if key_press_times and len(key_press_times) > 0: 
                activity_types += 1
                activity_quality += min(len(key_press_times), 5)
            if click_timestamps and len(click_timestamps) > 0: 
                activity_types += 1
                activity_quality += min(len(click_timestamps), 4)
            if scroll_speeds and len(scroll_speeds) > 0: 
                activity_types += 1
                activity_quality += min(len(scroll_speeds), 4)
            
            if activity_types >= 4:  # All interaction types present
                behavioral_evidence += 5
                human_score += 0.30
                efficiency_bonus += 3
                human_indicators.append("comprehensive_activity_low_cursor")
                logger.info("COMPREHENSIVE ACTIVITY - EXCELLENT HUMAN SIGNAL")
            elif activity_types >= 3:
                behavioral_evidence += 4
                human_score += 0.25
                efficiency_bonus += 2
                human_indicators.append("diverse_activity_low_cursor")
                logger.info("DIVERSE ACTIVITY DETECTED")
            elif activity_types >= 2:
                behavioral_evidence += 3
                human_score += 0.20
                efficiency_bonus += 1
                human_indicators.append("dual_activity_low_cursor")
                logger.info("DUAL ACTIVITY DETECTED")
            
            # 7. Additional human signal analysis
            additional_signals = 0
            
            if mouseJitter and isinstance(mouseJitter, list) and sum(mouseJitter) > 0:
                jitter_count = len([j for j in mouseJitter if j > 0])
                additional_signals += min(jitter_count, 3)
                behavioral_evidence += 2
                human_score += 0.15
                human_indicators.append("mouse_jitter_low_cursor")
            
            if tabKeyCount >= 1:
                tab_bonus = min(tabKeyCount, 4)
                additional_signals += tab_bonus
                behavioral_evidence += 2 + tab_bonus
                human_score += 0.15 + (tab_bonus * 0.05)
                human_indicators.append("tab_navigation_low_cursor")
                logger.info(f"TAB NAVIGATION: {tabKeyCount} presses")
            
            if behavior.get("pasteDetected", False):
                additional_signals += 3
                behavioral_evidence += 4
                human_score += 0.25
                efficiency_bonus += 2
                human_indicators.append("paste_activity_low_cursor")
                logger.info("PASTE ACTIVITY - EFFICIENCY INDICATOR")
            
            # 8. Enhanced progressive scoring with efficiency consideration
            total_evidence = movement_evidence + interaction_evidence + behavioral_evidence
            final_efficiency_score = efficiency_bonus * 0.05  # Convert bonus to score
            
            if total_evidence >= 15 and efficiency_bonus >= 6:
                human_score += 0.35 + final_efficiency_score
                human_indicators.append("exceptional_efficient_low_cursor_human")
                logger.info(f"EXCEPTIONAL EFFICIENT USER: total={total_evidence}, efficiency={efficiency_bonus}")
            elif total_evidence >= 12 and efficiency_bonus >= 4:
                human_score += 0.30 + final_efficiency_score
                human_indicators.append("excellent_low_cursor_human")
                logger.info(f"EXCELLENT LOW CURSOR USER: total={total_evidence}, efficiency={efficiency_bonus}")
            elif total_evidence >= 9 and efficiency_bonus >= 2:
                human_score += 0.25 + final_efficiency_score
                human_indicators.append("strong_low_cursor_human")
                logger.info(f"STRONG LOW CURSOR USER: total={total_evidence}, efficiency={efficiency_bonus}")
            elif total_evidence >= 6:
                human_score += 0.20 + final_efficiency_score
                human_indicators.append("verified_low_cursor_human")
                logger.info(f"VERIFIED LOW CURSOR USER: total={total_evidence}")
            elif total_evidence >= 4:
                human_score += 0.15 + final_efficiency_score
                human_indicators.append("probable_low_cursor_human")
                logger.info(f"PROBABLE LOW CURSOR USER: total={total_evidence}")
            elif total_evidence >= 2:
                human_score += 0.12 + final_efficiency_score
                has_human_behavior = True
                human_indicators.append("basic_low_cursor_human")
                logger.info(f"BASIC LOW CURSOR USER: total={total_evidence}")
            elif total_evidence >= 1:
                human_score += 0.08 + final_efficiency_score
                has_human_behavior = True
                human_indicators.append("minimal_low_cursor_human")
                logger.info(f"MINIMAL LOW CURSOR USER: total={total_evidence}")
            
            logger.info(f"LOW CURSOR FINAL ANALYSIS: movement={movement_evidence}, interaction={interaction_evidence}, behavior={behavioral_evidence}, efficiency={efficiency_bonus}, total_boost={human_score:.3f}")
        
        #--------------------------------------------------------

        

        

        # --- Require more bot indicators for bot classification ---
        # --- BALANCED BOT DETECTION RULES ---
        critical_bot_indicators = set([
            "impossible_entropy", "no_mouse_jitter", "perfect_click_intervals", "no_micro_pauses", "no_hesitation"
        ])
        n_critical_bot = len([b for b in bot_indicators if b in critical_bot_indicators])
        multiple_bot_signals = len(bot_indicators) >= 7 and n_critical_bot >= 1
        
        # BALANCED hard rule bot detection - reasonable but not too lenient
        hard_rule_bot = (
            bot_fingerprint_score >= 0.85 or  # Balanced threshold
            is_automated_browser or
            n_critical_bot >= 2 or  # Reasonable critical indicators required
            bot_score >= 0.50  # Balanced bot score required
        )
        
        # Advanced bot detection - balanced thresholds
        if cursor_entropy is not None and cursor_entropy < 0.005:  # Reasonable threshold
            hard_rule_bot = True
            bot_indicators.append("impossible_entropy")
        if (not mouseJitter or (isinstance(mouseJitter, list) and sum(mouseJitter) == 0)) and (cursor_movements and len(cursor_movements) > 40):  # Balanced threshold
            hard_rule_bot = True
            bot_indicators.append("no_mouse_jitter")
        if click_timestamps and len(click_timestamps) >= 25:  # Balanced click threshold
            click_intervals_check = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
            if len(set(click_intervals_check)) == 1:
                hard_rule_bot = True
                bot_indicators.append("perfect_click_intervals")

        # --- BALANCED FINAL DECISION LOGIC ---
        strong_bot_indicators = set([
            "webdriver_flagged", "missing_canvas_fingerprint", "languages_spoofed", "plugins_spoofed",
            "impossible_timing_precision", "superhuman_typing_speed", "definitive_bot_evidence",
            "no_human_behaviors_high_bot_fingerprint", "perfect_click_timing", "suspicious_gpu_vendor",
            "chrome_runtime_modified", "empty_canvas_metrics", "unusual_screen_resolution"
        ])
        n_strong_bot = len([b for b in bot_indicators if b in strong_bot_indicators])
        n_human = len(human_indicators)
        n_bot = len(bot_indicators)
        
        # Calculate balanced indicators
        zero_low_cursor_human_indicators = [h for h in human_indicators if 'zero_cursor' in h or 'low_cursor' in h]
        has_zero_low_cursor_evidence = len(zero_low_cursor_human_indicators) > 0
        strong_human_evidence = human_score >= 0.25 and n_human >= 2  # Reasonable human evidence threshold
        
        logger.info(f"=== FINAL DECISION ANALYSIS ===")
        logger.info(f"Human Score: {human_score:.3f}, Bot Score: {bot_score:.3f}")
        logger.info(f"Human Indicators ({n_human}): {human_indicators}")
        logger.info(f"Bot Indicators ({n_bot}): {bot_indicators}")
        logger.info(f"Zero/Low Cursor Evidence: {has_zero_low_cursor_evidence} ({len(zero_low_cursor_human_indicators)} indicators)")
        logger.info(f"Has Human Behavior: {has_human_behavior}")
        logger.info(f"Strong Bot Count: {n_strong_bot}, Critical Bot Count: {n_critical_bot}")

        # BALANCED DECISION LOGIC - accurate detection of both humans and bots
        definitive_automation = (
            is_automated_browser or
            ("webdriver_flagged" in bot_indicators) or
            (bot_fingerprint_score > 0.90 and n_strong_bot >= 2)  # Balanced threshold with reasonable indicators
        )

        # Override hard rule for legitimate zero/low cursor users with reasonable evidence
        if (is_no_cursor or is_low_cursor) and (human_score > bot_score or has_human_behavior):
            if not definitive_automation:
                hard_rule_bot = False  # Override for legitimate users
                logger.info(f"HARD RULE OVERRIDE: Zero/Low cursor user with human evidence")

        # BALANCED DECISION LOGIC - Accurate detection without being too lenient or too strict
        if definitive_automation:
            is_human = False
            retry_required = False
            logger.info("DECISION: DEFINITIVE automation detected - Classified as Bot.")
        
        # Clear bot detection with reasonable evidence
        elif hard_rule_bot and n_strong_bot >= 2:
            is_human = False
            retry_required = False
            logger.info(f"DECISION: Strong automation patterns detected - Classified as Bot.")

        # Bot detection for high fingerprint scores
        elif bot_fingerprint_score > 0.80 and n_strong_bot >= 1:
            is_human = False
            retry_required = False
            logger.info(f"DECISION: High bot fingerprint score (score={bot_fingerprint_score:.2f}) - Classified as Bot.")

        # Bot detection for multiple strong indicators
        elif n_strong_bot >= 3:
            is_human = False
            retry_required = False
            logger.info(f"DECISION: Multiple strong bot indicators - Classified as Bot.")

        # Bot detection for clear bot advantage
        elif bot_score > human_score * 1.5 and bot_score >= 0.30:
            is_human = False
            retry_required = False
            logger.info(f"DECISION: Clear bot score advantage - Classified as Bot.")

        # Special handling for zero/low cursor users - balanced approach
        elif (is_no_cursor or is_low_cursor):
            # Require meaningful human evidence for zero/low cursor users
            if has_human_behavior and human_score > 0.15 and n_human >= 2:
                is_human = True
                retry_required = False
                logger.info(f"DECISION: Zero/Low cursor user with meaningful human evidence - Classified as Human.")
            elif human_score > bot_score and n_strong_bot == 0:
                is_human = True
                retry_required = False
                logger.info(f"DECISION: Zero/Low cursor user with human advantage - Classified as Human.")
            elif bot_score > 0.25 or n_strong_bot >= 1:
                is_human = False
                retry_required = False
                logger.info(f"DECISION: Zero/Low cursor user with bot evidence - Classified as Bot.")
            else:
                # Default to human for ambiguous zero/low cursor cases
                is_human = True
                retry_required = False
                logger.info(f"DECISION: Zero/Low cursor user - default to Human.")

        # Human detection with good evidence
        elif has_human_behavior and human_score > bot_score and n_strong_bot == 0:
            is_human = True
            retry_required = False
            logger.info(f"DECISION: Strong human behavior without automation signals - Classified as Human.")

        # Human detection with clear advantage
        elif human_score > bot_score * 1.3 and has_human_behavior:
            is_human = True
            retry_required = False
            logger.info(f"DECISION: Clear human score advantage with behavior - Classified as Human.")

        # Human detection with multiple indicators
        elif n_human >= 3 and bot_score < 0.40:
            is_human = True
            retry_required = False
            logger.info(f"DECISION: Multiple human indicators with reasonable bot score - Classified as Human.")

        # Bot detection for significant bot evidence
        elif bot_score > human_score and bot_score >= 0.25 and n_human < 2:
            is_human = False
            retry_required = False
            logger.info(f"DECISION: Bot score advantage with limited human evidence - Classified as Bot.")

        # Human wins in close calls if they have some evidence
        elif human_score >= bot_score and (has_human_behavior or n_human >= 1):
            is_human = True
            retry_required = False
            logger.info(f"DECISION: Human score with evidence in close call - Classified as Human.")
        
        # Bot wins if they have clear advantage
        elif bot_score > human_score * 1.2:
            is_human = False
            retry_required = False
            logger.info(f"DECISION: Bot score advantage - Classified as Bot.")
        
        # Default based on evidence quality
        elif has_human_behavior or human_score > 0.10:
            is_human = True
            retry_required = False
            logger.info(f"DECISION: Some human evidence present - Classified as Human.")
        
        else:
            is_human = False
            retry_required = False
            logger.info(f"DECISION: No clear human evidence - Classified as Bot.")

        # Log final decision
        logger.info(f"Final decision - Human: {is_human}, Score - Human: {human_score}, Bot: {bot_score}, Indicators: H={human_indicators}, B={bot_indicators}, BotFingerprint={bot_fingerprint_score}")
        logger.info(f"DEBUG: All indicators: Human={human_indicators}, Bot={bot_indicators}, Scores: H={human_score}, B={bot_score}")
        
        # Log final decision
        logger.info(f"Final decision - Human: {is_human}, Score - Human: {human_score}, Bot: {bot_score}")
        
        # Return retry message if required
        if retry_required:
            return JsonResponse({
                "status": "retry",
                "message": "We couldn't confidently verify you as human. Please try again.",
                "classification": "Retry",
                "score": round(human_score * 100),
                "metrics": {
                    "human_score": round(human_score * 100),
                    "bot_score": round(bot_score * 100),
                    "human_indicators": human_indicators,
                    "bot_indicators": bot_indicators,
                    "has_human_behavior": has_human_behavior
                },
                "behavior_data": {
                    "usai_id": data.get("usai_id", "unknown"),
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }, status=200)
        
        behavior_data = UserBehavior_v3(
            usai_id=data.get("usai_id", "unknown"),
            cursor_movements=behavior.get("cursorMovements", []),
            key_press_times=behavior.get("keyPressTimes", []),
            key_hold_times=behavior.get("keyHoldTimes", []),
            click_timestamps=behavior.get("clickTimestamps", []),
            click_intervals=click_intervals,  # Add the calculated click intervals
            cursor_speeds=behavior.get("cursorSpeeds", []),
            cursor_acceleration=behavior.get("cursorAcceleration", []),
            cursor_curvature=behavior.get("cursorCurvature", []),
            paste_detected=behavior.get("pasteDetected", False),
            total_time=behavior.get("totalTimeToSubmit", 0),
            classification="Human" if is_human else "Bot",
            human_score=human_score,
            bot_score=bot_score,
            human_indicators=human_indicators,
            bot_indicators=bot_indicators,
            bot_fingerprint_score=bot_fingerprint_score,
            suspicious_feature_ratio=suspicious_feature_ratio,
            suspicious_flag=suspicious_flag,
            mouse_movement_debug=mouse_movement_debug,
            speed_calculation_debug=speed_calculation_debug,
            post_paste_activity=post_paste_activity,
            keyboard_patterns=behavior.get("keyboardPatterns", []),
            suspicious_patterns=behavior.get("suspiciousPatterns", []),
            action_count=behavior.get("actionCount", 0),
            is_automated_browser=is_automated_browser,
            cursor_entropy=behavior.get("cursorEntropy", 0),
            scroll_speeds=scroll_speeds,
            scroll_changes=scroll_changes,
            idle_time=idle_time,
            honeypot_value=honeypot_value,
            tabkeycount=tabKeyCount,
            cursorAngleVariance=cursor_angle_variance,
            mouseJitter=mouseJitter,
            micropause=micropause,
            hesitation=hesitation,
            devicefingerprint=devicefingerprint,
            missing_canvas_fingerprint=missing_canvas_fingerprint,
            canvas_metrics=canvas_metrics,
            unsualscreenresolution=unsualscreenresolution,
            gpu_info=gpu_info,
            timing_metrics=timing_metrics,
            evasion_signals=evasion_signals
        )
        behavior_data.save()
        
        return JsonResponse({
            "status": "verified" if is_human else "rejected",
            "message": "Human verified!" if is_human else "Bot detected!",
            "classification": "Human" if is_human else "Bot",
            "score": round(human_score * 100),
            "metrics": {
                "human_score": round(human_score * 100),
                "bot_score": round(bot_score * 100),
                "human_indicators": human_indicators,
                "bot_indicators": bot_indicators,
                "has_human_behavior": has_human_behavior
            },
            "behavior_data": {
                "usai_id": data.get("usai_id", "unknown"),
                "timestamp": datetime.datetime.now().isoformat()
            }
        }, status=200)
        
        
    except Exception as e:
        logger.error("Error analyzing behavior:")
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            "status": "error",
            "message": f"Error processing request: {str(e)}",
            "error_details": {
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        }, status=500)



