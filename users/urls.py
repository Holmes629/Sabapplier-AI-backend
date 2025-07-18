from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import contact_us

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
    path('check-access/', views.check_access_status, name='check_access_status'),
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
    path('notifications/mark-as-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    
    # Learning functionality endpoints
    path('extension/save-learned-data/', views.save_learned_form_data, name='save_learned_data'),
    path('extension/process-learned-data/', views.process_learned_data, name='process_learned_data'),
    path('extension/get-learned-data/', views.get_learned_data, name='get_learned_data'),
    path('extension/delete-learned-data/', views.delete_learned_data, name='delete_learned_data'),
    
    # New popup mode and smart comparison endpoints
    path('extension/toggle-popup-mode/', views.toggle_popup_mode, name='toggle_popup_mode'),
    path('extension/get-popup-mode/', views.get_popup_mode, name='get_popup_mode'),
    path('extension/get-autofill-data/', views.get_user_autofill_data, name='get_user_autofill_data'),
    path('extension/compare-form-data/', views.compare_form_data, name='compare_form_data'),
    path('extension/user-stats/', views.get_user_stats, name='get_user_stats'),

    # Shared accounts endpoint
    path('shared-accounts/', views.get_shared_accounts, name='get_shared_accounts'),
    
    # Contact us endpoint
    path('contact-us/', contact_us, name='contact-us'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
