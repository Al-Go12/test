from django.urls import path
from .views import SendOtpView, SignupApiView,AdminLoginView,ForgotPasswordRequestView,ForgotPasswordVerifyOTPView,ForgotPasswordResetView,UserLoginView,CookieTokenRefreshView,UserDetailView,LogoutView


urlpatterns = [
    path("otp/send/", SendOtpView.as_view(), name="otp-send"),
    path("signup/", SignupApiView.as_view(), name="otp-verify"),
   path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"), 
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),   

     path("auth/login/", UserLoginView.as_view(), name="user-login"),   
      path("logout/", LogoutView.as_view(), name="user-login"),  
   
    path('user/', UserDetailView.as_view(), name='user_details'),
     path("auth/forgot-password/request/", ForgotPasswordRequestView.as_view(), name="forgot-password-request"),
    path("auth/forgot-password/verify/", ForgotPasswordVerifyOTPView.as_view(), name="forgot-password-verify"),
    path("auth/forgot-password/reset/", ForgotPasswordResetView.as_view(), name="forgot-password-reset"),    

]
