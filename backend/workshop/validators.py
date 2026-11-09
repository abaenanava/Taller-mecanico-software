"""Validación de entrada del caso de uso de registro de clientes."""
import re
from datetime import date

from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class ClientInputError(Exception):
    """Error de dominio que contiene mensajes específicos para los campos de Vue."""

    def __init__(self, fields):
        self.fields = fields
        super().__init__('Los datos del cliente no son válidos.')


class ClientRegistrationValidator:
    REQUIRED_FIELDS = (
        'full_name', 'alternate_contact_name', 'age', 'birth_date', 'personal_phone', 'work_phone',
        'street', 'neighborhood', 'municipality', 'state', 'postal_code', 'personal_email',
    )
    MAX_PHOTO_SIZE = 15 * 1024 * 1024
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png'}

    def validate(self, raw_data, photo, *, photo_required=True):
        """Normaliza la entrada y valida formato, tamaño y firma de fotografía.

        ``photo_required`` permite editar un cliente sin volver a adjuntar su imagen.
        """
        errors = {}
        data = {field: str(raw_data.get(field, '')).strip() for field in self.REQUIRED_FIELDS}
        data['work_email'] = str(raw_data.get('work_email', '')).strip()

        for field in self.REQUIRED_FIELDS:
            if not data[field]:
                errors[field] = 'Este campo es obligatorio.'

        if data.get('full_name') and len(data['full_name'].split()) < 2:
            errors['full_name'] = 'Captura al menos nombre y apellido.'

        try:
            age = int(data['age'])
            if not 0 <= age <= 120:
                raise ValueError
        except (ValueError, TypeError):
            errors['age'] = 'La edad debe ser un número entre 0 y 120.'
            age = None

        try:
            birth_date = date.fromisoformat(data['birth_date'])
            if birth_date > date.today():
                errors['birth_date'] = 'La fecha de nacimiento no puede estar en el futuro.'
        except (ValueError, TypeError):
            errors['birth_date'] = 'Captura una fecha de nacimiento válida.'
            birth_date = None

        for field in ('personal_phone', 'work_phone'):
            phone_digits = re.sub(r'\D', '', data[field])
            if phone_digits.startswith('52') and len(phone_digits) == 12:
                phone_digits = phone_digits[2:]
            if len(phone_digits) != 10:
                errors[field] = 'El teléfono debe contener 10 dígitos; se permite el prefijo +52.'
            data[field] = f'+52{phone_digits}' if len(phone_digits) == 10 else data[field]

        if data.get('postal_code') and not re.fullmatch(r'\d{5}', data['postal_code']):
            errors['postal_code'] = 'El código postal debe contener exactamente 5 dígitos.'

        for field in ('personal_email', 'work_email'):
            if data[field]:
                try:
                    validate_email(data[field])
                except ValidationError:
                    errors[field] = 'Captura un correo electrónico válido.'

        if not photo and photo_required:
            errors['photo'] = 'La fotografía es obligatoria.'
        elif photo:
            extension = photo.name.rsplit('.', 1)[-1].lower() if '.' in photo.name else ''
            if photo.size > self.MAX_PHOTO_SIZE:
                errors['photo'] = 'La fotografía no debe superar 15 MB.'
            elif extension not in {'jpg', 'jpeg', 'png'} or photo.content_type not in self.ALLOWED_MIME_TYPES:
                errors['photo'] = 'La fotografía debe ser un archivo PNG o JPG válido.'
            else:
                signature = photo.read(8)
                photo.seek(0)
                is_png = signature.startswith(b'\x89PNG\r\n\x1a\n')
                is_jpeg = signature.startswith(b'\xff\xd8\xff')
                if not ((extension == 'png' and is_png) or (extension in {'jpg', 'jpeg'} and is_jpeg)):
                    errors['photo'] = 'El contenido del archivo no corresponde a una imagen PNG o JPG válida.'

        if errors:
            raise ClientInputError(errors)

        data['age'] = age
        data['birth_date'] = birth_date
        try:
            data['workshop_id'] = int(raw_data.get('workshop_id', ''))
        except (ValueError, TypeError):
            errors['workshop_id'] = 'Selecciona un taller.'
        if errors:
            raise ClientInputError(errors)
        return data

    def validate_workshop(self, raw_data, photo):
        fields = ('name', 'street', 'neighborhood', 'municipality', 'state', 'postal_code', 'business_name', 'phone', 'rfc', 'contact_email')
        data = {field: str(raw_data.get(field, '')).strip().upper() if field == 'rfc' else str(raw_data.get(field, '')).strip() for field in fields}
        errors = {field: 'Este campo es obligatorio.' for field in fields if not data[field]}
        phone_digits = re.sub(r'\D', '', data['phone'])
        if phone_digits.startswith('52') and len(phone_digits) == 12: phone_digits = phone_digits[2:]
        if len(phone_digits) != 10: errors['phone'] = 'El teléfono debe contener 10 dígitos.'
        else: data['phone'] = f'+52{phone_digits}'
        if not re.fullmatch(r'^(?:[A-ZÑ&]{3,4})(?:\d{6})(?:[A-Z0-9]{3})$', data['rfc']): errors['rfc'] = 'Captura un RFC mexicano válido de 12 o 13 caracteres.'
        if not re.fullmatch(r'\d{5}', data['postal_code']): errors['postal_code'] = 'El código postal debe tener 5 dígitos.'
        try: validate_email(data['contact_email'])
        except ValidationError: errors['contact_email'] = 'Captura un correo electrónico válido.'
        if not photo: errors['photo'] = 'La fotografía es obligatoria.'
        elif photo.size > self.MAX_PHOTO_SIZE or photo.content_type not in self.ALLOWED_MIME_TYPES: errors['photo'] = 'La fotografía debe ser PNG/JPG y no superar 15 MB.'
        else:
            extension = photo.name.rsplit('.', 1)[-1].lower() if '.' in photo.name else ''
            signature = photo.read(8); photo.seek(0)
            if extension not in {'jpg', 'jpeg', 'png'} or not ((extension == 'png' and signature.startswith(b'\x89PNG\r\n\x1a\n')) or (extension in {'jpg', 'jpeg'} and signature.startswith(b'\xff\xd8\xff'))):
                errors['photo'] = 'La fotografía debe ser un archivo PNG o JPG válido.'
        if errors: raise ClientInputError(errors)
        return data


