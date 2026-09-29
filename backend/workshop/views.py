import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.http.multipartparser import MultiPartParser, MultiPartParserError
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .facades import ClientFacade
from .models import WorkOrder, User
from .permissions import roles_required
from .validators import ClientInputError

def user_data(user):
    return {'id': user.id, 'name': user.get_full_name() or user.username, 'role': user.role}


def client_data(client, request):
    """Serializa el cliente para Vue sin filtrar objetos ORM a la capa HTTP."""
    return {
        'id': client.id,
        'full_name': client.full_name,
        'alternate_contact_name': client.alternate_contact_name,
        'age': client.age,
        'birth_date': client.birth_date.isoformat(),
        'personal_phone': client.personal_phone,
        'work_phone': client.work_phone,
        'street': client.street,
        'neighborhood': client.neighborhood,
        'municipality': client.municipality,
        'state': client.state,
        'postal_code': client.postal_code,
        'personal_email': client.personal_email,
        'work_email': client.work_email,
        'photo_url': request.build_absolute_uri(client.photo.url) if client.photo else None,
        'created_at': client.created_at.isoformat(),
    }

@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'csrfToken': get_token(request)})

@require_POST
def login_view(request):
    payload = json.loads(request.body or '{}')
    user = authenticate(request, username=payload.get('username', ''), password=payload.get('password', ''))
    if not user:
        return JsonResponse({'detail': 'Credenciales inválidas.'}, status=401)
    if not user.is_active:
        return JsonResponse({'detail': 'Cuenta inactiva.'}, status=403)
    login(request, user)
    return JsonResponse({'user': user_data(user)})

@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({'detail': 'Sesión cerrada.'})

@require_GET
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'No autenticado.'}, status=401)
    return JsonResponse({'user': user_data(request.user)})

@require_GET
def orders(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'No autenticado.'}, status=401)
    values = WorkOrder.objects.select_related('technician').order_by('-created_at')[:20]
    return JsonResponse({'orders': [{'folio': x.folio, 'vehicle': x.vehicle, 'service': x.service, 'status': x.status, 'technician': x.technician.get_full_name() if x.technician else 'Sin asignar'} for x in values]})


@require_GET
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def clients(request):
    """Consulta REST de clientes disponible sólo para Administración y Recepción."""
    facade = ClientFacade()
    return JsonResponse({'clients': [client_data(client, request) for client in facade.list_clients()]})


@require_POST
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def create_client(request):
    """Registra un cliente desde un formulario multipart; detecta duplicados antes de persistir."""
    facade = ClientFacade()
    try:
        result = facade.register(request.POST, request.FILES.get('photo'))
    except ClientInputError as error:
        return JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': error.fields}, status=422)

    serialized = client_data(result.client, request)
    if not result.created:
        return JsonResponse({
            'detail': 'Ya existe un cliente con el mismo teléfono, correo personal o nombre y fecha de nacimiento.',
            'client': serialized,
        }, status=409)
    return JsonResponse({'detail': 'Registro guardado exitosamente', 'client': serialized}, status=201)


@require_http_methods(['GET', 'PUT'])
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def client_detail(request, client_id):
    """Entrega el detalle o aplica una actualización multipart REST a un cliente autorizado."""
    facade = ClientFacade()
    if request.method == 'GET':
        client = facade.get_client(client_id)
        if not client:
            return JsonResponse({'detail': 'Cliente no encontrado.'}, status=404)
        return JsonResponse({'client': client_data(client, request)})

    try:
        data, files = MultiPartParser(
            request.META, request, request.upload_handlers, request.encoding,
        ).parse()
    except MultiPartParserError:
        return JsonResponse({'detail': 'No fue posible procesar el formulario enviado.'}, status=400)
    try:
        result = facade.update(client_id, data, files.get('photo'))
    except ClientInputError as error:
        return JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': error.fields}, status=422)
    if result is None:
        return JsonResponse({'detail': 'Cliente no encontrado.'}, status=404)
    serialized = client_data(result.client, request)
    if not result.created:
        return JsonResponse({
            'detail': 'Ya existe un cliente con el mismo teléfono, correo personal o nombre y fecha de nacimiento.',
            'client': serialized,
        }, status=409)
    return JsonResponse({'detail': 'Cliente actualizado exitosamente', 'client': serialized})

@require_POST
def register(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Solicitud inválida.'}, status=400)
    username = payload.get('username', '').strip()
    first_name = payload.get('first_name', '').strip()
    password = payload.get('password', '')
    if not username or not first_name or not password:
        return JsonResponse({'detail': 'Completa todos los campos.'}, status=400)
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({'detail': 'Este usuario ya está registrado.'}, status=409)
    if len(password) < 12:
        return JsonResponse({'detail': 'La contraseña debe tener al menos 12 caracteres.'}, status=400)
    user = User.objects.create_user(username=username, first_name=first_name, password=password, role=User.Role.VIEWER)
    login(request, user)
    return JsonResponse({'user': user_data(user)}, status=201)
