"""Fachada del caso de uso: registro y consulta de clientes."""
from dataclasses import dataclass

from django.db import IntegrityError

from .repositories import ClientRepository, PostalCodeRepository, WorkshopRepository
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
        self._validate_address(data)
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
        self._validate_address(data)
        existing = self._find_duplicate(data, exclude_id=client.id)
        if existing:
            return ClientRegistrationResult(client=existing, created=False)
        if photo:
            data['photo'] = photo
        try:
            return ClientRegistrationResult(client=self.repository.update(client, **data), created=True)
        except IntegrityError:
            return ClientRegistrationResult(client=self._find_duplicate(data, exclude_id=client.id), created=False)

    def list_clients(self, **filters):
        """Devuelve el conjunto de clientes para el repositorio REST de Vue."""
        return self.repository.list(**filters)

    def suspend(self, client_id):
        """Cambia un cliente a suspendido sin eliminar su historial."""
        client = self.get_client(client_id)
        if not client:
            return None
        client.status = 'SUSPENDIDO'
        return self.repository.update(client, status=client.status)

    def activate(self, client_id):
        """Restaura un cliente suspendido para que vuelva a estar activo."""
        client = self.get_client(client_id)
        if not client:
            return None
        client.status = 'ACTIVO'
        return self.repository.update(client, status=client.status)

    def _find_duplicate(self, data, exclude_id=None):
        """Centraliza los criterios que la base de datos también garantiza mediante índices."""
        return self.repository.find_duplicate(
            full_name=data['full_name'], birth_date=data['birth_date'],
            personal_phone=data['personal_phone'], personal_email=data['personal_email'],
            exclude_id=exclude_id,
        )

    def _validate_address(self, data):
        if not WorkshopRepository().get_by_id(data['workshop_id']):
            from .validators import ClientInputError
            raise ClientInputError({'workshop_id': 'El taller seleccionado no existe.'})
        postal = PostalCodeFacade()
        if not postal.verified(data):
            from .validators import ClientInputError
            raise ClientInputError({'neighborhood': 'La colonia no coincide con el código postal.', 'municipality': 'El municipio no coincide con el código postal.', 'state': 'El estado no coincide con el código postal.'})


class PostalCodeFacade:
    def __init__(self, repository=None):
        self.repository = repository or PostalCodeRepository()

    def lookup(self, cp):
        rows = list(self.repository.find(cp))
        if not rows:
            return None
        return {'cp': cp, 'state': rows[0].state, 'municipality': rows[0].municipality, 'neighborhoods': [{'name': row.neighborhood, 'settlement_type': row.settlement_type} for row in rows]}

    def verified(self, data):
        cp = str(data.get('postal_code', ''))
        if not self.repository.find(cp).exists():
            return True
        return self.repository.matches(cp, data.get('neighborhood', ''), data.get('municipality', ''), data.get('state', ''))


class WorkshopFacade:
    def __init__(self, repository=None, validator=None):
        self.repository = repository or WorkshopRepository()
        self.validator = validator or ClientRegistrationValidator()

    def register(self, raw_data, photo):
        data = self.validator.validate_workshop(raw_data, photo)
        if not PostalCodeFacade().verified(data):
            from .validators import ClientInputError
            raise ClientInputError({'neighborhood': 'La colonia no coincide con el código postal.', 'municipality': 'El municipio no coincide con el código postal.', 'state': 'El estado no coincide con el código postal.'})
        duplicate = self.repository.find_duplicate(**data)
        if duplicate:
            return ClientRegistrationResult(duplicate, False)
        try:
            return ClientRegistrationResult(self.repository.save(photo=photo, **data), True)
        except IntegrityError:
            # El índice único es la última barrera ante dos solicitudes simultáneas.
            return ClientRegistrationResult(self.repository.find_duplicate(**data), False)

    def list(self):
        return self.repository.list()
