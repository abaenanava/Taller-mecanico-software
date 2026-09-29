"""Capa de acceso a datos para clientes.

Las vistas y la fachada no hacen consultas ORM directamente. Esta clase concentra
los criterios de búsqueda para que puedan cambiar sin afectar la API ni Vue.
"""
from django.db.models import Q

from .models import Client


class ClientRepository:
    def find_duplicate(self, *, full_name, birth_date, personal_phone, personal_email, exclude_id=None):
        """Busca duplicados y puede excluir al cliente que se está editando."""
        matches = Client.objects.filter(
            Q(personal_phone=personal_phone)
            | Q(personal_email__iexact=personal_email)
            | Q(full_name__iexact=full_name, birth_date=birth_date)
        )
        if exclude_id:
            matches = matches.exclude(pk=exclude_id)
        return matches.order_by('-created_at').first()

    def save(self, **client_data):
        """Persiste un cliente validado por la fachada."""
        return Client.objects.create(**client_data)

    def list(self):
        """Obtiene clientes para la vista de recepción, sin exponer el ORM al controlador."""
        return Client.objects.all()

    def get_by_id(self, client_id):
        """Obtiene un cliente por llave primaria o devuelve ``None`` si no existe."""
        return Client.objects.filter(pk=client_id).first()

    def update(self, client, **client_data):
        """Actualiza únicamente la entidad ya validada y devuelve su estado persistido."""
        for field, value in client_data.items():
            setattr(client, field, value)
        client.save()
        return client
