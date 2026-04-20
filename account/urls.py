from django.urls import path
from .views import RegisterView,LoginAPIView,CustomTokenRefresView,ChangePasswordApiView,ForgetPasswordSendOTP, ForgetPasswordVerifyOTP, ForgetPasswordReset ,ProfileAPIView




urlpatterns = [

    #User Authentication Url
    path('register/', RegisterView.as_view(), name='register'),
    path('login/',LoginAPIView.as_view(),name='login'),
    path('refresh/',CustomTokenRefresView.as_view(),name='token_refresh'),
    path('password-change/',ChangePasswordApiView.as_view(),name='change-password'),

     #Forget Password URLs
    path("forget-password/send-otp/", ForgetPasswordSendOTP.as_view(), name="forget-password-send-otp"),
    path("forget-password/verify-otp/", ForgetPasswordVerifyOTP.as_view(), name="forget-password-verify-otp"),
    path("forget-password/reset/", ForgetPasswordReset.as_view(), name="forget-password-reset"),

    #profile
    path('profile/', ProfileAPIView.as_view(), name='profile'),

]