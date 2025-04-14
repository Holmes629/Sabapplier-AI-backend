from django.urls import path
from . import views

urlpatterns = [
    path('auto-fill/', views.auto_fill, name='auto-fill'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.get_profile, name='profile'),
    path('profile/<str:email>/', views.get_profile, name='profile'),
    path('extension/auto-fill/', views.auto_fill_extension, name='auto-fill-extension'),
] 