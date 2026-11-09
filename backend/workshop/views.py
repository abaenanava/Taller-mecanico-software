import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.http.multipartparser import MultiPartParser, MultiPartParserError
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .facades import ClientFacade, PostalCodeFacade, StatusFacade, VehicleFacade, VehicleUpdateConflict, WorkshopFacade
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
        'workshop_id': client.workshop_id,
        'workshop_name': client.workshop.name if client.workshop_id else None,
        'estatus_id': client.estatus_id,
        'status': client.estatus.name.upper(),
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
    page = max(int(request.GET.get('page', 1)), 1)
    workshop_id = request.GET.get('workshop_id') or None
    status = request.GET.get('status') or None
    order = request.GET.get('order', 'full_name')
    direction = request.GET.get('direction', 'asc')
    items, total = ClientFacade().list_clients(workshop_id=workshop_id, status=status, order=order, direction=direction, page=page)
    return JsonResponse({'clients': [client_data(client, request) for client in items], 'total': total, 'pages': max((total + 9) // 10, 1), 'page': page, 'order': order, 'direction': direction})


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

def status_data(item):
    return {'id': item.id, 'name': item.name, 'description': item.description, 'created_at': item.created_at.isoformat()}

@require_http_methods(['GET', 'POST'])
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def statuses(request):
    facade = StatusFacade()
    if request.method == 'GET':
        items, total = facade.list(order=request.GET.get('order', 'name'), direction=request.GET.get('direction', 'asc'), page=request.GET.get('page', 1))
        return JsonResponse({'statuses': [status_data(item) for item in items], 'total': total, 'pages': max((total + 9) // 10, 1), 'page': max(int(request.GET.get('page', 1)), 1)})
    try: result = facade.create(json.loads(request.body or '{}'))
    except (json.JSONDecodeError, ClientInputError) as error:
        return JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': getattr(error, 'fields', {})}, status=422)
    if not result.created: return JsonResponse({'detail': 'Ya existe un estatus con ese nombre.', 'status': status_data(result.entity)}, status=409)
    return JsonResponse({'detail': 'Estatus creado exitosamente.', 'status': status_data(result.entity)}, status=201)

@require_http_methods(['GET', 'PUT', 'DELETE'])
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def status_detail(request, status_id):
    facade = StatusFacade()
    if request.method == 'GET':
        item = facade.get(status_id)
        return JsonResponse({'detail': 'Estatus no encontrado.'}, status=404) if not item else JsonResponse({'status': status_data(item)})
    if request.method == 'DELETE':
        deleted, detail = facade.delete(status_id, request.user)
        return JsonResponse({'detail': detail or 'Estatus eliminado exitosamente.'}, status=400 if not deleted else 200)
    try: result = facade.update(status_id, json.loads(request.body or '{}'))
    except (json.JSONDecodeError, ClientInputError) as error: return JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': getattr(error, 'fields', {})}, status=422)
    if result is None: return JsonResponse({'detail': 'Estatus no encontrado.'}, status=404)
    if not result.created: return JsonResponse({'detail': 'Ya existe un estatus con ese nombre.', 'status': status_data(result.entity)}, status=409)
    return JsonResponse({'detail': 'Estatus actualizado exitosamente.', 'status': status_data(result.entity)})

def vehicle_data(item):
    return {'id': item.id, 'plate': item.plate, 'brand': item.brand, 'model': item.model, 'vin': item.vin, 'year': item.year, 'version': item.version, 'color': item.color, 'mileage': item.mileage, 'status': item.estatus.name, 'created_at': item.created_at.isoformat()}

@require_http_methods(['GET', 'POST'])
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def client_vehicles(request, client_id):
    facade = VehicleFacade()
    if request.method == 'GET':
        items, total = facade.list_for_client(client_id, order=request.GET.get('order', 'created_at'), direction=request.GET.get('direction', 'desc'), page=request.GET.get('page', 1))
        return JsonResponse({'vehicles': [vehicle_data(item) for item in items], 'total': total, 'pages': max((total + 9) // 10, 1), 'page': max(int(request.GET.get('page', 1)), 1)})
    try: result = facade.create(client_id, json.loads(request.body or '{}'))
    except (json.JSONDecodeError, ClientInputError) as error: return JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': getattr(error, 'fields', {})}, status=422)
    if not result.created: return JsonResponse({'detail': 'Ya existe un vehículo con ese VIN o placa.', 'vehicle': vehicle_data(result.entity)}, status=409)
    return JsonResponse({'detail': 'Vehículo registrado exitosamente.', 'vehicle': vehicle_data(result.entity)}, status=201)

@require_GET
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def postal_code(request, cp):
    result = PostalCodeFacade().lookup(cp)
    return JsonResponse({'verified': bool(result), 'data': result})

def workshop_data(workshop, request):
    return {'id': workshop.id, 'name': workshop.name, 'street': workshop.street, 'neighborhood': workshop.neighborhood, 'municipality': workshop.municipality, 'state': workshop.state, 'postal_code': workshop.postal_code, 'business_name': workshop.business_name, 'phone': workshop.phone, 'rfc': workshop.rfc, 'contact_email': workshop.contact_email, 'photo_url': request.build_absolute_uri(workshop.photo.url) if workshop.photo else None}

@require_http_methods(['GET', 'POST'])
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def workshops(request):
    """Lista talleres o registra uno; Administración y Recepción pueden gestionarlos."""
    facade = WorkshopFacade()
    if request.method == 'GET': return JsonResponse({'workshops': [workshop_data(item, request) for item in facade.list()]})
    try: result = facade.register(request.POST, request.FILES.get('photo'))
    except ClientInputError as error: return JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': error.fields}, status=422)
    if not result.created: return JsonResponse({'detail': 'Ya existe un taller con ese RFC o dirección.', 'workshop': workshop_data(result.client, request)}, status=409)
    return JsonResponse({'detail': 'Taller guardado exitosamente', 'workshop': workshop_data(result.client, request)}, status=201)

@require_POST
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def suspend_client(request, client_id):
    client, detail = ClientFacade().suspend(client_id)
    if not client: return JsonResponse({'detail': detail}, status=400 if detail != 'Cliente no encontrado.' else 404)
    return JsonResponse({'detail': 'Cliente suspendido exitosamente', 'client': client_data(client, request)})

@require_POST
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def activate_client(request, client_id):
    """Reactiva al cliente solicitado; Administración y Recepción pueden cambiar su estatus."""
    client, detail = ClientFacade().activate(client_id)
    if not client: return JsonResponse({'detail': detail}, status=400 if detail != 'Cliente no encontrado.' else 404)
    return JsonResponse({'detail': 'Cliente activado exitosamente', 'client': client_data(client, request)})

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


@require_GET
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def vehicle_lookup(request):
    """Consulta exacta; expone solo la identidad del cliente y taller asociados."""
    try:
        vehicle = VehicleFacade().lookup(request.GET)
    except ClientInputError as error:
        response = JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': error.fields}, status=422)
    else:
        if vehicle is None:
            response = JsonResponse({'detail': 'Vehículo no encontrado.'}, status=404)
        else:
            data = vehicle_data(vehicle)
            data['client'] = {'id': vehicle.client_id, 'full_name': vehicle.client.full_name}
            data['workshop'] = {'id': vehicle.client.workshop_id, 'name': vehicle.client.workshop.name}
            response = JsonResponse({'vehicle': data})
    response['Cache-Control'] = 'private, no-store'
    return response


@require_http_methods(['PATCH'])
@roles_required(User.Role.ADMIN, User.Role.RECEPTION)
def vehicle_update(request, vehicle_id):
    """Modifica únicamente campos editables; ID, VIN y asociaciones son inmutables."""
    if not 1 <= vehicle_id <= (1 << 63) - 1:
        response = JsonResponse({'detail': 'Vehículo no encontrado.'}, status=404)
    elif request.content_type != 'application/json':
        response = JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': {'body': 'Envía los datos como application/json.'}}, status=422)
    else:
        try:
            payload = json.loads(request.body)
            vehicle = VehicleFacade().update(vehicle_id, payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            response = JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': {'body': 'El cuerpo debe contener un objeto JSON válido.'}}, status=422)
        except ClientInputError as error:
            response = JsonResponse({'detail': 'Revisa los campos marcados.', 'fields': error.fields}, status=422)
        except VehicleUpdateConflict:
            response = JsonResponse({'detail': 'La placa ya está registrada en otro vehículo.', 'fields': {'plate': 'Esta placa ya está registrada.'}}, status=409)
        else:
            if vehicle is None:
                response = JsonResponse({'detail': 'Vehículo no encontrado.'}, status=404)
            else:
                data = vehicle_data(vehicle)
                data['client'] = {'id': vehicle.client_id, 'full_name': vehicle.client.full_name}
                data['workshop'] = {'id': vehicle.client.workshop_id, 'name': vehicle.client.workshop.name}
                response = JsonResponse({'detail': 'Vehículo actualizado exitosamente.', 'vehicle': data})
    response['Cache-Control'] = 'private, no-store'
    return response
