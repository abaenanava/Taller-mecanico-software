"""Alinea longitudes y validación declarativa del modelo Cliente con el esquema real."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('workshop', '0005_postalcode_workshop_client_workshop_status')]

    operations = [
        migrations.AlterField(model_name='client', name='neighborhood', field=models.CharField(max_length=160)),
        migrations.AlterField(model_name='client', name='municipality', field=models.CharField(max_length=160)),
        migrations.AlterField(model_name='client', name='postal_code', field=models.CharField(max_length=5)),
        migrations.AlterField(model_name='client', name='state', field=models.CharField(max_length=160)),
        migrations.AlterField(
            model_name='client', name='status',
            field=models.CharField(choices=[('ACTIVO', 'Activo'), ('SUSPENDIDO', 'Suspendido')], default='ACTIVO', max_length=12),
        ),
    ]
