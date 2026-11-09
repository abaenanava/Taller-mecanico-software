from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    """Registra en el estado Django los índices ya creados por SQL en 0007.

    MySQL necesita columnas generadas para unicidad entre registros no eliminados;
    por ello los índices físicos están en 0007 y aquí no se ejecuta SQL adicional.
    """
    dependencies = [('workshop', '0007_soft_delete_status_vehicle')]
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(model_name='client', name='personal_phone', field=models.CharField(max_length=16, validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])),
                migrations.AddIndex(model_name='client', index=models.Index(fields=['deleted_at', 'workshop', 'estatus'], name='clientes_lista_idx')),
                migrations.AddIndex(model_name='vehicle', index=models.Index(fields=['deleted_at', 'client', 'estatus'], name='vehiculos_lista_idx')),
                migrations.AddIndex(model_name='workshop', index=models.Index(fields=['deleted_at', 'name'], name='talleres_activos_idx')),
            ],
            database_operations=[],
        ),
    ]
