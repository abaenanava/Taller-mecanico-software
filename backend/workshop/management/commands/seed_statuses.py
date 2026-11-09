from django.core.management.base import BaseCommand

from workshop.models import Status


BASE_STATUSES = {
    'activo': 'Registro disponible para operar y para asociar vehículos.',
    'suspendido': 'Registro temporalmente inactivo; conserva su historial.',
    'actualizado': 'Registro con información actualizada que no permite asociar vehículos.',
    'cancelado': 'Registro cancelado; conserva su historial para auditoría.',
}


class Command(BaseCommand):
    help = 'Crea o actualiza los cuatro estatus base sin duplicarlos.'

    def handle(self, *args, **options):
        created = 0
        for name, description in BASE_STATUSES.items():
            _, was_created = Status.all_objects.update_or_create(name=name, defaults={'description': description, 'deleted_at': None, 'deleted_by': None})
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f'Estatus base listos; nuevos: {created}.'))
