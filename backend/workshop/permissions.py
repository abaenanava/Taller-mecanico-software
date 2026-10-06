"""Reglas de autorización reutilizables para la API del taller."""
from functools import wraps

from django.http import JsonResponse


def roles_required(*roles):
    """Requiere sesión y uno de los roles indicados; superusuarios conservan acceso administrativo."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'detail': 'Inicia sesión para continuar.'}, status=401)
            if not (request.user.is_superuser or request.user.role in roles):
                return JsonResponse({'detail': 'No tienes autorización para registrar o consultar clientes.'}, status=403)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
