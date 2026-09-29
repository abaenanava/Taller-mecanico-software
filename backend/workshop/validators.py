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
        return data
