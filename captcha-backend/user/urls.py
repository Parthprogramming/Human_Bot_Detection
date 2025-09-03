from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('signup/', views.sign_up, name='signup'),
    path('signin/', views.sign_in, name='signin'),
    path('store-baseline-behavior/', views.handle_baseline_storage, name='store_baseline_behavior'),
    path('behavioral-analysis/', views.analyze_behavioral_data, name='behavioral_analysis'),
]
