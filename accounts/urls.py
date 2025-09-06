from django.urls import path
from .views import SendOtpView, VerifyOtpView,AdminLoginView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("otp/send/", SendOtpView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOtpView.as_view(), name="otp-verify"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"), 
     path("admin/login/", AdminLoginView.as_view(), name="admin-login"),  # ✅
]
