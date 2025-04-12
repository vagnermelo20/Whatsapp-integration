from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpRequest, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import logging
import requests

from ..models import UserRegistration, WhatsAppMessage, Batch, BatchAssignment

logger = logging.getLogger(__name__)

# Implementação da classe WhatsAppService para substituir o módulo removido
class WhatsAppService:
    """
    Serviço para enviar mensagens usando a API do WhatsApp Cloud.
    """
    def __init__(self):
        self.base_url = settings.WHATSAPP_API.get('BASE_URL')
        self.api_version = settings.WHATSAPP_API.get('VERSION')
        self.phone_number_id = settings.WHATSAPP_API.get('PHONE_NUMBER_ID')
        self.access_token = settings.WHATSAPP_API.get('ACCESS_TOKEN')

    def send_message(self, recipient_number, message_text):
        """
        Envia uma mensagem de texto para o destinatário.
        
        Args:
            recipient_number: número de telefone do destinatário
            message_text: conteúdo da mensagem
            
        Returns:
            Resposta da API do WhatsApp como dicionário
        """
        # Assegura que o número está no formato correto (sem + ou espaços)
        recipient_number = recipient_number.replace('+', '').replace(' ', '')
        
        endpoint = f"{self.base_url}{self.api_version}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': recipient_number,
            'type': 'text',
            'text': {'body': message_text}
        }
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()  # Lança exceção se o status for de erro
            return response.json()  # Retorna a resposta como dicionário
        except requests.RequestException as e:
            logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
            # Pode-se optar por relançar a exceção ou retornar um dicionário de erro
            return {'error': str(e)}

    def send_batch_notification(self, user, batch):
        """
        Envia notificação de aprovação do lote para um usuário.
        
        Args:
            user: Objeto UserRegistration do destinatário
            batch: Objeto Batch com informações do agendamento
            
        Returns:
            Resposta da API do WhatsApp como dicionário
        """
        # Personaliza a mensagem com informações do usuário e do lote
        message = batch.message_template
        message = message.replace('{nome}', user.name)
        message = message.replace('{data}', batch.date.strftime('%d/%m/%Y'))
        message = message.replace('{hora}', batch.time.strftime('%H:%M'))
        
        # Usa o método send_message para enviar
        return self.send_message(user.phone_number, message)

@login_required
def whatsapp_dashboard(request: HttpRequest):
    """Exibe o painel para enviar mensagens WhatsApp e ver histórico."""
    approved_users = UserRegistration.objects.filter(status='approved').order_by('name')
    # Exibe as últimas 50 mensagens (enviadas e recebidas)
    messages = WhatsAppMessage.objects.all().order_by('-timestamp')[:50]

    context = {
        'approved_users': approved_users,
        'messages': messages
    }
    return render(request, 'whatsapp_dashboard.html', context)

