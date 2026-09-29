"""Seeder explícito de las dos cuentas autorizadas para gestionar clientes."""
import os

from django.core.management.base import BaseCommand, CommandError

from workshop.models import User


class Command(BaseCommand):
    help = 'Crea o actualiza las cuentas Administrador y Recepcionista usando variables de entorno.'

    def handle(self, *args, **options):
        accounts = (
            ('administrador', 'Administrador', User.Role.ADMIN, os.environ.get('SEED_ADMIN_PASSWORD')),
            ('recepcionista', 'Recepcionista', User.Role.RECEPTION, os.environ.get('SEED_RECEPTION_PASSWORD')),
        )
        missing = [username for username, _, _, password in accounts if not password]
        if missing:
            raise CommandError('Faltan las variables de contraseña para: ' + ', '.join(missing))
        for username, first_name, role, password in accounts:
            user, created = User.objects.get_or_create(username=username)
            user.first_name = first_name
            user.role = role
            user.is_active = True
            user.set_password(password)
            user.save()
            action = 'creada' if created else 'actualizada'
            self.stdout.write(self.style.SUCCESS(f'Cuenta {role.lower()} {action}: {username}'))
