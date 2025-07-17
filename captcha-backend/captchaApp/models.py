from django.db import models

class UserAttempt(models.Model):
    usai_id = models.CharField(max_length=255, unique=True)
    failed_attempts = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.usai_id} - {self.failed_attempts} attempts"

class UserBehavior_v1(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    usai_id = models.CharField(max_length=255)
    cursor_movements = models.JSONField()  # Store array of movements
    key_press_times = models.JSONField()   # Store array of timestamps
    key_hold_times = models.JSONField()    # Store array of hold durations
    click_timestamps = models.JSONField()  # Store array of click times
    click_intervals = models.JSONField(default=list)  # Store array of intervals between clicks
    cursor_speeds = models.JSONField()     # Store array of speeds
    cursor_acceleration = models.JSONField() # Store array of accelerations
    cursor_curvature = models.JSONField()  # Store array of curvatures
    paste_detected = models.BooleanField()
    total_time = models.IntegerField()     # Total time to submit in ms
    classification = models.CharField(max_length=10)  # 'Human' or 'Bot'
    human_score = models.FloatField()
    bot_score = models.FloatField()
    human_indicators = models.JSONField()  # Store array of indicators
    bot_indicators = models.JSONField()    # Store array of indicators
    bot_fingerprint_score = models.FloatField(default=0)
    suspicious_flag = models.BooleanField(default=False)
    suspicious_feature_ratio = models.FloatField(default=0)
    
    # New fields for enhanced metrics
    mouse_movement_debug = models.JSONField(default=dict)  # Store mouse movement debug data
    speed_calculation_debug = models.JSONField(default=dict)  # Store speed calculation debug data
    post_paste_activity = models.JSONField(default=dict)  # Store post paste activity data
    keyboard_patterns = models.JSONField(default=list)  # Store keyboard patterns
    suspicious_patterns = models.JSONField(default=list)  # Store suspicious patterns
    action_count = models.IntegerField(default=0)  # Store total action count
    is_automated_browser = models.BooleanField(default=False)  # Store automated browser flag
    cursor_entropy = models.FloatField(default=0)  # Store cursor entropy value
    scroll_speeds = models.JSONField(default=list)  # Store scroll speeds
    scroll_changes = models.IntegerField(default=0)  # Store scroll changes count
    idle_time = models.BigIntegerField(default=0)  # Store idle time in ms
    honeypot_value = models.CharField(max_length=255, null=True, blank=True)  # Store honeypot value if any
    tabkeycount = models.IntegerField(default=0)
    cursorAngleVariance = models.FloatField(default=0 , null=True)
    mouseJitter = models.JSONField(default=list)
    micropause = models.JSONField(default=list)
    hesitation = models.JSONField(default=list)
    
    class Meta:
        db_table = 'UserBehavior_v1'
        indexes = [
            models.Index(fields=['usai_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['classification']),
        ]
        
class UserBehavior_v2(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    usai_id = models.CharField(max_length=255)
    cursor_movements = models.JSONField()  # Store array of movements
    key_press_times = models.JSONField()   # Store array of timestamps
    key_hold_times = models.JSONField()    # Store array of hold durations
    click_timestamps = models.JSONField()  # Store array of click times
    click_intervals = models.JSONField(default=list)  # Store array of intervals between clicks
    cursor_speeds = models.JSONField()     # Store array of speeds
    cursor_acceleration = models.JSONField() # Store array of accelerations
    cursor_curvature = models.JSONField()  # Store array of curvatures
    paste_detected = models.BooleanField()
    total_time = models.IntegerField()     # Total time to submit in ms
    classification = models.CharField(max_length=10)  # 'Human' or 'Bot'
    human_score = models.FloatField()
    bot_score = models.FloatField()
    human_indicators = models.JSONField()  # Store array of indicators
    bot_indicators = models.JSONField()    # Store array of indicators
    bot_fingerprint_score = models.FloatField(default=0)
    suspicious_flag = models.BooleanField(default=False)
    suspicious_feature_ratio = models.FloatField(default=0)
    
    # New fields for enhanced metrics
    mouse_movement_debug = models.JSONField(default=dict)  # Store mouse movement debug data
    speed_calculation_debug = models.JSONField(default=dict)  # Store speed calculation debug data
    post_paste_activity = models.JSONField(default=dict)  # Store post paste activity data
    keyboard_patterns = models.JSONField(default=list)  # Store keyboard patterns
    suspicious_patterns = models.JSONField(default=list)  # Store suspicious patterns
    action_count = models.IntegerField(default=0)  # Store total action count
    is_automated_browser = models.BooleanField(default=False)  # Store automated browser flag
    cursor_entropy = models.FloatField(default=0)  # Store cursor entropy value
    scroll_speeds = models.JSONField(default=list)  # Store scroll speeds
    scroll_changes = models.IntegerField(default=0)  # Store scroll changes count
    idle_time = models.BigIntegerField(default=0)  # Store idle time in ms
    honeypot_value = models.CharField(max_length=255, null=True, blank=True)  # Store honeypot value if any
    tabkeycount = models.IntegerField(default=0)
    cursorAngleVariance = models.FloatField(default=0 , null=True)
    mouseJitter = models.JSONField(default=list)
    micropause = models.JSONField(default=list)
    hesitation = models.JSONField(default=list)
    devicefingerprint = models.CharField(default=0 , null=True)
    missing_canvas_fingerprint = models.BooleanField(default=False)
    canvas_metrics = models.JSONField(default=dict)
    unsualscreenresolution = models.JSONField(default=dict)
    gpu_info = models.JSONField(default=dict)
    timing_metrics = models.JSONField(default=dict)
    evasion_signals = models.JSONField(default=dict)

    class Meta:
        db_table = 'user_behavior_v2'
        indexes = [
            models.Index(fields=['usai_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['classification']),
        ]
        
class UserBehavior_v3(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    usai_id = models.CharField(max_length=255)
    cursor_movements = models.JSONField()  # Store array of movements
    key_press_times = models.JSONField()   # Store array of timestamps
    key_hold_times = models.JSONField()    # Store array of hold durations
    click_timestamps = models.JSONField()  # Store array of click times
    click_intervals = models.JSONField(default=list)  # Store array of intervals between clicks
    cursor_speeds = models.JSONField()     # Store array of speeds
    cursor_acceleration = models.JSONField() # Store array of accelerations
    cursor_curvature = models.JSONField()  # Store array of curvatures
    paste_detected = models.BooleanField()
    total_time = models.IntegerField()     # Total time to submit in ms
    classification = models.CharField(max_length=10)  # 'Human' or 'Bot'
    human_score = models.FloatField()
    bot_score = models.FloatField()
    human_indicators = models.JSONField()  # Store array of indicators
    bot_indicators = models.JSONField()    # Store array of indicators
    bot_fingerprint_score = models.FloatField(default=0)
    suspicious_flag = models.BooleanField(default=False)
    suspicious_feature_ratio = models.FloatField(default=0)
    
    # New fields for enhanced metrics
    mouse_movement_debug = models.JSONField(default=dict)  # Store mouse movement debug data
    speed_calculation_debug = models.JSONField(default=dict)  # Store speed calculation debug data
    post_paste_activity = models.JSONField(default=dict)  # Store post paste activity data
    keyboard_patterns = models.JSONField(default=list)  # Store keyboard patterns
    suspicious_patterns = models.JSONField(default=list)  # Store suspicious patterns
    action_count = models.IntegerField(default=0)  # Store total action count
    is_automated_browser = models.BooleanField(default=False)  # Store automated browser flag
    cursor_entropy = models.FloatField(default=0)  # Store cursor entropy value
    scroll_speeds = models.JSONField(default=list)  # Store scroll speeds
    scroll_changes = models.IntegerField(default=0)  # Store scroll changes count
    idle_time = models.IntegerField(default=0)  # Store idle time in ms
    honeypot_value = models.CharField(max_length=255, null=True, blank=True)  # Store honeypot value if any
    tabkeycount = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'user_behavior_v3'
        indexes = [
            models.Index(fields=['usai_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['classification']),
        ]