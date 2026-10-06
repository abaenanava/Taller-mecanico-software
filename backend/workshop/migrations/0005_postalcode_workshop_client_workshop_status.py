from django.db import migrations, models
import django.core.validators


def create_default_workshop_and_assign_clients(apps, schema_editor):
    Workshop = apps.get_model('workshop', 'Workshop')
    Client = apps.get_model('workshop', 'Client')
    workshop, _ = Workshop.objects.get_or_create(
        rfc='XAXX010101000',
        defaults={
            'name': 'Taller predeterminado', 'street': 'Sin dirección', 'neighborhood': 'Sin colonia',
            'municipality': 'Sin municipio', 'state': 'Sin estado', 'postal_code': '00000',
            'business_name': 'Taller predeterminado', 'phone': '+520000000000',
            'contact_email': 'predeterminado@example.invalid', 'photo': 'workshops/default.png',
        },
    )
    Client.objects.filter(workshop__isnull=True).update(workshop=workshop)


class Migration(migrations.Migration):
    dependencies = [('workshop', '0004_alter_client_phone_validators')]

    operations = [
        migrations.CreateModel(
            name='PostalCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cp', models.CharField(db_index=True, max_length=5)), ('neighborhood', models.CharField(max_length=160)),
                ('settlement_type', models.CharField(max_length=80)), ('municipality', models.CharField(max_length=160)),
                ('state', models.CharField(max_length=160)),
            ], options={'db_table': 'codigos_postales'},
        ),
        migrations.CreateModel(
            name='Workshop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)), ('street', models.CharField(max_length=120)),
                ('neighborhood', models.CharField(max_length=120)), ('municipality', models.CharField(max_length=120)),
                ('state', models.CharField(max_length=120)), ('postal_code', models.CharField(max_length=5)),
                ('business_name', models.CharField(max_length=200)),
                ('phone', models.CharField(max_length=16, validators=[django.core.validators.RegexValidator('^\\+52\\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])),
                ('rfc', models.CharField(max_length=13, unique=True)), ('contact_email', models.EmailField(max_length=254)),
                ('photo', models.FileField(upload_to='workshops/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])])),
                ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ], options={'db_table': 'talleres'},
        ),
        migrations.AddConstraint(model_name='postalcode', constraint=models.UniqueConstraint(fields=('cp', 'neighborhood', 'settlement_type', 'municipality', 'state'), name='cp_asentamiento_unico')),
        migrations.AddConstraint(model_name='workshop', constraint=models.UniqueConstraint(fields=('name', 'street', 'neighborhood', 'municipality', 'state', 'postal_code'), name='taller_nombre_direccion_unico')),
        migrations.AddField(model_name='client', name='workshop', field=models.ForeignKey(null=True, on_delete=models.PROTECT, related_name='clients', to='workshop.workshop')),
        migrations.AddField(model_name='client', name='status', field=models.CharField(choices=[('ACTIVO', 'Activo'), ('SUSPENDIDO', 'Suspendido')], default='ACTIVO', max_length=10)),
        migrations.RunPython(create_default_workshop_and_assign_clients, migrations.RunPython.noop),
        migrations.AlterField(model_name='client', name='workshop', field=models.ForeignKey(on_delete=models.PROTECT, related_name='clients', to='workshop.workshop')),
    ]