class StatusValidator:
    """Valida el catálogo sin aceptar nombres vacíos ni variantes de mayúsculas."""

    def validate(self, raw_data):
        name = str(raw_data.get('name', '')).strip().lower()
        description = str(raw_data.get('description', '')).strip()
        errors = {}
        if not name: errors['name'] = 'El nombre es obligatorio.'
        elif len(name) > 50: errors['name'] = 'El nombre no debe superar 50 caracteres.'
        if not description: errors['description'] = 'La descripción es obligatoria.'
        if errors: raise ClientInputError(errors)
        return {'name': name, 'description': description}


class VehicleValidator:
    """Normaliza y valida el formulario de vehículos antes de persistirlo."""

    PLATE_PATTERN = r'^[A-Z]{3}-\d{3}-[A-Z]$'
    VIN_PATTERN = r'^[A-HJ-NPR-Z0-9]{17}$'

    def validate(self, raw_data):
        fields = ('plate', 'brand', 'model', 'vin', 'year', 'version', 'color')
        data = {field: str(raw_data.get(field, '')).strip() for field in fields}
        data['plate'] = data['plate'].upper()
        data['vin'] = data['vin'].upper().replace(' ', '')
        errors = {field: 'Este campo es obligatorio.' for field in fields if not data[field]}
        if data['plate'] and not re.fullmatch(self.PLATE_PATTERN, data['plate']):
            errors['plate'] = 'La placa debe tener el formato ABC-123-D en mayúsculas.'
        if data['vin'] and not re.fullmatch(self.VIN_PATTERN, data['vin']):
            errors['vin'] = 'El VIN debe contener 17 caracteres válidos, sin I, O, Q ni espacios.'
        for field in ('brand', 'model', 'version', 'color'):
            if data[field] and len(data[field]) > 50: errors[field] = 'No debe superar 50 caracteres.'
        try:
            data['year'] = int(data['year'])
            if not 1950 <= data['year'] <= date.today().year + 1: raise ValueError
        except (ValueError, TypeError):
            errors['year'] = f'El año debe estar entre 1950 y {date.today().year + 1}.'
        mileage = str(raw_data.get('mileage', '')).strip()
        if mileage:
            try:
                data['mileage'] = int(mileage)
                if data['mileage'] < 0: raise ValueError
            except (ValueError, TypeError): errors['mileage'] = 'El kilometraje debe ser un entero mayor o igual a cero.'
        else: data['mileage'] = None
        if errors: raise ClientInputError(errors)
        return data


