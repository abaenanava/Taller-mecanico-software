from django.db import migrations, models
import django.db.models.deletion


BASE_STATUSES = {
    'activo': 'Registro disponible para operar y para asociar vehículos.',
    'suspendido': 'Registro temporalmente inactivo; conserva su historial.',
    'actualizado': 'Registro con información actualizada que no permite asociar vehículos.',
    'cancelado': 'Registro cancelado; conserva su historial para auditoría.',
}


def seed_statuses_and_migrate_clients(apps, schema_editor):
    Status = apps.get_model('workshop', 'Status')
    Client = apps.get_model('workshop', 'Client')
    statuses = {}
    for name, description in BASE_STATUSES.items():
        item, _ = Status.objects.get_or_create(name=name, defaults={'description': description})
        statuses[name] = item
    for client in Client.objects.all().iterator():
        legacy = (getattr(client, 'status', '') or '').lower()
        client.estatus_id = statuses['suspendido' if legacy == 'suspendido' else 'activo'].id
        client.save(update_fields=['estatus'])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [('workshop', '0006_align_client_address_fields')]

    operations = [
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='workshop.user')),
            ],
            options={'db_table': 'estatus'},
        ),
        migrations.AddField(model_name='postalcode', name='deleted_at', field=models.DateTimeField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name='postalcode', name='deleted_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='workshop.user')),
        migrations.AddField(model_name='workorder', name='deleted_at', field=models.DateTimeField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name='workorder', name='deleted_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='workshop.user')),
        migrations.AddField(model_name='workshop', name='deleted_at', field=models.DateTimeField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name='workshop', name='deleted_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='workshop.user')),
        migrations.AddField(model_name='client', name='deleted_at', field=models.DateTimeField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name='client', name='deleted_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='workshop.user')),
        migrations.AddField(model_name='client', name='estatus', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='clients', to='workshop.status')),
        migrations.RunPython(seed_statuses_and_migrate_clients, migrations.RunPython.noop),
        migrations.AlterField(model_name='client', name='estatus', field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='clients', to='workshop.status')),
        migrations.RemoveField(model_name='client', name='status'),
        migrations.AlterField(model_name='client', name='personal_phone', field=models.CharField(max_length=16)),
        migrations.AlterField(model_name='client', name='personal_email', field=models.EmailField(max_length=254)),
        migrations.AlterField(model_name='workshop', name='rfc', field=models.CharField(max_length=13)),
        migrations.RemoveConstraint(model_name='client', name='clientes_nombre_fecha_nacimiento_unico'),
        migrations.RemoveConstraint(model_name='workshop', name='taller_nombre_direccion_unico'),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plate', models.CharField(max_length=8)), ('brand', models.CharField(max_length=50)),
                ('model', models.CharField(max_length=50)), ('vin', models.CharField(max_length=17)),
                ('year', models.PositiveSmallIntegerField()), ('version', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=50)), ('mileage', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vehicles', to='workshop.client')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='workshop.user')),
                ('estatus', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vehicles', to='workshop.status')),
            ], options={'db_table': 'vehiculos'},
        ),
        # TiDB requiere VIRTUAL para agregar columnas generadas con ALTER TABLE.
        # Crear las columnas antes de los índices; al revertir, retirar los índices primero.
        migrations.RunSQL(
            [
                "ALTER TABLE estatus ADD COLUMN active_name varchar(50) GENERATED ALWAYS AS (IF(deleted_at IS NULL, LOWER(name), NULL)) VIRTUAL",
                "ALTER TABLE estatus ADD UNIQUE INDEX estatus_nombre_activo_unico (active_name)",
                "ALTER TABLE clientes ADD COLUMN active_personal_phone varchar(16) GENERATED ALWAYS AS (IF(deleted_at IS NULL, personal_phone, NULL)) VIRTUAL",
                "ALTER TABLE clientes ADD COLUMN active_personal_email varchar(254) GENERATED ALWAYS AS (IF(deleted_at IS NULL, LOWER(personal_email), NULL)) VIRTUAL",
                "ALTER TABLE clientes ADD COLUMN active_identity varchar(200) GENERATED ALWAYS AS (IF(deleted_at IS NULL, CONCAT(LOWER(full_name), '|', birth_date), NULL)) VIRTUAL",
                "ALTER TABLE clientes ADD UNIQUE INDEX clientes_telefono_activo_unico (active_personal_phone)",
                "ALTER TABLE clientes ADD UNIQUE INDEX clientes_correo_activo_unico (active_personal_email)",
                "ALTER TABLE clientes ADD UNIQUE INDEX clientes_identidad_activa_unica (active_identity)",
                "ALTER TABLE clientes ADD INDEX clientes_lista_idx (deleted_at, workshop_id, estatus_id)",
                "ALTER TABLE talleres ADD COLUMN active_rfc varchar(13) GENERATED ALWAYS AS (IF(deleted_at IS NULL, LOWER(rfc), NULL)) VIRTUAL",
                "ALTER TABLE talleres ADD COLUMN active_address varchar(700) GENERATED ALWAYS AS (IF(deleted_at IS NULL, CONCAT(LOWER(name), '|', LOWER(street), '|', LOWER(neighborhood), '|', LOWER(municipality), '|', LOWER(state), '|', postal_code), NULL)) VIRTUAL",
                "ALTER TABLE talleres ADD UNIQUE INDEX talleres_rfc_activo_unico (active_rfc)",
                "ALTER TABLE talleres ADD UNIQUE INDEX talleres_direccion_activa_unica (active_address)",
                "ALTER TABLE talleres ADD INDEX talleres_activos_idx (deleted_at, name)",
                "ALTER TABLE vehiculos ADD COLUMN active_vin varchar(17) GENERATED ALWAYS AS (IF(deleted_at IS NULL, vin, NULL)) VIRTUAL",
                "ALTER TABLE vehiculos ADD COLUMN active_plate varchar(8) GENERATED ALWAYS AS (IF(deleted_at IS NULL, plate, NULL)) VIRTUAL",
                "ALTER TABLE vehiculos ADD UNIQUE INDEX vehiculos_vin_activo_unico (active_vin)",
                "ALTER TABLE vehiculos ADD UNIQUE INDEX vehiculos_placa_activa_unica (active_plate)",
                "ALTER TABLE vehiculos ADD INDEX vehiculos_lista_idx (deleted_at, client_id, estatus_id)",
            ],
            [
                "ALTER TABLE vehiculos DROP INDEX vehiculos_vin_activo_unico",
                "ALTER TABLE vehiculos DROP INDEX vehiculos_placa_activa_unica",
                "ALTER TABLE vehiculos DROP INDEX vehiculos_lista_idx",
                "ALTER TABLE talleres DROP INDEX talleres_rfc_activo_unico",
                "ALTER TABLE talleres DROP INDEX talleres_direccion_activa_unica",
                "ALTER TABLE talleres DROP INDEX talleres_activos_idx",
                "ALTER TABLE clientes DROP INDEX clientes_telefono_activo_unico",
                "ALTER TABLE clientes DROP INDEX clientes_correo_activo_unico",
                "ALTER TABLE clientes DROP INDEX clientes_identidad_activa_unica",
                "ALTER TABLE clientes DROP INDEX clientes_lista_idx",
                "ALTER TABLE estatus DROP INDEX estatus_nombre_activo_unico",
                "ALTER TABLE vehiculos DROP COLUMN active_vin",
                "ALTER TABLE vehiculos DROP COLUMN active_plate",
                "ALTER TABLE talleres DROP COLUMN active_rfc",
                "ALTER TABLE talleres DROP COLUMN active_address",
                "ALTER TABLE clientes DROP COLUMN active_personal_phone",
                "ALTER TABLE clientes DROP COLUMN active_personal_email",
                "ALTER TABLE clientes DROP COLUMN active_identity",
                "ALTER TABLE estatus DROP COLUMN active_name",
            ],
        ),
        migrations.AddIndex(model_name='status', index=models.Index(fields=['name', 'deleted_at'], name='estatus_nombre_activo_idx')),
    ]
