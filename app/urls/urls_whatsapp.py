from django.urls import path
from django.views.generic import RedirectView
from ..views import whatsapp_views

whatsapp_urlpatterns = [
    # Redirecionar a URL raiz para o dashboard
    path('', RedirectView.as_view(pattern_name='whatsapp_dashboard'), name='whatsapp_root'),
    path('dashboard/', whatsapp_views.whatsapp_dashboard, name='whatsapp_dashboard'),
    path('send/', whatsapp_views.send_whatsapp_message, name='send_whatsapp_message'),
    path('webhook/', whatsapp_views.whatsapp_webhook, name='whatsapp_webhook'),
    path('delete-message/<int:message_id>/', whatsapp_views.delete_whatsapp_message, name='delete_whatsapp_message'),
    path('delete-user/<int:user_id>/', whatsapp_views.delete_user, name='delete_user'),
]