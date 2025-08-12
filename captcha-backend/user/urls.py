from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('signup/', views.sign_up, name='signup'),
    path('signin/', views.sign_in, name='signin'),
    path('session/<str:session_id>/', views.check_session, name='check_session'),
    path('baseline-storage/', views.handle_baseline_storage, name='baseline_storage'),
    path('behavioral-analysis/', views.analyze_behavioral_data, name='behavioral_analysis'),
    path('behavioral-analytics/<str:session_id>/', views.get_behavioral_analytics, name='behavioral_analytics'),
]
