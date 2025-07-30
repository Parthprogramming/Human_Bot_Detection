from django.db import models
from django.utils import timezone
import json

class HttpBotDetection(models.Model):
    
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(default=timezone.now)
    user_agent = models.TextField()
    
    
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    request_interval = models.FloatField(null=True, blank=True)  # seconds between requests
    
    
    payload_schema_valid = models.BooleanField(default=True)
    cookies_present = models.BooleanField(default=False)
    
    
    confidence = models.FloatField()  # 0.0 to 1.0
    classification = models.CharField(max_length=255 , null=True, blank=True) 
    
    suspicious_headers = models.JSONField(default=list, blank=True)
    request_fingerprint = models.CharField(max_length=64, null=True, blank=True)
    session_id = models.CharField(max_length=64, null=True, blank=True)
    
    
    is_headless_browser = models.BooleanField(default=False)
    automation_detected = models.BooleanField(default=False)
    rate_limit_exceeded = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'httpbot_detection'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.ip_address} - {self.classification} ({self.confidence:.2f}) - {self.timestamp}"
