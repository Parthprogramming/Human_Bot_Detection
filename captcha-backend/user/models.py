from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    """
    Extended user profile to store additional user information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    usai_id = models.CharField(max_length=100, unique=True, help_text="Unique USAI identifier")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.usai_id}"


class UserSession(models.Model):

    session_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255, help_text="User's display name")
    usai_id = models.CharField(max_length=100, help_text="USAI identifier")
    session_type = models.CharField(
        max_length=20,
        choices=[
            ('SIGNIN', 'Sign In'),
            ('SIGNUP', 'Sign Up'),
        ],
        help_text="Type of session - sign in or sign up"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['usai_id']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.usai_id}) - {self.session_type} - {self.session_id}"
    
    def is_session_expired(self, timeout_minutes=30):
        """
        Check if session has expired based on last activity
        """
        from datetime import timedelta
        return timezone.now() > self.last_activity + timedelta(minutes=timeout_minutes)
    
    def update_activity(self):
        """
        Update last activity timestamp
        """
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class SignUpAttempt(models.Model):
    """
    Model to track sign-up attempts for analytics and security
    """
    session_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    usai_id = models.CharField(max_length=100)
    success = models.BooleanField(default=False)
    attempt_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signup_attempts'
        indexes = [
            models.Index(fields=['usai_id']),
            models.Index(fields=['attempt_time']),
            models.Index(fields=['success']),
        ]
        ordering = ['-attempt_time']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.name} ({self.usai_id}) - {status} - {self.attempt_time}"


class SignInAttempt(models.Model):
    """
    Model to track sign-in attempts for analytics and security
    """
    session_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255, null=True, blank=True)
    usai_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    attempt_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signin_attempts'
        indexes = [
            models.Index(fields=['usai_id']),
            models.Index(fields=['attempt_time']),
            models.Index(fields=['success']),
        ]
        ordering = ['-attempt_time']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.usai_id} - {status} - {self.attempt_time}"


class BehavioralData(models.Model):
    """
    Model to store comprehensive behavioral data for bot detection analysis
    """
    session_id = models.CharField(max_length=100, help_text="Session identifier")
    user_auth = models.CharField(
        max_length=20,
        choices=[
            ('Authorized_user', 'Authorized User'),
            ('Unauthorized_user', 'Unauthorized User'),
        ],
        help_text="User authorization status"
    )
    
    # Core behavioral metrics
    cursor_movements = models.JSONField(default=list, help_text="Store array of movements")
    key_press_times = models.JSONField(default=list, help_text="Store array of timestamps")
    key_hold_times = models.JSONField(default=list, help_text="Store array of hold durations")
    click_timestamps = models.JSONField(default=list, help_text="Store array of click times")
    click_intervals = models.JSONField(default=list, help_text="Store array of intervals between clicks")
    cursor_speeds = models.JSONField(default=list, help_text="Store array of speeds")
    cursor_acceleration = models.JSONField(default=list, help_text="Store array of accelerations")
    cursor_curvature = models.JSONField(default=list, help_text="Store array of curvatures")
    paste_detected = models.BooleanField(default=False)
    total_time = models.IntegerField(help_text="Total time to submit in ms")
    
    # Classification and scoring
    classification = models.CharField(max_length=10, help_text="'Human' or 'Bot'")
    human_score = models.FloatField(default=0.0)
    bot_score = models.FloatField(default=0.0)
    human_indicators = models.JSONField(default=list, help_text="Store array of indicators")
    bot_indicators = models.JSONField(default=list, help_text="Store array of indicators")
    bot_fingerprint_score = models.FloatField(default=0.0)
    suspicious_flag = models.BooleanField(default=False)
    suspicious_feature_ratio = models.FloatField(default=0.0)
    
    # Enhanced behavioral metrics
    mouse_movement_debug = models.JSONField(default=dict, help_text="Store mouse movement debug data")
    speed_calculation_debug = models.JSONField(default=dict, help_text="Store speed calculation debug data")
    post_paste_activity = models.JSONField(default=dict, help_text="Store post paste activity data")
    keyboard_patterns = models.JSONField(default=list, help_text="Store keyboard patterns")
    suspicious_patterns = models.JSONField(default=list, help_text="Store suspicious patterns")
    action_count = models.IntegerField(default=0, help_text="Store total action count")
    is_automated_browser = models.BooleanField(default=False, help_text="Store automated browser flag")
    cursor_entropy = models.FloatField(default=0.0, help_text="Store cursor entropy value")
    scroll_speeds = models.JSONField(default=list, help_text="Store scroll speeds")
    scroll_changes = models.IntegerField(default=0, help_text="Store scroll changes count")
    idle_time = models.BigIntegerField(default=0, help_text="Store idle time in ms")
    honeypot_value = models.CharField(max_length=255, null=True, blank=True, help_text="Store honeypot value if any")
    tabkeycount = models.IntegerField(default=0)
    cursorAngleVariance = models.FloatField(default=0.0, null=True)
    mouseJitter = models.JSONField(default=list)
    micropause = models.JSONField(default=list)
    hesitation = models.JSONField(default=list)
    devicefingerprint = models.CharField(max_length=255, default="0", null=True)
    missing_canvas_fingerprint = models.BooleanField(default=False)
    canvas_metrics = models.JSONField(default=dict)
    unsualscreenresolution = models.JSONField(default=dict)
    gpu_info = models.JSONField(default=dict)
    timing_metrics = models.JSONField(default=dict)
    evasion_signals = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'behavioral_data'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user_auth']),
            models.Index(fields=['classification']),
            models.Index(fields=['created_at']),
            models.Index(fields=['suspicious_flag']),
        ]
        ordering = ['-created_at']
    
class UserBaselineBehavior(models.Model):
    """
    Model to store user baseline behavioral data collected during the initial 20-second period
    """
    user_id = models.CharField(max_length=255, help_text="User identifier (USAI ID or username)" )
    session_id = models.CharField(max_length=100, help_text="Session identifier for the baseline collection")
    baseline_user_behavior = models.JSONField(
        help_text="Complete baseline behavioral data collected during 20-second period"
    )
    
    # Additional baseline metadata
    collection_start_time = models.DateTimeField(help_text="When baseline collection started")
    collection_end_time = models.DateTimeField(help_text="When baseline collection ended")
    collection_duration_ms = models.IntegerField(help_text="Actual collection duration in milliseconds")
    
    # Baseline metrics for quick access
    baseline_metrics = models.JSONField(
        default=dict,
        help_text="Calculated baseline metrics (speeds, frequencies, patterns)"
    )
    
    # Quality indicators
    data_quality_score = models.FloatField(
        default=0.0,
        help_text="Quality score of baseline data (0.0 to 1.0)"
    )
    sufficient_interaction = models.BooleanField(
        default=False,
        help_text="Whether sufficient user interaction was captured"
    )
    
    # Status tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this baseline is currently active for comparison"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_baseline_behavior'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['session_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Baseline for {self.user_id} - Session {self.session_id} - {self.created_at}"
    
    def get_baseline_summary(self):
        """
        Get a summary of the baseline behavior for quick reference
        """
        if not self.baseline_metrics:
            return "No metrics available"
        
        return {
            'duration': f"{self.collection_duration_ms/1000:.1f}s",
            'mouse_movements': self.baseline_metrics.get('mouseMovementCount', 0),
            'key_presses': self.baseline_metrics.get('keyPressCount', 0),
            'clicks': self.baseline_metrics.get('clickCount', 0),
            'avg_mouse_speed': f"{self.baseline_metrics.get('averageMouseSpeed', 0):.2f}",
            'quality_score': f"{self.data_quality_score:.2f}",
            'sufficient_interaction': self.sufficient_interaction
        }

