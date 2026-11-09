from django.db import migrations, models
from django.db.migrations.exceptions import IrreversibleError
from django.db.models.functions import Length


DROP_ACTIVE_PLATE = [
    "ALTER TABLE vehiculos DROP INDEX vehiculos_placa_activa_unica",
    "ALTER TABLE vehiculos DROP COLUMN active_plate",
]


def add_active_plate(length):
    return [
        f"ALTER TABLE vehiculos ADD COLUMN active_plate varchar({length}) GENERATED ALWAYS AS (IF(deleted_at IS NULL, plate, NULL)) VIRTUAL",
        "ALTER TABLE vehiculos ADD UNIQUE INDEX vehiculos_placa_activa_unica (active_plate)",
    ]


def guard_plate_length_rollback(apps, schema_editor):
    Vehicle = apps.get_model('workshop', 'Vehicle')
    # El ancho aplica a todas las placas, incluidas las de vehículos eliminados.
    if Vehicle._base_manager.using(schema_editor.connection.alias).annotate(
        plate_length=Length('plate'),
    ).filter(plate_length__gt=8).exists():
        raise IrreversibleError(
            'No se puede revertir la longitud de placa a 8: existen placas de más de 8 caracteres.'
        )


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('workshop', '0008_model_state_indexes')]
    operations = [
        # La retirada admite active_plate STORED de un esquema anterior o VIRTUAL.
        migrations.RunSQL(DROP_ACTIVE_PLATE, add_active_plate(8)),
        migrations.AlterField(model_name='vehicle', name='plate', field=models.CharField(max_length=9)),
        migrations.RunSQL(add_active_plate(9), DROP_ACTIVE_PLATE),
        # En reversa se comprueba la longitud antes de alterar cualquier objeto.
        migrations.RunPython(migrations.RunPython.noop, guard_plate_length_rollback),
    ]