@csrf_exempt
@login_required
def send_whatsapp_message(request: HttpRequest):
    """Envia uma mensagem WhatsApp avulsa a partir do painel."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recipient = data.get('recipient')
            message_text = data.get('message')

            if not recipient or not message_text:
                return JsonResponse({'success': False, 'error': 'Destinatário e mensagem são obrigatórios.'}, status=400)

            # Envia a mensagem usando o serviço
            whatsapp_service = WhatsAppService()
            response = whatsapp_service.send_message(recipient, message_text)
            logger.info(f"Mensagem avulsa enviada para {recipient}. Resposta API: {response}")

            # Tenta associar a mensagem a um usuário existente (opcional)
            user = UserRegistration.objects.filter(phone_number=recipient).first()

            # Salva o registro da mensagem enviada
            message = WhatsAppMessage.objects.create(
                recipient=recipient,
                message=message_text,
                status='sent', # Status inicial, pode ser atualizado pelo webhook
                user=user # Pode ser None se o número não estiver cadastrado
            )

            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'api_response': response # Retorna a resposta da API para debug/info
            })

        except json.JSONDecodeError:
            logger.error("Erro ao decodificar JSON em send_whatsapp_message")
            return JsonResponse({'success': False, 'error': 'Requisição inválida.'}, status=400)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WhatsApp avulsa: {e}")
            return JsonResponse({'success': False, 'error': 'Ocorreu um erro interno.'}, status=500)

    return HttpResponseNotAllowed(['POST'])

@csrf_exempt
def whatsapp_webhook(request: HttpRequest):
    """Recebe notificações (mensagens, status) da API do WhatsApp."""
    if request.method == 'GET':
        # Processo de verificação do Webhook (necessário na configuração inicial)
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        verify_token = settings.WHATSAPP_API.get('VERIFY_TOKEN') # Pega do settings

        if mode == 'subscribe' and token == verify_token:
            logger.info("Webhook verificado com sucesso!")
            return HttpResponse(challenge, status=200)
        else:
            logger.warning(f"Falha na verificação do Webhook. Modo: {mode}, Token recebido: {token}")
            return HttpResponse('Falha na verificação', status=403)

    elif request.method == 'POST':
        # Processa notificações recebidas (mensagens, atualizações de status)
        try:
            data = json.loads(request.body.decode('utf-8'))
            logger.debug(f"Webhook recebido: {json.dumps(data, indent=2)}") # Log detalhado para debug

            # Estrutura esperada da Meta para notificações
            if 'entry' in data:
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        metadata = value.get('metadata', {})
                        # Processa mensagens recebidas
                        if 'messages' in value:
                            for message_data in value.get('messages', []):
                                phone_number = message_data.get('from')
                                message_type = message_data.get('type')
                                message_id = message_data.get('id') # ID da mensagem do WhatsApp

                                if message_type == 'text':
                                    message_body = message_data.get('text', {}).get('body', '')
                                    logger.info(f"Mensagem recebida de {phone_number}: {message_body}")

                                    # Tenta encontrar o usuário associado
                                    user = UserRegistration.objects.filter(phone_number=phone_number).first()

                                    # Salva a mensagem recebida no banco
                                    WhatsAppMessage.objects.create(
                                        recipient='system', # Indica que é uma mensagem recebida pela aplicação
                                        message=message_body,
                                        status='received',
                                        user=user, # Associa ao usuário se encontrado
                                        wamid=message_id # Salva o ID da mensagem do WhatsApp para referência
                                    )
                                # Adicionar lógica para outros tipos de mensagem (imagem, áudio, etc.) se necessário

                        # Processa atualizações de status de mensagens enviadas
                        elif 'statuses' in value:
                             for status_data in value.get('statuses', []):
                                 message_wamid = status_data.get('id') # ID da mensagem enviada
                                 status = status_data.get('status') # sent, delivered, read, failed
                                 recipient_phone = status_data.get('recipient_id')
                                 timestamp = status_data.get('timestamp') # Pode ser útil

                                 logger.info(f"Atualização de status para {recipient_phone} (Msg ID: {message_wamid}): {status}")
                                 
                                 # Atualiza o status da mensagem no banco de dados
                                 try:
                                     # Procura a mensagem pelo wamid (ID da mensagem do WhatsApp)
                                     messages = WhatsAppMessage.objects.filter(wamid=message_wamid)
                                     
                                     if messages.exists():
                                         for message in messages:
                                             message.status = status
                                             message.save()
                                             logger.info(f"Status da mensagem {message_wamid} atualizado para {status}")
                                     else:
                                         # Se não encontrar pelo wamid (caso não tenha sido salvo), tenta pelo destinatário
                                         # Esta é uma fallback, mas não garante precisão se houver múltiplas mensagens
                                         recent_message = WhatsAppMessage.objects.filter(
                                             recipient=recipient_phone
                                         ).order_by('-timestamp').first()
                                         
                                         if recent_message:
                                             recent_message.status = status
                                             recent_message.wamid = message_wamid  # Atualiza o ID para referências futuras
                                             recent_message.save()
                                             logger.info(f"Status da mensagem para {recipient_phone} atualizado para {status}")
                                         else:
                                             logger.warning(f"Nenhuma mensagem encontrada para atualização de status: {message_wamid}")
                                 except Exception as e:
                                     logger.error(f"Erro ao atualizar status da mensagem: {e}")

            return HttpResponse('OK', status=200) # Responde à Meta que recebeu a notificação

        except json.JSONDecodeError:
            logger.error("Erro ao decodificar JSON no webhook")
            return HttpResponseBadRequest('Requisição inválida.')
        except Exception as e:
            logger.error(f"Erro ao processar webhook do WhatsApp: {e}", exc_info=True) # Log com traceback
            # Retorna 200 para a Meta não reenviar, mas loga o erro internamente
            return HttpResponse('Erro interno', status=200)

    return HttpResponseNotAllowed(['GET', 'POST'])

@login_required
def delete_whatsapp_message(request: HttpRequest, message_id: int):
    """Exclui uma mensagem do histórico."""
    if request.method == 'POST':
        message = get_object_or_404(WhatsAppMessage, id=message_id)
        message.delete()
        logger.info(f"Mensagem {message_id} excluída com sucesso")
        
        # Redireciona de volta para o dashboard
        return redirect('whatsapp_dashboard')
    
    # Redireciona se não for POST
    return redirect('whatsapp_dashboard')

@login_required
def delete_user(request: HttpRequest, user_id: int):
    """Exclui um usuário e todas suas mensagens."""
    if request.method == 'POST':
        user = get_object_or_404(UserRegistration, id=user_id)
        
        # Verificar se o usuário está associado a algum lote
        batch_assignments = BatchAssignment.objects.filter(user=user)
        if batch_assignments.exists():
            # Remove as atribuições de lote primeiro
            batch_assignments.delete()
        
        # Remove todas as mensagens associadas ao usuário
        WhatsAppMessage.objects.filter(user=user).delete()
        
        # Remove o usuário
        user.delete()
        logger.info(f"Usuário {user_id} excluído com sucesso")
        
        # Redireciona de volta para o dashboard
        return redirect('whatsapp_dashboard')
    
    # Redireciona se não for POST
    return redirect('whatsapp_dashboard')