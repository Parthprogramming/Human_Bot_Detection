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
from .models import UserBehavior_v2
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
            if raw_speed is not None and raw_speed > 0:
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
            width = unsualscreenresolution.get("width", 0)
            height = unsualscreenresolution.get("height", 0)
            if width > 400 and height > 300:
                human_score += 0.01
                human_indicators.append("screen_resolution_present")
        
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
            if cursor_angle_variance > 30:
                human_score += 0.15
                human_indicators.append("varied_cursor_angles")
                has_human_behavior = True
            else:
                bot_score += 0.15
                bot_indicators.append("static_cursor_path")
        
        # 1. Typing Analysis - Softer, wider range
        if key_press_times and len(key_press_times) >= 2:
            typing_intervals = [key_press_times[i] - key_press_times[i-1] for i in range(1, len(key_press_times))]
            avg_typing = sum(typing_intervals) / len(typing_intervals)
            std_typing = np.std(typing_intervals) if len(typing_intervals) > 1 else 0
            
            # Softer, wider thresholds for human typing
            if 40 <= avg_typing <= 900 and std_typing > 20:  # Natural human typing range
                human_score += 0.18  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_typing")
            elif avg_typing < 20 or avg_typing > 1200 or std_typing < 7:  # Only penalize extreme cases
                bot_score += 0.10  # Reduced penalty
                bot_indicators.append("unnatural_typing")

        # 2. Cursor Movement - Softer, wider range
        if cursor_movements and len(cursor_movements) >= 2:
            movement_times = [m["timestamp"] for m in cursor_movements]
            movement_durations = [movement_times[i] - movement_times[i-1] for i in range(1, len(movement_times))]
            avg_duration = sum(movement_durations) / len(movement_durations)
            std_duration = np.std(movement_durations) if len(movement_durations) > 1 else 0
            
            # Softer, wider movement patterns
            if 5 <= avg_duration <= 700 and std_duration > 12:  # Natural human movement
                human_score += 0.16  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_movement")
            elif avg_duration < 3 or avg_duration > 1200 or std_duration < 5:
                bot_score += 0.08  # Reduced penalty
                bot_indicators.append("unnatural_movement")

        # 3. Click Analysis - Softer
        if click_timestamps and len(click_timestamps) >= 2:
            click_intervals = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
            avg_click = sum(click_intervals) / len(click_intervals)
            std_click = np.std(click_intervals) if len(click_intervals) > 1 else 0
            
            # Softer clicking patterns
            if avg_click > 80 and std_click > 10:  # Natural clicking
                human_score += 0.14  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_clicking")
            elif avg_click < 30 or avg_click > 7000 or std_click < 5:
                bot_score += 0.08  # Reduced penalty
                bot_indicators.append("unnatural_clicking")

        # 4. Timing Analysis - Softer
        if total_time > 0:
            # Softer timing expectations
            if 1000 <= total_time <= 30000:  # 1 to 30 seconds is reasonable
                human_score += 0.15
                has_human_behavior = True
                human_indicators.append("natural_timing")
            elif total_time < 500 or total_time > 60000:  # Only penalize very quick or very slow
                bot_score += 0.10
                bot_indicators.append("unnatural_timing")
        
        # 8. Curvature - Softer
        if cursor_curvature:
            avg_curvature = sum(cursor_curvature) / len(cursor_curvature)
            curvature_std = np.std(cursor_curvature) if len(cursor_curvature) > 1 else 0
            
            logger.info(f"  Average curvature: {avg_curvature}")
            logger.info(f"  Curvature std dev: {curvature_std}")
            
            if 0.4 <= avg_curvature <= 2.5 and curvature_std > 0.15:  # Natural curvature
                human_score += 0.13  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_curvature")
            else:
                bot_score += 0.02  # Reduced penalty
                bot_indicators.append("unnatural_curvature")

        # 9. Key Hold - Softer
        if key_hold_times:
            avg_hold = sum(key_hold_times) / len(key_hold_times)
            std_hold = np.std(key_hold_times) if len(key_hold_times) > 1 else 0
            
            # Softer, wider key hold patterns
            if 10 <= avg_hold <= 1500 and std_hold > 3:  # Very wide range for natural key holds
                human_score += 0.13  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_key_hold")
            elif avg_hold < 3 or avg_hold > 3000 or (avg_hold > 1500 and std_hold < 1):  # Only penalize extreme cases
                bot_score += 0.02  # Reduced penalty
                bot_indicators.append("unnatural_key_hold")

        # --- NEW METRICS INTEGRATION ---
        # 10. GPU Info Analysis
        if gpu_info:
            vendor = str(gpu_info.get("vendor", "")).lower()
            renderer = str(gpu_info.get("renderer", "")).lower()
            # Common bot/VM/automation GPU vendors
            suspicious_vendors = ["microsoft", "llvmpipe", "swiftshader", "mesa", "google", "virtualbox", "vmware", "parallels"]
            if any(v in vendor for v in suspicious_vendors) or any(v in renderer for v in suspicious_vendors):
                bot_score += 0.12
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

        # 12. Timing Metrics (fine-grained timing analysis)
        if timing_metrics:
            # Example: check for suspiciously low or high event intervals
            min_interval = timing_metrics.get("min_event_interval", None)
            max_interval = timing_metrics.get("max_event_interval", None)
            avg_interval = timing_metrics.get("avg_event_interval", None)
            if min_interval is not None and (min_interval < 2 or min_interval > 2000):
                bot_score += 0.08
                bot_indicators.append("suspicious_min_event_interval")
            if max_interval is not None and (max_interval > 10000 or max_interval < 10):
                bot_score += 0.08
                bot_indicators.append("suspicious_max_event_interval")
            if avg_interval is not None and (avg_interval < 10 or avg_interval > 3000):
                bot_score += 0.08
                bot_indicators.append("suspicious_avg_event_interval")
            if min_interval and max_interval and avg_interval:
                if 10 <= min_interval <= 1000 and 10 <= avg_interval <= 2000 and 10 <= max_interval <= 8000:
                    human_score += 0.05
                    human_indicators.append("normal_timing_metrics")

        # 13. Evasion Signals
        if evasion_signals:
            # Example: webdriver, languages spoofed, plugins spoofed, etc.
            if evasion_signals.get("webdriver", False):
                bot_score += 0.18
                bot_indicators.append("webdriver_flagged")
            if evasion_signals.get("languages_spoofed", False):
                bot_score += 0.10
                bot_indicators.append("languages_spoofed")
            if evasion_signals.get("plugins_spoofed", False):
                bot_score += 0.10
                bot_indicators.append("plugins_spoofed")
            if evasion_signals.get("chrome_runtime_modified", False):
                bot_score += 0.10
                bot_indicators.append("chrome_runtime_modified")
            # If no evasion signals, reward a bit
            if not any(evasion_signals.values()):
                human_score += 0.04
                human_indicators.append("no_evasion_signals")

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

        critical_bot_indicators = set([
            "impossible_entropy", "no_mouse_jitter", "perfect_click_intervals", "no_micro_pauses", "no_hesitation"
        ])
        n_critical_bot = len([b for b in bot_indicators if b in critical_bot_indicators])
        multiple_bot_signals = len(bot_indicators) >= 7 and n_critical_bot >= 1
        # If 2+ critical bot indicators, always classify as bot
        hard_rule_bot = (
            bot_fingerprint_score >= 0.85 or
            is_automated_browser or
            ("high_bot_fingerprint" in bot_indicators and bot_score > human_score) or
            n_critical_bot >= 2
        )
        # Even more conservative hard rules for advanced bots
        if cursor_entropy is not None and cursor_entropy < 0.0001:
            hard_rule_bot = True
            bot_indicators.append("impossible_entropy")
        if (not mouseJitter or (isinstance(mouseJitter, list) and sum(mouseJitter) == 0)) and (cursor_movements and len(cursor_movements) > 30):
            hard_rule_bot = True
            bot_indicators.append("no_mouse_jitter")
        if click_timestamps and len(click_timestamps) >= 16:
            click_intervals_check = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
            if len(set(click_intervals_check)) == 1:
                hard_rule_bot = True
                bot_indicators.append("perfect_click_intervals")

        # --- ENHANCED FINAL DECISION LOGIC (No Borderline, Not Lenient) ---
        strong_bot_indicators = set([
            "webdriver_flagged", "missing_canvas_fingerprint", "suspicious_gpu_vendor",
            "impossible_entropy", "no_mouse_jitter", "perfect_click_intervals"
        ])
        n_strong_bot = len([b for b in bot_indicators if b in strong_bot_indicators])
        n_human = len(human_indicators)
        n_bot = len(bot_indicators)

        if hard_rule_bot:
            is_human = False
            retry_required = False
            logger.info("Hard rule triggered: Bot fingerprint, automation, or 2+ critical bot indicators.")
        elif n_strong_bot >= 2:
            is_human = False
            retry_required = False
            logger.info("Multiple strong bot indicators. Classified as Bot.")
        elif n_human >= 2 and n_bot <= 1:
            is_human = True
            retry_required = False
            logger.info("At least 2 human indicators and <=1 bot indicator. Classified as Human.")
        elif human_score > bot_score:
            is_human = True
            retry_required = False
            logger.info("Human score exceeds bot score. Classified as Human.")
        else:
            is_human = False
            retry_required = False
            logger.info("Weak human evidence. Classified as Bot.")

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
        
        behavior_data = UserBehavior_v2(
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


