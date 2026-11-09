"""Facades de negocio: las vistas HTTP no consultan el ORM directamente."""
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from .repositories import ClientRepository, PostalCodeRepository, StatusRepository, VehicleRepository, WorkshopRepository
from .validators import ClientInputError, ClientRegistrationValidator, StatusValidator, VehicleLookupValidator, VehicleUpdateValidator, VehicleValidator


@dataclass
class RegistrationResult:
    entity: object
    created: bool

    @property
    def client(self):
        """Compatibilidad con las respuestas existentes de clientes y talleres."""
        return self.entity


class PostalCodeFacade:
    def __init__(self, repository=None): self.repository = repository or PostalCodeRepository()
    def lookup(self, cp):
        rows = list(self.repository.find(cp))
        return None if not rows else {'cp': cp, 'state': rows[0].state, 'municipality': rows[0].municipality, 'neighborhoods': [{'name': row.neighborhood, 'settlement_type': row.settlement_type} for row in rows]}
    def verified(self, data):
        cp = str(data.get('postal_code', ''))
        return not self.repository.find(cp).exists() or self.repository.matches(cp, data.get('neighborhood', ''), data.get('municipality', ''), data.get('state', ''))


class ClientFacade:
    def __init__(self, repository=None, validator=None):
        self.repository = repository or ClientRepository(); self.validator = validator or ClientRegistrationValidator()
    def register(self, raw_data, photo):
        data = self.validator.validate(raw_data, photo); self._validate_address(data)
        duplicate = self._duplicate(data)
        if duplicate: return RegistrationResult(duplicate, False)
        data['estatus'] = StatusRepository().by_name('activo')
        try: return RegistrationResult(self.repository.save(photo=photo, **data), True)
        except IntegrityError: return RegistrationResult(self._duplicate(data), False)
    def get_client(self, client_id, lock=False): return self.repository.get_by_id(client_id, lock=lock)
    def list_clients(self, **filters): return self.repository.list(**filters)
    def update(self, client_id, raw_data, photo=None):
        client = self.get_client(client_id)
        if not client: return None
        data = self.validator.validate(raw_data, photo, photo_required=False); self._validate_address(data)
        duplicate = self._duplicate(data, client.id)
        if duplicate: return RegistrationResult(duplicate, False)
        if photo: data['photo'] = photo
        try: return RegistrationResult(self.repository.update(client, **data), True)
        except IntegrityError: return RegistrationResult(self._duplicate(data, client.id), False)
    def suspend(self, client_id):
        with transaction.atomic():
            client = self.get_client(client_id, lock=True)
            if not client: return None, 'Cliente no encontrado.'
            if client.estatus.name == 'suspendido': return None, 'El cliente ya está suspendido.'
            suspended = StatusRepository().by_name('suspendido')
            changed = self.repository.set_status_if_current(client_id, from_status='activo', to_status=suspended.id)
            if not changed: return None, 'El cliente no está activo y no puede suspenderse.'
            client.estatus = suspended; return client, None
    def activate(self, client_id):
        with transaction.atomic():
            client = self.get_client(client_id, lock=True)
            if not client: return None, 'Cliente no encontrado.'
            active = StatusRepository().by_name('activo')
            changed = self.repository.set_status_if_current(client_id, from_status='suspendido', to_status=active.id)
            if not changed: return None, 'El cliente no está suspendido.'
            client.estatus = active; return client, None
    def _duplicate(self, data, exclude_id=None): return self.repository.find_duplicate(full_name=data['full_name'], birth_date=data['birth_date'], personal_phone=data['personal_phone'], personal_email=data['personal_email'], exclude_id=exclude_id)
    def _validate_address(self, data):
        if not WorkshopRepository().get_by_id(data['workshop_id']): raise ClientInputError({'workshop_id': 'El taller seleccionado no existe.'})
        if not PostalCodeFacade().verified(data): raise ClientInputError({'neighborhood': 'La colonia no coincide con el código postal.', 'municipality': 'El municipio no coincide con el código postal.', 'state': 'El estado no coincide con el código postal.'})


