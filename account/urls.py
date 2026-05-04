from django.urls import path
from .views import RegisterView,RegisterVerifyOTPView,LoginAPIView,CustomTokenRefresView,ChangePasswordApiView,ForgetPasswordSendOTP, ForgetPasswordVerifyOTP, ForgetPasswordReset ,ProfileAPIView,PrivacyPolicyView,TermsAndConditionsView
from . import views




urlpatterns = [

    #User Authentication Url
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-registration/', views.RegisterVerifyOTPView.as_view(), name='verify-registration'),
    path('login/',LoginAPIView.as_view(),name='login'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('refresh/',CustomTokenRefresView.as_view(),name='token_refresh'),
    path('password-change/',ChangePasswordApiView.as_view(),name='change-password'),

     #Forget Password URLs
    path("forget-password/send-otp/", ForgetPasswordSendOTP.as_view(), name="forget-password-send-otp"),
    path("forget-password/verify-otp/", ForgetPasswordVerifyOTP.as_view(), name="forget-password-verify-otp"),
    path("forget-password/reset/", ForgetPasswordReset.as_view(), name="forget-password-reset"),

    #profile
    path('profile/', ProfileAPIView.as_view(), name='profile'),

    #privacy policy and terms and conditions
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('privacy-policy', PrivacyPolicyView.as_view()),
    path('terms-and-conditions/', TermsAndConditionsView.as_view(), name='terms-and-conditions'),
    path('terms-and-conditions', TermsAndConditionsView.as_view()),

]