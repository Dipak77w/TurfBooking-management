from django.urls import path
from . import views

urlpatterns = [
    # Customer Auth
    path('customer/login/', views.customer_login_view, name='customer_login'),
    path('customer/register/', views.customer_register_view, name='customer_register'),
    path('customer/profile/', views.customer_profile_view, name='customer_profile'),
    
    # Owner (Admin) Auth
    path('owner/login/', views.owner_login_view, name='owner_login'),
    path('owner/register/', views.owner_register_view, name='owner_register'),
    path('owner/settings/', views.owner_settings_view, name='owner_settings'),
    
    # Common
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
]