class StatusFacade:
    BASE = {'activo', 'suspendido', 'actualizado', 'cancelado'}
    def __init__(self, repository=None, validator=None): self.repository = repository or StatusRepository(); self.validator = validator or StatusValidator()
    def list(self, **filters): return self.repository.list(**filters)
    def get(self, status_id): return self.repository.get(status_id)
    def create(self, raw):
        data = self.validator.validate(raw); existing = self.repository.find_name(data['name'])
        if existing: return RegistrationResult(existing, False)
        try: return RegistrationResult(self.repository.save(**data), True)
        except IntegrityError: return RegistrationResult(self.repository.find_name(data['name']), False)
    def update(self, status_id, raw):
        status = self.get(status_id)
        if not status: return None
        data = self.validator.validate(raw); existing = self.repository.find_name(data['name'], exclude_id=status.id)
        if existing: return RegistrationResult(existing, False)
        return RegistrationResult(self.repository.update(status, **data), True)
    def delete(self, status_id, user):
        with transaction.atomic():
            status = self.repository.get(status_id, lock=True)
            if not status: return False, 'Estatus no encontrado.'
            if status.name in self.BASE: return False, 'Los cuatro estatus base no se pueden eliminar.'
            if self.repository.is_in_use(status.id): return False, 'No se puede eliminar un estatus que está en uso.'
            status.deleted_at = timezone.now(); status.deleted_by = user; status.save(update_fields=['deleted_at', 'deleted_by']); return True, None


class VehicleUpdateConflict(Exception):
    """Conflicto de escritura de vehículo sin exponer datos de otro registro."""


class VehicleFacade:
    def update(self, vehicle_id, raw_data):
        data = VehicleUpdateValidator().validate(raw_data)
        try:
            with transaction.atomic():
                vehicle = self.repository.get_for_update(vehicle_id)
                if vehicle is None:
                    return None
                if 'plate' in data and self.repository.plate_in_use(data['plate'], exclude_id=vehicle.id):
                    raise VehicleUpdateConflict()
                return self.repository.update(vehicle, data)
        except IntegrityError:
            # atomic ya revirtió el savepoint; no consultar dentro de una transacción rota.
            raise VehicleUpdateConflict() from None

    def __init__(self, repository=None, validator=None): self.repository = repository or VehicleRepository(); self.validator = validator or VehicleValidator()
    def create(self, client_id, raw):
        data = self.validator.validate(raw)
        with transaction.atomic():
            client = ClientRepository().get_by_id(client_id, lock=True)
            if not client: raise ClientInputError({'client_id': 'El cliente no existe.'})
            if client.estatus.name != 'activo': raise ClientInputError({'client_id': 'Sólo se pueden registrar vehículos para clientes activos.'})
            duplicate = self.repository.find_duplicate(vin=data['vin'], plate=data['plate'])
            if duplicate: return RegistrationResult(duplicate, False)
            data['client'] = client; data['estatus'] = StatusRepository().by_name('activo')
            try: return RegistrationResult(self.repository.save(**data), True)
            except IntegrityError: return RegistrationResult(self.repository.find_duplicate(vin=data['vin'], plate=data['plate']), False)
    def lookup(self, params):
        query = VehicleLookupValidator().validate(params)
        return self.repository.lookup(**query)

    def list_for_client(self, client_id, **filters): return self.repository.list_for_client(client_id, **filters)


class WorkshopFacade:
    def __init__(self, repository=None, validator=None): self.repository = repository or WorkshopRepository(); self.validator = validator or ClientRegistrationValidator()
    def register(self, raw_data, photo):
        data = self.validator.validate_workshop(raw_data, photo)
        if not PostalCodeFacade().verified(data): raise ClientInputError({'neighborhood': 'La colonia no coincide con el código postal.'})
        duplicate = self.repository.find_duplicate(**data)
        if duplicate: return RegistrationResult(duplicate, False)
        try: return RegistrationResult(self.repository.save(photo=photo, **data), True)
        except IntegrityError: return RegistrationResult(self.repository.find_duplicate(**data), False)
    def list(self): return self.repository.list()