class VehicleLookupValidator:
    """Consulta un identificador exacto, sin permitir filtros arbitrarios del ORM."""

    FIELDS = {'vin', 'plate', 'id'}
    MAX_ID = (1 << 63) - 1

    def validate(self, params):
        errors = {}
        if set(params) - {'field', 'value'}:
            errors['field'] = 'La consulta solo admite field y value.'
        for name in ('field', 'value'):
            if hasattr(params, 'getlist') and len(params.getlist(name)) > 1:
                errors[name] = 'Envía este parámetro una sola vez.'
        field = str(params.get('field', '')).strip()
        raw_value = str(params.get('value', ''))
        value = raw_value.strip().upper()
        if field not in self.FIELDS:
            errors['field'] = 'Selecciona VIN, placa o ID.'
        if not value:
            errors['value'] = 'Captura el identificador del vehículo.'
        elif len(raw_value) > 128:
            errors['value'] = 'El identificador enviado es demasiado largo.'
        elif field == 'id':
            if not re.fullmatch(r'[0-9]{1,19}', value) or not 1 <= int(value) <= self.MAX_ID:
                errors['value'] = 'El ID debe ser un entero positivo de hasta 9223372036854775807.'
            else:
                value = int(value)
        elif field == 'vin' and not re.fullmatch(VehicleValidator.VIN_PATTERN, value, flags=re.ASCII):
            errors['value'] = 'El VIN debe contener 17 caracteres válidos, sin I, O, Q ni espacios.'
        elif field == 'plate' and not re.fullmatch(VehicleValidator.PLATE_PATTERN, value, flags=re.ASCII):
            errors['value'] = 'La placa debe tener el formato ABC-123-D.'
        if errors:
            raise ClientInputError(errors)
        return {'field': field, 'value': value}


class VehicleUpdateValidator:
    """PATCH explícito: no admite identificadores, relaciones ni conversión implícita de tipos."""

    EDITABLE_FIELDS = {'plate', 'brand', 'model', 'year', 'version', 'color', 'mileage'}
    MAX_MILEAGE = (1 << 32) - 1  # PositiveIntegerField se almacena como integer unsigned en MySQL.

    def validate(self, raw_data):
        if not isinstance(raw_data, dict) or not raw_data:
            raise ClientInputError({'body': 'Envía un objeto JSON con al menos un campo editable.'})
        unknown = set(raw_data) - self.EDITABLE_FIELDS
        if unknown:
            raise ClientInputError({field: 'Este campo no se puede modificar.' for field in sorted(unknown)})
        errors = {}
        data = {}
        for field, value in raw_data.items():
            if field in {'plate', 'brand', 'model', 'version', 'color'}:
                if not isinstance(value, str):
                    errors[field] = 'Este campo debe ser texto.'
                    continue
                value = value.strip()
                if not value:
                    errors[field] = 'Este campo es obligatorio.'
                elif field == 'plate':
                    value = value.upper()
                    if not re.fullmatch(VehicleValidator.PLATE_PATTERN, value, flags=re.ASCII):
                        errors[field] = 'La placa debe tener el formato ABC-123-D.'
                elif len(value) > 50:
                    errors[field] = 'No debe superar 50 caracteres.'
            elif field == 'year':
                if type(value) is not int or not 1950 <= value <= date.today().year + 1:
                    errors[field] = f'El año debe ser un entero entre 1950 y {date.today().year + 1}.'
            elif field == 'mileage':
                if value is not None and (type(value) is not int or not 0 <= value <= self.MAX_MILEAGE):
                    errors[field] = 'El kilometraje debe ser null o un entero entre 0 y 4294967295.'
            data[field] = value
        if errors:
            raise ClientInputError(errors)
        return data
