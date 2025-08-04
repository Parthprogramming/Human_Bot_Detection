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
from .models import UserBehavior_v1
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
            "click_intervals": behavior.get("clickTimes", []),

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


def analyze_behavior(data):
    """Enhanced behavior analysis with improved human-bot distinction"""
    behavior = data.get("behavior", {})
    cursor_movements = behavior.get("cursorMovements", [])
    key_press_times = behavior.get("keyPressTimes", [])
    key_hold_times = behavior.get("keyHoldTimes", [])
    click_timestamps = behavior.get("clickTimestamps", [])
    cursor_speeds = behavior.get("cursorSpeeds", [])
    cursor_acceleration = behavior.get("cursorAcceleration", [])
    cursor_curvature = behavior.get("cursorCurvature", [])
    paste_detected = behavior.get("pasteDetected", False)
    total_time = behavior.get("totalTimeToSubmit", 0)
    bot_fingerprint_score = behavior.get("botFingerprintScore", 0)
    suspicious_flag = behavior.get("suspiciousFlag", False)
    suspicious_feature_ratio = behavior.get("suspiciousFeatureRatio", 0)
    scroll_changes = behavior.get("scrollChanges", 0)
    cursorangle = behavior.get("cursorAngle" , [])
    mouseJitter = behavior.get("mouseJitter",[])
    micropause = behavior.get("microPauses",[])
    hesitation = behavior.get("hesitationTimes",[])
    
    
    cursor_angle_variance = compute_cursor_angle_variance(cursorangle)  
    behavior["cursor_angle_variance"] = cursor_angle_variance
       
    
    confidence_score = 0.5  # Start neutral
    feature_scores = {}
    human_indicators = []
    bot_indicators = []
    
    
    import numpy as np  # Make sure this is imported at the top

# Step 1: Extract the list of angles from behavior data
    cursor_angles = behavior.get("cursorAngles", [])
    cursor_angle_std = None  # Default if list is invalid
    angle_variance_valid = False

