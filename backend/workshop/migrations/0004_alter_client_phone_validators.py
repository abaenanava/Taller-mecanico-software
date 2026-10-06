import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('workshop', '0003_client_access_constraints')]

    operations = [
        migrations.AlterField(
            model_name='client', name='personal_phone',
            field=models.CharField(
                max_length=16, unique=True,
                validators=[django.core.validators.RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')],
            ),
        ),
        migrations.AlterField(
            model_name='client', name='work_phone',
            field=models.CharField(
                max_length=16,
                validators=[django.core.validators.RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')],
            ),
        ),
    ]
