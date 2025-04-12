from django.urls import path
from django.contrib.auth import views as auth_views
from ..views import auth_views as custom_auth_views

public_urlpatterns = [
    path('', custom_auth_views.landing_page, name='landing_page'),
    path('register/', custom_auth_views.register_user, name='register_user'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True,
        next_page='admin_dashboard'  # Redireciona para o dashboard após login
    ), name='login'),
    path('logout/', custom_auth_views.custom_logout, name='logout'),
]