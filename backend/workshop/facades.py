"""Fachada del caso de uso: registro y consulta de clientes."""
from dataclasses import dataclass

from django.db import IntegrityError

from .repositories import ClientRepository
from .validators import ClientRegistrationValidator


@dataclass
class ClientRegistrationResult:
    client: object
    created: bool


class ClientFacade:
    """Orquesta validación y repositorio; la capa HTTP sólo traduce solicitudes/respuestas."""

    def __init__(self, repository=None, validator=None):
        self.repository = repository or ClientRepository()
        self.validator = validator or ClientRegistrationValidator()

    def register(self, raw_data, photo):
        """Crea un cliente tras validar y comprobar las tres reglas de unicidad."""
        data = self.validator.validate(raw_data, photo)
        existing = self._find_duplicate(data)
        if existing:
            return ClientRegistrationResult(client=existing, created=False)
        try:
            return ClientRegistrationResult(client=self.repository.save(photo=photo, **data), created=True)
        except IntegrityError:
            return ClientRegistrationResult(client=self._find_duplicate(data), created=False)

    def get_client(self, client_id):
        """Consulta un cliente para su vista de detalle."""
        return self.repository.get_by_id(client_id)

    def update(self, client_id, raw_data, photo=None):
        """Actualiza un cliente y evita que su edición invada otro registro existente."""
        client = self.get_client(client_id)
        if not client:
            return None
        data = self.validator.validate(raw_data, photo, photo_required=False)
        existing = self._find_duplicate(data, exclude_id=client.id)
        if existing:
            return ClientRegistrationResult(client=existing, created=False)
        if photo:
            data['photo'] = photo
        try:
            return ClientRegistrationResult(client=self.repository.update(client, **data), created=True)
        except IntegrityError:
            return ClientRegistrationResult(client=self._find_duplicate(data, exclude_id=client.id), created=False)

    def list_clients(self):
        """Devuelve el conjunto de clientes para el repositorio REST de Vue."""
        return self.repository.list()

    def _find_duplicate(self, data, exclude_id=None):
        """Centraliza los criterios que la base de datos también garantiza mediante índices."""
        return self.repository.find_duplicate(
            full_name=data['full_name'], birth_date=data['birth_date'],
            personal_phone=data['personal_phone'], personal_email=data['personal_email'],
            exclude_id=exclude_id,
        )
