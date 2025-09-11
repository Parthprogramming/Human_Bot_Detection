1) Human Bot Detection :
Below are the metrics on the basis of which the Human and Bot are differentiated.
------------------------------------
    + cursor_movements,
    + key_press_times,
    + key_hold_times,
    + click_timestamps,
    + click_intervals,
    + cursor_speeds,
    + cursor_acceleration,
    + cursor_curvature
    + paste_detected,
    + total_time,
    + classification,
    + human_score,
    + bot_score,
    + human_indicators,
    + bot_indicators,
    + bot_fingerprint_score
    + suspicious_flag,
    + suspicious_feature_ratio,
    + mouse_movement_debug,
    + speed_calculation_debug,
    + post_paste_activity,
    + keyboard_patterns,suspicious_patterns,
    + action_count
    + is_automated_browser,
    + cursor_entropy,
    + scroll_speeds,
    + scroll_changes,
    + idle_time,
    + honeypot_value,
    + tabkeycount,
    + cursorAngleVariance,
    + mouseJitter
    + micropause,
    + hesitation,
    + devicefingerprint,
    + missing_canvas_fingerprint,
    + canvas_metrics,
    + unsualscreenresolution,
    + gpu_info,
    + timing_metrics,
    + evasion_signals
(42)
Detection Parameter : 
1) No Cursor movements , Fast cursor movements , Straight cursor movements , Spoofed GPU's , Having GPU names as "Google Vulkan , Swift swader etc ", Missing canvas fingerprint , Honey pot value filled , More number of Bot indicators , Perfect cursor angles(Humans have unlinear cursor movements). 
---------------------------------------

2) HTTP Client Bot detection below are the metrics on the basis of which HTTP CLIENT BOT are detected : 

--------------------------------------------------------
    + ip_address 
    + timestamp
    + user_agent 
    + headers 
    + endpoint 
    + method 
    + request_interval 
    + payload_schema_valid
    + cookies_present
    + confidence 
    + classification 
    + suspicious_headers 
    + request_fingerprint
    + session_id 
    + is_headless_browser 
    + automation_detected 
    + rate_limit_exceeded 
    + cookies 
(15)
------------------------------------------------------------


3) To detect if the user is Authenticated or Unauthenticated on the basis of the behaviorial metrics :


