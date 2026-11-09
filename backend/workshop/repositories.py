"""Repositorios: acceso ORM aislado de las vistas y de las Facades."""
from django.db.models import Q

from .models import Client, PostalCode, Status, Vehicle, Workshop


def paginate(query, page, page_size=10):
    """Hace COUNT separado y LIMIT/OFFSET, limitado a diez registros por solicitud."""
    page = max(int(page or 1), 1)
    total = query.count()
    return query[(page - 1) * page_size: page * page_size], total


class ClientRepository:
    def find_duplicate(self, *, full_name, birth_date, personal_phone, personal_email, exclude_id=None):
        query = Client.objects.filter(Q(personal_phone=personal_phone) | Q(personal_email__iexact=personal_email) | Q(full_name__iexact=full_name, birth_date=birth_date))
        if exclude_id:
            query = query.exclude(pk=exclude_id)
        return query.order_by('-created_at').first()

    def save(self, **data): return Client.objects.create(**data)

    def list(self, *, workshop_id=None, status=None, order='full_name', direction='asc', page=1):
        query = Client.objects.select_related('workshop', 'estatus').only('id', 'full_name', 'photo', 'created_at', 'workshop__name', 'estatus__name', 'workshop_id', 'estatus_id')
        if workshop_id: query = query.filter(workshop_id=workshop_id)
        if status: query = query.filter(estatus__name__iexact=status)
        order = order if order in {'full_name', 'created_at'} else 'full_name'
        query = query.order_by(('-' if direction == 'desc' else '') + order, 'id')
        return paginate(query, page)

    def get_by_id(self, client_id, *, lock=False):
        query = Client.objects.select_related('workshop', 'estatus')
        if lock: query = query.select_for_update()
        return query.filter(pk=client_id).first()

    def update(self, client, **data):
        for field, value in data.items(): setattr(client, field, value)
        client.save()
        return client

    def set_status_if_current(self, client_id, *, from_status, to_status):
        return Client.objects.filter(pk=client_id, estatus__name__iexact=from_status).update(estatus_id=to_status)


class StatusRepository:
    def list(self, *, order='name', direction='asc', page=1):
        order = order if order in {'name', 'created_at'} else 'name'
        query = Status.objects.only('id', 'name', 'description', 'created_at').order_by(('-' if direction == 'desc' else '') + order, 'id')
        return paginate(query, page)

    def get(self, status_id, *, lock=False):
        query = Status.objects
        if lock: query = query.select_for_update()
        return query.filter(pk=status_id).first()

    def find_name(self, name, exclude_id=None):
        query = Status.objects.filter(name__iexact=name)
        if exclude_id: query = query.exclude(pk=exclude_id)
        return query.first()

    def by_name(self, name): return Status.objects.filter(name__iexact=name).first()
    def save(self, **data): return Status.objects.create(**data)
    def update(self, status, **data):
        for field, value in data.items(): setattr(status, field, value)
        status.save()
        return status

    def is_in_use(self, status_id):
        return Client.objects.filter(estatus_id=status_id).exists() or Vehicle.objects.filter(estatus_id=status_id).exists()


class VehicleRepository:
    def get_for_update(self, vehicle_id):
        """Bloquea el vehículo visible y sus relaciones durante una modificación."""
        return Vehicle.objects.select_related('client__workshop', 'estatus').select_for_update().filter(
            pk=vehicle_id,
            client__deleted_at__isnull=True,
            client__workshop__deleted_at__isnull=True,
        ).first()

    def plate_in_use(self, plate, exclude_id):
        return Vehicle.objects.filter(plate__iexact=plate).exclude(pk=exclude_id).exists()

    def update(self, vehicle, data):
        for field, value in data.items():
            setattr(vehicle, field, value)
        vehicle.save(update_fields=[*data, 'updated_at'])
        return vehicle

    def lookup(self, *, field, value):
        """Excluye también relaciones eliminadas; se consulta sin alterar sus estatus."""
        lookup_field = {'id': 'pk', 'vin': 'vin__iexact', 'plate': 'plate__iexact'}[field]
        return Vehicle.objects.select_related('client__workshop', 'estatus').filter(
            client__deleted_at__isnull=True,
            client__workshop__deleted_at__isnull=True,
            **{lookup_field: value},
        ).order_by('id').first()

    def find_duplicate(self, *, vin, plate):
        return Vehicle.objects.filter(Q(vin=vin) | Q(plate=plate)).select_related('client', 'estatus').first()

    def save(self, **data): return Vehicle.objects.create(**data)

    def list_for_client(self, client_id, *, order='created_at', direction='desc', page=1):
        order = order if order in {'created_at', 'brand', 'plate', 'year'} else 'created_at'
        query = Vehicle.objects.filter(client_id=client_id).select_related('estatus').only('id', 'plate', 'brand', 'model', 'vin', 'year', 'version', 'color', 'mileage', 'created_at', 'estatus__name')
        query = query.order_by(('-' if direction == 'desc' else '') + order, 'id')
        return paginate(query, page)


class PostalCodeRepository:
    def find(self, cp): return PostalCode.objects.filter(cp=cp).order_by('neighborhood')
    def matches(self, cp, neighborhood, municipality, state): return PostalCode.objects.filter(cp=cp, neighborhood__iexact=neighborhood, municipality__iexact=municipality, state__iexact=state).exists()


class WorkshopRepository:
    def find_duplicate(self, *, rfc, name, street, neighborhood, municipality, state, postal_code, exclude_id=None, **_unused):
        query = Workshop.objects.filter(Q(rfc__iexact=rfc) | Q(name__iexact=name, street__iexact=street, neighborhood__iexact=neighborhood, municipality__iexact=municipality, state__iexact=state, postal_code=postal_code))
        if exclude_id: query = query.exclude(pk=exclude_id)
        return query.order_by('-created_at').first()
    def save(self, **data): return Workshop.objects.create(**data)
    def list(self): return Workshop.objects.order_by('name')
    def get_by_id(self, workshop_id): return Workshop.objects.filter(pk=workshop_id).first()