# Step 2: Ensure it's a valid list of numeric angles
    if isinstance(cursor_angles, list) and len(cursor_angles) >= 5:
        try:
            cleaned_angles = [float(a) for a in cursor_angles if isinstance(a, (int, float))]

            if len(cleaned_angles) >= 5:
                cursor_angle_std = float(np.std(cleaned_angles))
                angle_variance_valid = True
                logger.info(f"[Angle Variance] STD={cursor_angle_std:.2f}")
            else:
                logger.warning("Not enough valid cursor angles to compute variance.")
        except Exception as e:
            logger.warning(f"Error calculating angle variance: {e}")
    else:
        logger.info("Not enough cursor angles to evaluate variance.")

    if angle_variance_valid:
        if cursor_angle_std > 30:
            human_score += 0.15
            human_indicators.append("varied_cursor_angles")
        else:
            bot_score += 0.15
            bot_indicators.append("static_cursor_path")

    # 1. Enhanced Typing Analysis (25% weight)
    if key_press_times:
        logger.info("\nTyping behavior analysis:")
        typing_intervals = [key_press_times[i] - key_press_times[i-1] for i in range(1, len(key_press_times))]
        
        if typing_intervals:
            avg_typing_interval = sum(typing_intervals) / len(typing_intervals)
            std_typing_interval = np.std(typing_intervals) if len(typing_intervals) > 1 else 0
            
            logger.info(f"  Average typing interval: {avg_typing_interval}ms")
            logger.info(f"  Typing interval std dev: {std_typing_interval}ms")
            
            # More nuanced typing pattern analysis
            if 50 <= avg_typing_interval <= 800:  # Wider range for natural typing
                if std_typing_interval > 30:  # Natural variation
                    confidence_score += 0.15
                    feature_scores["typing_variation"] = 0.9
                    human_indicators.append("natural_typing_variation")
                elif std_typing_interval > 15:  # Moderate variation
                    confidence_score += 0.1
                    feature_scores["typing_variation"] = 0.7
                    human_indicators.append("moderate_typing_variation")
            else:
                confidence_score -= 0.1
                feature_scores["typing_variation"] = 0.3
                bot_indicators.append("unnatural_typing_speed")
        
        # Enhanced key hold analysis
        if key_hold_times:
            avg_hold = sum(key_hold_times) / len(key_hold_times)
            hold_std = np.std(key_hold_times) if len(key_hold_times) > 1 else 0
            
            logger.info(f"  Average key hold: {avg_hold}ms")
            logger.info(f"  Key hold std dev: {hold_std}ms")
            
            if 40 <= avg_hold <= 400:  # Wider range for natural holds
                if hold_std > 20:  # Natural variation
                    confidence_score += 0.1
                    feature_scores["key_hold"] = 0.8
                    human_indicators.append("natural_key_hold")
                else:
                    confidence_score += 0.05
                    feature_scores["key_hold"] = 0.6
                    human_indicators.append("moderate_key_hold")
            else:
                confidence_score -= 0.05
                feature_scores["key_hold"] = 0.3
                bot_indicators.append("unnatural_key_hold")
    
    # 2. Enhanced Cursor Movement Analysis (30% weight)
    if cursor_movements:
        logger.info("\nCursor movement analysis:")
        movement_times = [m["timestamp"] for m in cursor_movements]
        movement_durations = [movement_times[i] - movement_times[i-1] for i in range(1, len(movement_times))]
        
        if movement_durations:
            avg_duration = sum(movement_durations) / len(movement_durations)
            std_duration = np.std(movement_durations) if len(movement_durations) > 1 else 0
            
            logger.info(f"  Average duration: {avg_duration}ms")
            logger.info(f"  Duration std dev: {std_duration}ms")
            
            # More nuanced cursor movement analysis
            if 5 <= avg_duration <= 600:  # Wider range for natural movement
                if std_duration > 10:  # Natural variation
                    confidence_score += 0.15
                    feature_scores["cursor_variation"] = 0.9
                    human_indicators.append("natural_cursor_variation")
                elif std_duration > 5:  # Moderate variation
                    confidence_score += 0.1
                    feature_scores["cursor_variation"] = 0.7
                    human_indicators.append("moderate_cursor_variation")
            else:
                confidence_score -= 0.1
                feature_scores["cursor_variation"] = 0.3
                bot_indicators.append("unnatural_cursor_speed")
        
        # Enhanced acceleration analysis
        if cursor_acceleration:
            accel_std = np.std(cursor_acceleration) if len(cursor_acceleration) > 1 else 0
            accel_mean = np.mean(cursor_acceleration)
            
            logger.info(f"  Acceleration std dev: {accel_std}")
            logger.info(f"  Mean acceleration: {accel_mean}")
            
            if accel_std > 30 and abs(accel_mean) < 1000:  # Natural acceleration patterns
                confidence_score += 0.1
                feature_scores["cursor_acceleration"] = 0.8
                human_indicators.append("natural_acceleration")
            else:
                confidence_score -= 0.05
                feature_scores["cursor_acceleration"] = 0.3
                bot_indicators.append("unnatural_acceleration")
        
        # Enhanced curvature analysis
        if cursor_curvature:
            avg_curvature = sum(cursor_curvature) / len(cursor_curvature)
            curvature_std = np.std(cursor_curvature) if len(cursor_curvature) > 1 else 0
            
            logger.info(f"  Average curvature: {avg_curvature}")
            logger.info(f"  Curvature std dev: {curvature_std}")
            
            if 0.4 <= avg_curvature <= 2.5 and curvature_std > 0.2:  # Natural curvature
                confidence_score += 0.12  # Increased reward
                has_human_behavior = True
                human_indicators.append("natural_curvature")
            else:
                bot_score += 0.03  # Reduced penalty
                bot_indicators.append("unnatural_curvature")
    
    # 3. Enhanced Click Analysis (15% weight)
    if click_timestamps:
        logger.info("\nClick analysis:")
        if len(click_timestamps) >= 2:
            click_intervals = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
            avg_click_interval = sum(click_intervals) / len(click_intervals)
            
            logger.info(f"  Average click interval: {avg_click_interval}ms")
            
            if avg_click_interval > 150:  # Natural click timing
                confidence_score += 0.1
                feature_scores["click_timing"] = 0.8
                human_indicators.append("natural_click_timing")
            else:
                confidence_score -= 0.05
                feature_scores["click_timing"] = 0.3
                bot_indicators.append("unnatural_click_timing")
    
    # 4. Enhanced Timing Analysis (20% weight)
    if total_time > 0:
        logger.info(f"\nTiming analysis:")
        logger.info(f"  Total time to submit: {total_time}ms")
        
        if 1000 <= total_time <= 20000:  # Wider range for natural timing
            if 2000 <= total_time <= 10000:  # Ideal range
                confidence_score += 0.15
                feature_scores["timing"] = 0.9
                human_indicators.append("natural_timing")
            else:
                confidence_score += 0.1
                feature_scores["timing"] = 0.7
                human_indicators.append("acceptable_timing")
        else:
            confidence_score -= 0.1
            feature_scores["timing"] = 0.3
            bot_indicators.append("unnatural_timing")
    
    # 5. Enhanced Paste Behavior Analysis (10% weight)
    if paste_detected:
        logger.info("\nPaste behavior analysis:")
        has_supporting_behavior = False
        
        if cursor_movements:
            paste_time = min(m["timestamp"] for m in cursor_movements) if cursor_movements else 0
            movements_before = sum(1 for m in cursor_movements if m["timestamp"] < paste_time)
            movements_after = sum(1 for m in cursor_movements if m["timestamp"] > paste_time)
            
            if movements_before > 0 or movements_after > 0:
                has_supporting_behavior = True
                confidence_score += 0.05
                feature_scores["paste_behavior"] = 0.8
                human_indicators.append("natural_paste_behavior")
        
        if not has_supporting_behavior:
            confidence_score -= 0.05
            feature_scores["paste_behavior"] = 0.3
            bot_indicators.append("suspicious_paste_behavior")
    
    
    
    is_human = confidence_score >= 0.6  
    
    # Additional checks for borderline cases
    if 0.55 <= confidence_score < 0.6:
        # If we have strong human indicators, lean towards human
        if len(human_indicators) > len(bot_indicators):
            is_human = True
            logger.info("Borderline case: Leaning human due to strong human indicators")
        else:
            is_human = False
            logger.info("Borderline case: Leaning bot due to strong bot indicators")
    
    logger.info(f"Final classification: {'Human' if is_human else 'Bot'}")
    logger.info("=== ENHANCED BEHAVIOR ANALYSIS END ===\n")
    
    return is_human, confidence_score, {
        "feature_scores": feature_scores,
        "human_indicators": human_indicators,
        "bot_indicators": bot_indicators
    }

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
        click_intervals = behavior.get("clicktimes",0)
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
        click_intervals = behavior.get("clicktimes",[])
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

        # --- Require more bot indicators for bot classification ---
        # Aggregate weak bot signals: if 7+ bot indicators, treat as bot
        multiple_bot_signals = len(bot_indicators) >= 7
        # In borderline cases, always lean human unless hard rule is triggered
        borderline_margin = 0.04
        # Define strong human indicators
        strong_human_indicators = set([
            "natural_typing", "natural_movement", "natural_clicking", "high_entropy", "natural_jitter"
        ])
        n_strong_human = len([h for h in human_indicators if h in strong_human_indicators])
        # --- HARD RULE: If bot fingerprint is very high or automation detected, always classify as Bot ---
        hard_rule_bot = (
            bot_fingerprint_score >= 0.85 or
            is_automated_browser or
            ("high_bot_fingerprint" in bot_indicators and bot_score > human_score)
        )
        # Even more conservative hard rules for advanced bots
        # 1. Truly impossible entropy
        if cursor_entropy is not None and cursor_entropy < 0.0001:
            hard_rule_bot = True
            bot_indicators.append("impossible_entropy")
        # 2. No mouse jitter (robotic movement, but only if many moves)
        if (not mouseJitter or (isinstance(mouseJitter, list) and sum(mouseJitter) == 0)) and (cursor_movements and len(cursor_movements) > 30):
            hard_rule_bot = True
            bot_indicators.append("no_mouse_jitter")
        # 3. Perfectly regular click intervals (bot-like, but only if >15 clicks)
        if click_timestamps and len(click_timestamps) >= 16:
            click_intervals_check = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]
            if len(set(click_intervals_check)) == 1:
                hard_rule_bot = True
                bot_indicators.append("perfect_click_intervals")
        # Aggregate weak bot signals: if 7+ bot indicators, treat as bot
        multiple_bot_signals = len(bot_indicators) >= 7
        # More forgiving margin for human classification
        human_margin = 0.04
        borderline_margin = 0.04
        # Define strong human indicators
        strong_human_indicators = set([
            "natural_typing", "natural_movement", "natural_clicking", "high_entropy", "natural_jitter"
        ])
        n_strong_human = len([h for h in human_indicators if h in strong_human_indicators])
        if hard_rule_bot:
            is_human = False
            logger.info("Hard rule triggered: Bot fingerprint or automation detected or advanced bot pattern.")
        elif multiple_bot_signals:
            is_human = False
            logger.info("Multiple bot indicators present (7+). Classified as Bot.")
        elif abs(human_score - bot_score) < borderline_margin:
            is_human = True
            logger.info("Borderline case: Always lean human unless hard rule triggered.")
        elif n_strong_human >= 1 and not hard_rule_bot:
            is_human = True
            logger.info("At least one strong human indicator and no hard rule. Classified as Human.")
        elif len(human_indicators) > len(bot_indicators):
            is_human = True
            logger.info("Leaning human due to more human indicators.")
        elif human_score > bot_score + human_margin:
            is_human = True
        else:
            is_human = False
            logger.info("Weak human evidence. Classified as Bot.")
        # Log final decision
        logger.info(f"Final decision - Human: {is_human}, Score - Human: {human_score}, Bot: {bot_score}, Indicators: H={human_indicators}, B={bot_indicators}, BotFingerprint={bot_fingerprint_score}")
        logger.info(f"DEBUG: All indicators: Human={human_indicators}, Bot={bot_indicators}, Scores: H={human_score}, B={bot_score}")
        
        # Log final decision
        logger.info(f"Final decision - Human: {is_human}, Score - Human: {human_score}, Bot: {bot_score}")
        
        # Calculate click intervals if we have click timestamps
        click_intervals = []
        if click_timestamps and len(click_timestamps) >= 2:
            click_intervals = [click_timestamps[i] - click_timestamps[i-1] for i in range(1, len(click_timestamps))]

    
        behavior_data = UserBehavior_v1(
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
            hesitation=hesitation
        )
        behavior_data.save()
        
        if is_human:
            return JsonResponse({
                "status": "success",
                "message": "User verified successfully!",
                "classification": "Human",
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
                    "behavior": {
                        
                        "cursorMovements": behavior.get("cursorMovements", []),
                        "cursorSpeeds": behavior.get("cursorSpeeds", []),
                        "cursorCurvature": behavior.get("cursorCurvature", []),
                        "cursorAcceleration": behavior.get("cursorAcceleration", []),
                        "cursorAngleVariance": cursor_angle_variance,
                        "Entropy": behavior.get("entropy", None),
                        "keyPressTimes": behavior.get("keyPressTimes", []),
                        "keyHoldTimes": behavior.get("keyHoldTimes", []),
                        "clickTimes": behavior.get("clickTimes", []),
                        "clickTimestamps": behavior.get("clickTimestamps", []),
                        "scrollSpeeds": behavior.get("scrollSpeeds", []),
                        "totalTimeToSubmit": behavior.get("totalTimeToSubmit", 0),
                        "scrollChanges": behavior.get("scrollChanges", 0),
                        "idleTime": behavior.get("idleTime", 0),
                        "pasteDetected": behavior.get("pasteDetected", False),
                        "postPasteActivity": behavior.get("postPasteActivity", {}),
                        "keyboardPatterns": behavior.get("keyboardPatterns", []),
                        "suspiciousPatterns": behavior.get("suspiciousPatterns", []),
                        "actionCount": behavior.get("actionCount", 0),
                        "isAutomatedBrowser": behavior.get("isAutomatedBrowser", False),
                        "botFingerprintScore": behavior.get("botFingerprintScore", 0),
                        "mouseMovementDebug": {
                            "distance": behavior.get("mouseMovementDebug", {}).get("distance", 0),
                            "timeDiff": behavior.get("mouseMovementDebug", {}).get("timeDiff", 0),
                            "dx": behavior.get("mouseMovementDebug", {}).get("dx", 0),
                            "dy": behavior.get("mouseMovementDebug", {}).get("dy", 0),
                            "currentSpeed": behavior.get("mouseMovementDebug", {}).get("currentSpeed", 0)
                        },
                        "speedCalculationDebug": {
                            "rawSpeed": behavior.get("speedCalculationDebug", {}).get("rawSpeed", 0),
                            "filteredSpeed": behavior.get("speedCalculationDebug", {}).get("filteredSpeed", 0),
                            "latestSpeed": behavior.get("speedCalculationDebug", {}).get("latestSpeed", 0)
                        },
                        "mouseJitter": behavior.get("mouseJitter", []),
                        "microPauses": behavior.get("microPauses", []),
                        "hesitationTimes": behavior.get("hesitationTimes", []),
                    },
                    "verification_status": {
                        "status": "success",
                        "message": "User verified successfully!",
                        "classification": "Human",
                        "score": round(human_score * 100),
                        "metrics": {
                            "human_score": round(human_score * 100),
                            "bot_score": round(bot_score * 100),
                            "human_indicators": human_indicators,
                            "bot_indicators": bot_indicators,
                            "has_human_behavior": has_human_behavior
                        }
                    },
                    "human_or_bot": "Human",
                    "cursor_speeds": behavior.get("cursorSpeeds", []),
                    "click_intervals": click_intervals,
                    "timestamp": datetime.datetime.now().isoformat(),
                    
                    
                }
                 
            })
       
            
        else:
            return JsonResponse({
                "status": "rejected",
                "message": "Automated behavior detected! Access denied.",
                "classification": "Bot",
                "score": round(bot_score * 100),
                "metrics": {
                    "human_score": round(human_score * 100),
                    "bot_score": round(bot_score * 100),
                    "human_indicators": human_indicators,
                    "bot_indicators": bot_indicators,
                    "has_human_behavior": has_human_behavior
                },
                "behavior_data": {
                    "usai_id": data.get("usai_id", "unknown"),
                    "behavior": {
                        "cursorMovements": behavior.get("cursorMovements", []),
                        "cursorSpeeds": behavior.get("cursorSpeeds", []),
                        "cursorCurvature": behavior.get("cursorCurvature", []),
                        "cursorAcceleration": behavior.get("cursorAcceleration", []),
                        "keyPressTimes": behavior.get("keyPressTimes", []),
                        "keyHoldTimes": behavior.get("keyHoldTimes", []),
                        "clickTimes": behavior.get("clickTimes", []),
                        "clickTimestamps": behavior.get("clickTimestamps", []),
                        "scrollSpeeds": behavior.get("scrollSpeeds", []),
                        "totalTimeToSubmit": behavior.get("totalTimeToSubmit", 0),
                        "scrollChanges": behavior.get("scrollChanges", 0),
                        "idleTime": behavior.get("idleTime", 0),
                        "pasteDetected": behavior.get("pasteDetected", False),
                        "postPasteActivity": behavior.get("postPasteActivity", {}),
                        "keyboardPatterns": behavior.get("keyboardPatterns", []),
                        "suspiciousPatterns": behavior.get("suspiciousPatterns", []),
                        "actionCount": behavior.get("actionCount", 0),
                        "isAutomatedBrowser": behavior.get("isAutomatedBrowser", False),
                        "botFingerprintScore": behavior.get("botFingerprintScore", 0),
                        "mouseMovementDebug": {
                            "distance": behavior.get("mouseMovementDebug", {}).get("distance", 0),
                            "timeDiff": behavior.get("mouseMovementDebug", {}).get("timeDiff", 0),
                            "dx": behavior.get("mouseMovementDebug", {}).get("dx", 0),
                            "dy": behavior.get("mouseMovementDebug", {}).get("dy", 0),
                            "currentSpeed": behavior.get("mouseMovementDebug", {}).get("currentSpeed", 0)
                        },
                        "speedCalculationDebug": {
                            "rawSpeed": behavior.get("speedCalculationDebug", {}).get("rawSpeed", 0),
                            "filteredSpeed": behavior.get("speedCalculationDebug", {}).get("filteredSpeed", 0),
                            "latestSpeed": behavior.get("speedCalculationDebug", {}).get("latestSpeed", 0)
                        },
                        "mouseJitter": behavior.get("mouseJitter", []),
                        "microPauses": behavior.get("microPauses", []),
                        "hesitationTimes": behavior.get("hesitationTimes", []),
                    },
                    "verification_status": {
                        "status": "rejected",
                        "message": "Automated behavior detected! Access denied.",
                        "classification": "Bot",
                        "score": round(bot_score * 100),
                        "metrics": {
                            "human_score": round(human_score * 100),
                            "bot_score": round(bot_score * 100),
                            "human_indicators": human_indicators,
                            "bot_indicators": bot_indicators,
                            "has_human_behavior": has_human_behavior
                        }
                    },
                    "human_or_bot": "Bot",
                    "cursor_speeds": behavior.get("cursorSpeeds", []),
                    "click_intervals": click_intervals,
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

