"""Importa una vez el catálogo CPdescarga.txt de Correos de México."""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from workshop.models import PostalCode


class Command(BaseCommand):
    help = 'Importa el TXT SEPOMEX oficial en lotes idempotentes de 1,000 filas.'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='/app/database/seeds/CPdescarga.txt')

    def handle(self, *args, **options):
        path = Path(options['file'])
        if not path.exists():
            raise CommandError(f'No existe el catálogo: {path}')
        if path.stat().st_size < 1_000_000:
            raise CommandError('El catálogo es demasiado pequeño para ser el archivo nacional.')

        before_total = PostalCode.objects.count()
        batch, attempted, rows = [], 0, 0
        seen = set()
        with path.open('r', encoding='latin-1', newline='') as source:
            for line_number, raw in enumerate(source, start=1):
                line = raw.rstrip('\r\n')
                if line_number <= 2 or not line or line.startswith('d_codigo|'):
                    continue
                values = line.split('|')
                if len(values) < 5:
                    continue
                cp, neighborhood, settlement_type, municipality, state = (value.strip() for value in values[:5])
                if not (cp.isdigit() and len(cp) == 5 and neighborhood and municipality and state):
                    continue
                key = (cp, neighborhood, settlement_type, municipality, state)
                if key in seen:
                    continue
                seen.add(key); rows += 1
                batch.append(PostalCode(cp=cp, neighborhood=neighborhood, settlement_type=settlement_type, municipality=municipality, state=state))
                if len(batch) == 1000:
                    PostalCode.objects.bulk_create(batch, batch_size=1000, ignore_conflicts=True)
                    attempted += len(batch); batch.clear()
            if batch:
                PostalCode.objects.bulk_create(batch, batch_size=1000, ignore_conflicts=True)
                attempted += len(batch)
        total = PostalCode.objects.count()
        created = total - before_total
        self.stdout.write(self.style.SUCCESS(
            f'Filas válidas leídas: {rows}; intentadas: {attempted}; '
            f'nuevos registros: {created}; total en codigos_postales: {total}.'
        ))
