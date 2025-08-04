from django.urls import path
from . import views  # Or specific views if needed

urlpatterns = [
    path('detect/', views.detect_http_bot, name='detect-http-bot'),
    path('detection/', views.get_detection_stats, name='get-detection'),
]
