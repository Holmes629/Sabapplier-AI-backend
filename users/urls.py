from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # OTP endpoints
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
    # Forgot Password endpoints
    path('forgot-password/send-otp/', views.send_forgot_password_otp, name='send_forgot_password_otp'),
    path('forgot-password/reset/', views.reset_password, name='reset_password'),

    # Google OAuth endpoint
    path('google-signup/', views.google_signup, name='google_signup'),

    # User management endpoints
    path('register/', views.register, name='register'),
    path('update/', views.update_data, name='update_data'),
    path('delete/', views.delete_data, name='delete_data'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.get_profile, name='profile'),
    path('profile/<str:email>/', views.get_profile, name='profile'),
    path('extension/login', views.extension_login_view, name='extension_login_view'),
    path('extension/auto-fill/', views.auto_fill_extension, name='auto-fill-extension'),
    
    # Data sharing endpoints
    path('share/send/', views.share_data_with_friend, name='share_data_with_friend'),
    path('share/respond/', views.respond_to_share_request, name='respond_to_share_request'),
    path('share/stop/', views.stop_data_sharing, name='stop_data_sharing'),
    path('share/get-data/', views.get_shared_data, name='get_shared_data'),
    path('share/refresh-data/', views.refresh_shared_data, name='refresh_shared_data'),
    path('notifications/', views.get_user_notifications, name='get_user_notifications'),
    path('shares/', views.get_user_shares, name='get_user_shares'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
