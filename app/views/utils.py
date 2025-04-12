import logging
from ..models import UserRegistration, Batch, WhatsAppMessage
from .whatsapp_views import WhatsAppService

logger = logging.getLogger(__name__)

def _send_whatsapp_approval_notification(user: UserRegistration, batch: Batch):
    """
    Envia a notificação de aprovação via WhatsApp e salva o registro da mensagem.
    Retorna a resposta da API do WhatsApp.
    """
    whatsapp_service = WhatsAppService()
    response = whatsapp_service.send_batch_notification(user, batch)

    # Salva o registro da mensagem enviada
    message_content = batch.message_template.replace('{nome}', user.name)
    message_content = message_content.replace('{data}', batch.date.strftime('%d/%m/%Y'))
    message_content = message_content.replace('{hora}', batch.time.strftime('%H:%M'))

    # Extrai o ID da mensagem da resposta da API para referência futura
    wamid = None
    if isinstance(response, dict) and 'messages' in response and response['messages']:
        # A API retorna algo como {"messages": [{"id": "wamid.XXXX"}]}
        wamid = response['messages'][0]['id'] if response['messages'] else None
    
    WhatsAppMessage.objects.create(
        recipient=user.phone_number,
        message=message_content,
        status='sent', # Assumindo 'sent', será atualizado via webhook
        user=user,
        wamid=wamid  # Salva o ID da mensagem para rastreamento de status
    )
    logger.info(f"Notificação de lote enviada para {user.phone_number}. Resposta API: {response}")
    return response