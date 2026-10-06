"""Capa de acceso a datos para clientes.

Las vistas y la fachada no hacen consultas ORM directamente. Esta clase concentra
los criterios de búsqueda para que puedan cambiar sin afectar la API ni Vue.
"""
from django.db.models import Q

from .models import Client, PostalCode, Workshop


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

    def list(self, *, workshop_id=None, status=None, order='full_name', direction='asc', page=1, page_size=10):
        """Obtiene clientes para la vista de recepción, sin exponer el ORM al controlador."""
        query = Client.objects.select_related('workshop').all()
        if workshop_id:
            query = query.filter(workshop_id=workshop_id)
        if status:
            query = query.filter(status=status)
        safe_order = {'full_name', 'created_at'}
        ordering = ('-' if direction == 'desc' else '') + (order if order in safe_order else 'full_name')
        query = query.order_by(ordering, 'id')
        total = query.count()
        start = (max(page, 1) - 1) * page_size
        return query[start:start + page_size], total

    def get_by_id(self, client_id):
        """Obtiene un cliente por llave primaria o devuelve ``None`` si no existe."""
        return Client.objects.filter(pk=client_id).first()

    def update(self, client, **client_data):
        """Actualiza únicamente la entidad ya validada y devuelve su estado persistido."""
        for field, value in client_data.items():
            setattr(client, field, value)
        client.save()
        return client


class PostalCodeRepository:
    def find(self, cp):
        return PostalCode.objects.filter(cp=cp).order_by('neighborhood')

    def matches(self, cp, neighborhood, municipality, state):
        return PostalCode.objects.filter(cp=cp, neighborhood__iexact=neighborhood, municipality__iexact=municipality, state__iexact=state).exists()


class WorkshopRepository:
    def find_duplicate(self, *, rfc, name, street, neighborhood, municipality, state, postal_code, exclude_id=None, **_unused):
        matches = Workshop.objects.filter(Q(rfc__iexact=rfc) | Q(name__iexact=name, street__iexact=street, neighborhood__iexact=neighborhood, municipality__iexact=municipality, state__iexact=state, postal_code=postal_code))
        if exclude_id:
            matches = matches.exclude(pk=exclude_id)
        return matches.order_by('-created_at').first()

    def save(self, **data):
        return Workshop.objects.create(**data)

    def list(self):
        return Workshop.objects.order_by('name')

    def get_by_id(self, workshop_id):
        return Workshop.objects.filter(pk=workshop_id).first()
