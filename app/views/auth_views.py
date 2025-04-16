from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
import logging
from ..models import UserRegistration

logger = logging.getLogger(__name__)

def landing_page(request: HttpRequest):
    """Exibe a página inicial com opções de login e cadastro."""
    # Se o usuário já estiver logado, redireciona para o dashboard
    if request.user.is_authenticated:
        # Verifica se é admin/staff para redirecionar para o painel correto
        if request.user.is_staff or request.user.is_superuser:
             return redirect('admin_dashboard') # Nome da URL do painel admin
        else:
             # Redirecionar para um painel de usuário comum, se existir,
             # ou para o login/landing page se não houver painel de usuário.
             # Por enquanto, vamos redirecionar para o dashboard admin como padrão se logado.
             return redirect('admin_dashboard') # Ajuste se tiver painel de usuário não-admin

    return render(request, 'landing_page.html')

@csrf_exempt # Necessário se o formulário não incluir token CSRF via JS
def register_user(request: HttpRequest):
    """Registra um novo usuário com status pendente."""
    if request.method == 'GET':
        return render(request, 'register.html')

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            phone_number = request.POST.get('phone_number')
            age = request.POST.get('age')
            bairro = request.POST.get('bairro')
            education = request.POST.get('education')
            study_period = request.POST.get('study_period')
            desired_course = request.POST.get('desired_course')

            if not name or not phone_number:
                return JsonResponse({'error': 'Nome e telefone são obrigatórios.'}, status=400)

            user = UserRegistration.objects.create(
                name=name,
                phone_number=phone_number,
                age=age if age else None,
                bairro=bairro if bairro else None,
                education=education if education else None,
                study_period=study_period if study_period else None,
                desired_course=desired_course if desired_course else None
                # status='pending' é o padrão
            )
            logger.info(f"Usuário registrado: {user.id} - {user.name}")
            return JsonResponse({'message': 'Usuário registrado com sucesso!', 'user_id': user.id})
        except Exception as e:
            logger.error(f"Erro ao registrar usuário: {e}")
            return JsonResponse({'error': 'Ocorreu um erro interno.'}, status=500)

    return HttpResponseNotAllowed(['GET', 'POST'])

def custom_logout(request):
    """Realiza o logout do usuário e redireciona para a página inicial."""
    logout(request)
    return redirect('landing_page')