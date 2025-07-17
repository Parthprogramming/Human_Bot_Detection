from django.urls import path
from .views import analyze_user , predict_user_type

urlpatterns = [
    path("analyze-user/", analyze_user, name="analyze_user"),
    path("predict-user-type/", predict_user_type , name="predict_user_type"),
]
