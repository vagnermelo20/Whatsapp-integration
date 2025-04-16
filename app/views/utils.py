import logging
from ..models import UserRegistration, Batch, WhatsAppMessage
from .whatsapp_views import WhatsAppService

logger = logging.getLogger(__name__)

def format_phone(number):
    """
    Format a phone number to (xx)xxxxx-xxxx pattern
    Example: '22998765432' becomes '(22)99876-5432'
    """
    if not number:
        return ""
    
    # Remove any non-digit character
    clean_number = ''.join(filter(str.isdigit, number))
    
    # Check if it might be starting with country code (e.g., 55 for Brazil)
    if len(clean_number) > 11 and clean_number.startswith('55'):
        clean_number = clean_number[2:]  # Remove country code
        
    # Format the number
    if len(clean_number) == 11:  # With 9-digit (mobile)
        return f"({clean_number[:2]}){clean_number[2:7]}-{clean_number[7:]}"
    elif len(clean_number) == 10:  # Without 9-digit (landline)
        return f"({clean_number[:2]}){clean_number[2:6]}-{clean_number[6:]}"
    else:
        # Return original if format doesn't match expected patterns
        return number

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