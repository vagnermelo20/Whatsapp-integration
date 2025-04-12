from django.urls import path, include
from .urls_public import public_urlpatterns 
from .urls_admin import admin_urlpatterns
from .urls_whatsapp import whatsapp_urlpatterns

# Todos os padrões de URL combinados
# Adicionando prefixos apropriados para as URLs
urlpatterns = public_urlpatterns + [
    path('admin/', include(admin_urlpatterns)),
    path('admin/whatsapp/', include(whatsapp_urlpatterns)),
    # Mantendo também as URLs de WhatsApp na raiz para compatibilidade
    path('', include(whatsapp_urlpatterns)),
]