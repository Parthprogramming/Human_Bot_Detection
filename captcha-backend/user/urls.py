from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('signup/', views.sign_up, name='signup'),
    path('signin/', views.sign_in, name='signin'),
    path('baseline-storage/', views.handle_baseline_storage, name='baseline_storage'),
    path('behavioral-analysis/', views.analyze_behavioral_data, name='behavioral_analysis')
]
