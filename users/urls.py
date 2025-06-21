from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('update/', views.update_data, name='update_data'),
    path('delete/', views.delete_data, name='delete_data'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.get_profile, name='profile'),
    path('profile/<str:email>/', views.get_profile, name='profile'),
    path('extension/login', views.extension_login_view, name='extension_login_view'),
    path('extension/auto-fill/', views.auto_fill_extension, name='auto-fill-extension'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
