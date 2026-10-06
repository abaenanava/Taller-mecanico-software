from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('workshop', '0002_client')]

    operations = [
        migrations.AddField(
            model_name='client', name='work_phone',
            field=models.CharField(default='+520000000000', max_length=16), preserve_default=False,
        ),
        migrations.AlterField(model_name='client', name='personal_email', field=models.EmailField(max_length=254, unique=True)),
        migrations.AlterField(model_name='client', name='personal_phone', field=models.CharField(max_length=16, unique=True)),
        migrations.AlterModelTable(name='client', table='clientes'),
        migrations.AddConstraint(
            model_name='client',
            constraint=models.UniqueConstraint(fields=('full_name', 'birth_date'), name='clientes_nombre_fecha_nacimiento_unico'),
        ),
    ]
