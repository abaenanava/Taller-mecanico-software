from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from .models import Client, PostalCode, Status, User, Vehicle, Workshop


PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32


class ClientRegistrationApiTests(TestCase):
    """Prueba el recorrido REST completo que consumen Administrador y Recepcionista."""

    def setUp(self):
        self.administrator = User.objects.create_user(username='admin_test', password='PruebaSegura2026!', role=User.Role.ADMIN)
        self.receptionist = User.objects.create_user(username='reception_test', password='PruebaSegura2026!', role=User.Role.RECEPTION)
        self.viewer = User.objects.create_user(username='viewer_test', password='PruebaSegura2026!', role=User.Role.VIEWER)
        PostalCode.objects.create(
            cp='06000', neighborhood='Centro', settlement_type='Colonia',
            municipality='Cuauhtémoc', state='Ciudad de México',
        )
        self.workshop = Workshop.objects.create(name='Taller Pruebas', street='Calle Uno', neighborhood='Centro', municipality='Ciudad de México', state='Ciudad de México', postal_code='01000', business_name='Taller Pruebas SA', phone='+525511111111', rfc='TLP010101AAA', contact_email='taller@example.com', photo=SimpleUploadedFile('taller.png', PNG, content_type='image/png'))

    def payload(self, **overrides):
        data = {
            'full_name': 'María López Hernández', 'alternate_contact_name': 'José López', 'age': '30',
            'birth_date': date(1996, 5, 12).isoformat(), 'personal_phone': '5512345678', 'work_phone': '5587654321',
            'street': 'Av. Reforma 100', 'neighborhood': 'Centro', 'municipality': 'Cuauhtémoc',
            'state': 'Ciudad de México', 'postal_code': '06000', 'personal_email': 'maria@example.com',
            'work_email': 'maria.trabajo@example.com',
            'workshop_id': str(self.workshop.id),
            'photo': SimpleUploadedFile('cliente.png', PNG, content_type='image/png'),
        }
        data.update(overrides)
        return data

    def multipart_put(self, url, data):
        """El cliente de pruebas codifica explícitamente PUT multipart como lo hace FormData."""
        body = encode_multipart(BOUNDARY, {key: value for key, value in data.items() if value is not None})
        return self.client.generic('PUT', url, body, content_type=MULTIPART_CONTENT)

    def test_anonymous_user_is_rejected(self):
        self.assertEqual(self.client.post('/api/clients/register/', self.payload()).status_code, 401)

    def test_viewer_cannot_manage_clients(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post('/api/clients/register/', self.payload()).status_code, 403)
        self.assertEqual(self.client.get('/api/clients/').status_code, 403)

    def test_administrator_and_receptionist_complete_client_flow(self):
        for number, account in enumerate((self.administrator, self.receptionist), start=1):
            with self.subTest(role=account.role):
                self.client.force_login(account)
                data = self.payload(
                    full_name=f'Cliente Prueba {number} Apellido', personal_phone=f'551234567{number}',
                    personal_email=f'cliente{number}@example.com',
                )
                created = self.client.post('/api/clients/register/', data)
                self.assertEqual(created.status_code, 201, created.content.decode())
                self.assertEqual(created.json()['detail'], 'Registro guardado exitosamente')
                client_id = created.json()['client']['id']

                listed = self.client.get('/api/clients/')
                self.assertEqual(listed.status_code, 200)
                self.assertIn(client_id, [item['id'] for item in listed.json()['clients']])

                edited = self.payload(
                    full_name=f'Cliente Prueba {number} Apellido', personal_phone=f'551234567{number}',
                    personal_email=f'cliente{number}@example.com', street='Calle actualizada 200', photo=None,
                )
                updated = self.multipart_put(f'/api/clients/{client_id}/', edited)
                self.assertEqual(updated.status_code, 200)
                self.assertEqual(updated.json()['client']['street'], 'Calle actualizada 200')

                duplicate = self.client.post('/api/clients/register/', self.payload(
                    full_name=f'Otro Nombre {number} Apellido', personal_phone=f'551234567{number}',
                    personal_email=f'otro{number}@example.com',
                ))
                self.assertEqual(duplicate.status_code, 409)
                self.assertEqual(Client.objects.filter(personal_phone=f'+52551234567{number}').count(), 1)
                self.client.logout()

    def test_update_excludes_own_record_but_rejects_other_client_data(self):
        self.client.force_login(self.receptionist)
        first = self.client.post('/api/clients/register/', self.payload()).json()['client']
        self.client.post('/api/clients/register/', self.payload(
            full_name='Ana García Pérez', birth_date='1990-01-01', personal_phone='5599999999',
            personal_email='ana@example.com', photo=SimpleUploadedFile('ana.png', PNG, content_type='image/png'),
        ))
        response = self.multipart_put(f"/api/clients/{first['id']}/", self.payload(personal_phone='5599999999', photo=None))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Client.objects.count(), 2)

    def test_validation_returns_field_messages(self):
        self.client.force_login(self.receptionist)
        response = self.client.post('/api/clients/register/', self.payload(personal_phone='123', work_phone='ABC', postal_code='ABC'))
        self.assertEqual(response.status_code, 422)
        self.assertIn('personal_phone', response.json()['fields'])
        self.assertIn('work_phone', response.json()['fields'])
        self.assertIn('postal_code', response.json()['fields'])

    def test_postal_code_lookup_and_address_catalog_validation(self):
        """El catálogo se consulta por API y bloquea combinaciones que no le pertenecen."""
        self.client.force_login(self.receptionist)
        lookup = self.client.get('/api/codigos-postales/06000/')
        self.assertEqual(lookup.status_code, 200)
        self.assertTrue(lookup.json()['verified'])
        self.assertEqual(lookup.json()['data']['municipality'], 'Cuauhtémoc')
        self.assertIn('Centro', [item['name'] for item in lookup.json()['data']['neighborhoods']])

        mismatch = self.client.post('/api/clients/register/', self.payload(neighborhood='Colonia incorrecta'))
        self.assertEqual(mismatch.status_code, 422)
        self.assertIn('neighborhood', mismatch.json()['fields'])

        manual = self.client.post('/api/clients/register/', self.payload(
            full_name='Cliente CP Manual', personal_phone='5577777777', personal_email='manual@example.com',
            postal_code='99999', neighborhood='Colonia Manual', municipality='Municipio Manual', state='Estado Manual',
        ))
        self.assertEqual(manual.status_code, 201, manual.content.decode())

    def test_administrator_and_receptionist_can_create_workshops(self):
        workshop = {
            'name': 'Taller Norte', 'street': 'Avenida Uno', 'neighborhood': 'Centro', 'municipality': 'Monterrey',
            'state': 'Nuevo León', 'postal_code': '64000', 'business_name': 'Taller Norte SA',
            'phone': '5511111111', 'rfc': 'ABC010101AAA', 'contact_email': 'norte@example.com',
            'photo': SimpleUploadedFile('taller.png', PNG, content_type='image/png'),
        }
        self.client.force_login(self.administrator)
        self.assertEqual(self.client.post('/api/talleres/', workshop).status_code, 201)
        workshop['photo'] = SimpleUploadedFile('taller2.png', PNG, content_type='image/png')
        self.assertEqual(self.client.post('/api/talleres/', workshop).status_code, 409)
        workshop['rfc'] = 'RFC-MALO'
        self.assertEqual(self.client.post('/api/talleres/', workshop).status_code, 422)
        self.client.force_login(self.receptionist)
        workshop.update(name='Taller Recepción', street='Avenida Dos', rfc='DEF010101AAA')
        workshop['photo'] = SimpleUploadedFile('taller-recepcion.png', PNG, content_type='image/png')
        self.assertEqual(self.client.post('/api/talleres/', workshop).status_code, 201)

    def test_administrator_and_receptionist_change_client_status_and_list_paginates(self):
        self.client.force_login(self.administrator)
        for number in range(12):
            data = self.payload(full_name=f'Cliente Lista {number} Prueba', personal_phone=f'5530000{number:03d}', personal_email=f'lista{number}@example.com')
            self.assertEqual(self.client.post('/api/clients/register/', data).status_code, 201)
        listed = self.client.get('/api/clients/?page=1&order=full_name&direction=asc')
        self.assertEqual(len(listed.json()['clients']), 10)
        self.assertEqual(listed.json()['total'], 12)
        client_id = listed.json()['clients'][0]['id']
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/suspend/').status_code, 200)
        self.assertEqual(Client.objects.get(pk=client_id).estatus.name, 'suspendido')
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/activate/').status_code, 200)
        self.assertEqual(Client.objects.get(pk=client_id).estatus.name, 'activo')
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/suspend/').status_code, 200)
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/activate/').status_code, 200)
        self.assertEqual(Client.objects.get(pk=client_id).estatus.name, 'activo')
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/suspend/').status_code, 200)
        self.assertEqual(Client.objects.get(pk=client_id).estatus.name, 'suspendido')
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/suspend/').status_code, 403)
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/activate/').status_code, 403)

    def test_status_soft_delete_keeps_database_record_and_hides_it(self):
        self.client.force_login(self.administrator)
        created = self.client.post('/api/estatus/', data='{"name":"pausado","description":"Pausa temporal."}', content_type='application/json')
        self.assertEqual(created.status_code, 201, created.content.decode())
        status_id = created.json()['status']['id']
        self.assertEqual(self.client.post('/api/estatus/', data='{"name":"PAUSADO","description":"Duplicado."}', content_type='application/json').status_code, 409)
        deleted = self.client.delete(f'/api/estatus/{status_id}/')
        self.assertEqual(deleted.status_code, 200)
        self.assertIsNotNone(Status.all_objects.get(pk=status_id).deleted_at)
        self.assertNotIn(status_id, [item['id'] for item in self.client.get('/api/estatus/').json()['statuses']])
        base = Status.objects.get(name='activo')
        self.assertEqual(self.client.delete(f'/api/estatus/{base.id}/').status_code, 400)

    def test_vehicle_requires_active_client_and_unique_identifiers(self):
        self.client.force_login(self.administrator)
        client_id = self.client.post('/api/clients/register/', self.payload()).json()['client']['id']
        payload = {'plate': 'ABC-123-D', 'vin': '1HGCM82633A004352', 'brand': 'Honda', 'model': 'Civic', 'year': 2026, 'version': 'EX', 'color': 'Azul'}
        created = self.client.post(f'/api/clients/{client_id}/vehicles/', data=__import__('json').dumps(payload), content_type='application/json')
        self.assertEqual(created.status_code, 201, created.content.decode())
        self.assertEqual(created.json()['vehicle']['status'], 'activo')
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/vehicles/', data=__import__('json').dumps(payload), content_type='application/json').status_code, 409)
        self.client.post(f'/api/clients/{client_id}/suspend/')
        payload.update({'plate': 'DEF-456-G', 'vin': '1M8GDM9AXKP042788'})
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/vehicles/', data=__import__('json').dumps(payload), content_type='application/json').status_code, 422)


class VehicleLookupApiTests(TestCase):
    """VEH-CONSULTA-001: búsqueda exacta y permisos sin cuentas superusuario."""

    URL = '/api/vehicles/lookup/'

    @classmethod
    def setUpTestData(cls):
        cls.administrator = User.objects.create_user(username='lookup_admin', role=User.Role.ADMIN)
        cls.receptionist = User.objects.create_user(username='lookup_reception', role=User.Role.RECEPTION)
        cls.viewer = User.objects.create_user(username='lookup_viewer', role=User.Role.VIEWER)
        cls.technician = User.objects.create_user(username='lookup_technician', role=User.Role.TECHNICIAN)
        cls.active, _ = Status.objects.get_or_create(name='activo', defaults={'description': 'Activo'})
        cls.suspended, _ = Status.objects.get_or_create(name='suspendido', defaults={'description': 'Suspendido'})
        cls.workshop = Workshop.objects.create(
            name='Taller Consulta', street='Calle Consulta 1', neighborhood='Centro',
            municipality='Ciudad de México', state='Ciudad de México', postal_code='06000',
            business_name='Taller Consulta SA', phone='+525511111111', rfc='TCO010101AAA',
            contact_email='consulta@example.com', photo='fixtures/taller.png',
        )
        cls.customer = Client.objects.create(
            full_name='Cliente Consulta Ejemplo', alternate_contact_name='Contacto Ejemplo',
            age=30, birth_date=date(1996, 5, 12), personal_phone='+525522222222',
            work_phone='+525533333333', street='Calle Cliente 2', neighborhood='Centro',
            municipality='Ciudad de México', state='Ciudad de México', postal_code='06000',
            personal_email='clienteconsulta@example.com', work_email='', photo='fixtures/cliente.png',
            workshop=cls.workshop, estatus=cls.active,
        )
        cls.vehicle = Vehicle.objects.create(
            client=cls.customer, estatus=cls.active, plate='ABC-123-D', vin='1HGCM82633A004352',
            brand='Honda', model='Civic', year=2026, version='EX', color='Azul', mileage=12345,
        )

    def test_both_operational_roles_find_by_each_identifier(self):
        for account in (self.administrator, self.receptionist):
            self.assertFalse(account.is_superuser)
            self.client.force_login(account)
            for field, value in (('id', self.vehicle.id), ('vin', self.vehicle.vin), ('plate', self.vehicle.plate)):
                with self.subTest(role=account.role, field=field):
                    response = self.client.get(self.URL, {'field': field, 'value': value})
                    self.assertEqual(response.status_code, 200)
                    data = response.json()['vehicle']
                    self.assertEqual(data['id'], self.vehicle.id)
                    self.assertEqual(data['vin'], self.vehicle.vin)
                    self.assertEqual(data['plate'], self.vehicle.plate)
                    self.assertEqual(data['brand'], 'Honda')
                    self.assertEqual(data['mileage'], 12345)
                    self.assertEqual(data['client'], {'id': self.customer.id, 'full_name': self.customer.full_name})
                    self.assertEqual(data['workshop'], {'id': self.workshop.id, 'name': self.workshop.name})
                    self.assertEqual(set(data), {'id', 'plate', 'vin', 'brand', 'model', 'year', 'version', 'color', 'mileage', 'status', 'created_at', 'client', 'workshop'})
                    self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_normalizes_case_and_outer_spaces_without_substring_search(self):
        self.client.force_login(self.receptionist)
        for field, value in (('vin', '  1hgcm82633a004352  '), ('plate', '  abc-123-d  '), ('id', f'  {self.vehicle.id}  ')):
            with self.subTest(field=field):
                self.assertEqual(self.client.get(self.URL, {'field': field, 'value': value}).json()['vehicle']['id'], self.vehicle.id)
        partial = self.client.get(self.URL, {'field': 'plate', 'value': 'ABC'})
        self.assertEqual(partial.status_code, 422)

    def test_anonymous_and_non_operational_roles_are_rejected(self):
        self.assertEqual(self.client.get(self.URL, {'field': 'id', 'value': self.vehicle.id}).status_code, 401)
        for account in (self.viewer, self.technician):
            self.client.force_login(account)
            with self.subTest(role=account.role):
                response = self.client.get(self.URL, {'field': 'id', 'value': self.vehicle.id})
                self.assertEqual(response.status_code, 403)
                self.assertNotIn('vehicle', response.json())
        self.client.logout()

    def test_valid_unmatched_identifiers_return_vehicle_not_found(self):
        self.client.force_login(self.administrator)
        for field, value in (('id', (1 << 63) - 1), ('vin', '1M8GDM9AXKP042788'), ('plate', 'DEF-456-G')):
            with self.subTest(field=field):
                response = self.client.get(self.URL, {'field': field, 'value': value})
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {'detail': 'Vehículo no encontrado.'})

    def test_deleted_vehicle_client_or_workshop_is_not_visible(self):
        from django.utils import timezone
        self.client.force_login(self.administrator)
        for entity in (self.vehicle, self.customer, self.workshop):
            with self.subTest(model=type(entity).__name__):
                type(entity).all_objects.filter(pk=entity.pk).update(deleted_at=timezone.now())
                response = self.client.get(self.URL, {'field': 'id', 'value': self.vehicle.id})
                self.assertEqual(response.status_code, 404)
                type(entity).all_objects.filter(pk=entity.pk).update(deleted_at=None)

    def test_suspended_client_remains_searchable(self):
        Client.objects.filter(pk=self.customer.pk).update(estatus=self.suspended)
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.get(self.URL, {'field': 'id', 'value': self.vehicle.id}).status_code, 200)

    def test_invalid_fields_values_and_repeated_parameters_return_422(self):
        self.client.force_login(self.administrator)
        invalid_queries = [
            {}, {'field': 'id'}, {'value': '1'}, {'field': 'pk', 'value': '1'},
            {'field': 'client__id', 'value': '1'}, {'field': 'id', 'value': '0'},
            {'field': 'id', 'value': '-1'}, {'field': 'id', 'value': '1.0'},
            {'field': 'id', 'value': str(1 << 63)}, {'field': 'id', 'value': '9' * 200},
            {'field': 'id', 'value': '١'}, {'field': 'vin', 'value': 'INVALID'},
            {'field': 'vin', 'value': '1HGCM82633A00435I'},
            {'field': 'plate', 'value': 'ABC%123-D'},
            {'field': 'plate', 'value': 'ABC-١٢٣-D'},
            {'field': 'plate', 'value': "ABC' OR 1=1"},
            {'field': 'vin', 'value': '1HGCM82633A004352', 'extra': '1'},
            {'field': 'plate', 'value': ' ' * 129 + 'ABC-123-D'},
        ]
        for query in invalid_queries:
            with self.subTest(query=query):
                response = self.client.get(self.URL, query)
                self.assertEqual(response.status_code, 422)
                self.assertIn('fields', response.json())
                self.assertNotIn('vehicle', response.json())
        for query in ('field=id&field=vin&value=1', 'field=id&value=1&value=2'):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(self.URL + '?' + query).status_code, 422)

    def test_lookup_is_read_only_and_id_is_automatic(self):
        self.assertIsInstance(self.vehicle.id, int)
        self.assertGreater(self.vehicle.id, 0)
        from django.db.models import BigAutoField
        self.assertIsInstance(Vehicle._meta.get_field('id'), BigAutoField)
        self.client.force_login(self.administrator)
        before = Vehicle.objects.count()
        self.assertEqual(self.client.post(self.URL, {'field': 'id', 'value': self.vehicle.id}).status_code, 405)
        self.assertEqual(self.client.get(self.URL, {'field': 'id', 'value': self.vehicle.id}).status_code, 200)
        self.assertEqual(Vehicle.objects.count(), before)

    def test_repository_fetches_vehicle_and_names_in_one_query(self):
        from .facades import VehicleFacade
        with self.assertNumQueries(1):
            vehicle = VehicleFacade().lookup({'field': 'id', 'value': str(self.vehicle.id)})
            self.assertEqual(vehicle.client.full_name, self.customer.full_name)
            self.assertEqual(vehicle.client.workshop.name, self.workshop.name)
            self.assertEqual(vehicle.estatus.name, 'activo')


class VehicleUpdateApiTests(TestCase):
    """Regresión PATCH: límites, autorización e inmutabilidad de identificadores."""

    @classmethod
    def setUpTestData(cls):
        VehicleLookupApiTests.setUpTestData.__func__(cls)
        cls.other_vehicle = Vehicle.objects.create(
            client=cls.customer, estatus=cls.active, plate='DEF-456-G', vin='1M8GDM9AXKP042788',
            brand='Honda', model='Accord', year=2026, version='EX', color='Blanco', mileage=None,
        )

    @property
    def url(self):
        return f'/api/vehicles/{self.vehicle.id}/'

    def patch_vehicle(self, payload):
        import json
        return self.client.patch(self.url, data=json.dumps(payload), content_type='application/json')

    def test_both_roles_update_editable_fields_preserving_identity_and_associations(self):
        original_vin = self.vehicle.vin
        original_client_id = self.vehicle.client_id
        original_status_id = self.vehicle.estatus_id
        for index, account in enumerate((self.administrator, self.receptionist)):
            self.assertFalse(account.is_superuser)
            self.client.force_login(account)
            with self.subTest(role=account.role):
                payload = {'plate': ' ghi-789-j ' if index == 0 else 'JKL-012-M', 'brand': ' Toyota ', 'model': ' Corolla ', 'year': 2025, 'version': ' XLE ', 'color': ' Gris ', 'mileage': 42000 + index}
                response = self.patch_vehicle(payload)
                self.assertEqual(response.status_code, 200, response.content.decode())
                data = response.json()['vehicle']
                self.assertEqual(data['id'], self.vehicle.id)
                self.assertEqual(data['vin'], original_vin)
                self.assertEqual(data['plate'], payload['plate'].strip().upper())
                self.assertEqual(data['brand'], 'Toyota')
                self.assertEqual(data['mileage'], 42000 + index)
                self.assertEqual(data['client'], {'id': self.customer.id, 'full_name': self.customer.full_name})
                self.assertEqual(data['workshop'], {'id': self.workshop.id, 'name': self.workshop.name})
                self.assertEqual(response['Cache-Control'], 'private, no-store')
                self.vehicle.refresh_from_db()
                self.assertEqual(self.vehicle.client_id, original_client_id)
                self.assertEqual(self.vehicle.estatus_id, original_status_id)
                self.assertEqual(self.vehicle.vin, original_vin)

    def test_patch_omitted_fields_are_preserved_and_null_mileage_is_supported(self):
        self.client.force_login(self.receptionist)
        self.assertEqual(self.patch_vehicle({'color': 'Rojo'}).status_code, 200)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.plate, 'ABC-123-D')
        self.assertEqual(self.vehicle.brand, 'Honda')
        self.assertEqual(self.vehicle.mileage, 12345)
        self.assertEqual(self.patch_vehicle({'mileage': None}).status_code, 200)
        self.vehicle.refresh_from_db()
        self.assertIsNone(self.vehicle.mileage)
        self.assertEqual(self.vehicle.color, 'Rojo')
        self.assertEqual(self.patch_vehicle({'mileage': 0}).status_code, 200)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.mileage, 0)

    def test_rejects_immutable_and_unknown_fields_even_with_unchanged_values(self):
        self.client.force_login(self.administrator)
        fields = {'id': self.vehicle.id, 'vin': self.vehicle.vin, 'client': self.customer.id, 'client_id': self.customer.id, 'workshop': self.workshop.id, 'estatus': self.active.id, 'estatus_id': self.active.id, 'status': 'activo', 'created_at': '2026-01-01', 'arbitrary': 'value'}
        for field, value in fields.items():
            with self.subTest(field=field):
                response = self.patch_vehicle({field: value, 'color': 'Negro'})
                self.assertEqual(response.status_code, 422)
                self.assertIn(field, response.json()['fields'])
                self.vehicle.refresh_from_db()
                self.assertEqual(self.vehicle.color, 'Azul')
                self.assertEqual(self.vehicle.vin, '1HGCM82633A004352')

    def test_invalid_types_ranges_json_and_empty_body_never_partially_update(self):
        self.client.force_login(self.administrator)
        payloads = [
            {}, [], None, True, 123, 'text', {'year': '2025'}, {'year': True},
            {'year': 2025.0}, {'year': 1949}, {'year': date.today().year + 2},
            {'mileage': -1}, {'mileage': True}, {'mileage': '100'}, {'mileage': 1.5},
            {'mileage': 4294967296}, {'brand': None}, {'brand': []}, {'brand': 123},
            {'model': ''}, {'version': ' '}, {'color': 'A' * 51},
            {'plate': None}, {'plate': 'INVALID'}, {'plate': 'ABC-١٢٣-D'},
            {'plate': 'ABC-123-D', 'year': 1949, 'color': 'Negro'},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.patch_vehicle(payload)
                self.assertEqual(response.status_code, 422)
                self.assertIn('fields', response.json())
                self.vehicle.refresh_from_db()
                self.assertEqual(self.vehicle.color, 'Azul')
                self.assertEqual(self.vehicle.year, 2026)
        for body in ('{', '', '{"year":'):
            self.assertEqual(self.client.patch(self.url, data=body, content_type='application/json').status_code, 422)
        self.assertEqual(self.client.patch(self.url, data='color=Rojo', content_type='text/plain').status_code, 422)

    def test_plate_uniqueness_excludes_self_and_rejects_conflict_without_leak(self):
        self.client.force_login(self.administrator)
        self.assertEqual(self.patch_vehicle({'plate': ' abc-123-d '}).status_code, 200)
        response = self.patch_vehicle({'plate': self.other_vehicle.plate.lower(), 'color': 'Negro'})
        self.assertEqual(response.status_code, 409)
        self.assertIn('plate', response.json()['fields'])
        self.assertNotIn('vehicle', response.json())
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.plate, 'ABC-123-D')
        self.assertEqual(self.vehicle.color, 'Azul')

    def test_integrity_conflict_rolls_back_without_breaking_later_queries(self):
        from unittest.mock import patch
        self.client.force_login(self.administrator)
        # Simula una carrera tras la comprobación previa; la restricción MySQL sigue siendo real.
        with patch('workshop.repositories.VehicleRepository.plate_in_use', return_value=False):
            response = self.patch_vehicle({'plate': self.other_vehicle.plate, 'color': 'Negro'})
        self.assertEqual(response.status_code, 409)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.plate, 'ABC-123-D')
        self.assertEqual(self.vehicle.color, 'Azul')
        self.assertEqual(self.patch_vehicle({'color': 'Verde'}).status_code, 200)

    def test_session_and_operational_permissions_are_required(self):
        self.assertEqual(self.patch_vehicle({'color': 'Rojo'}).status_code, 401)
        for account in (self.viewer, self.technician):
            self.client.force_login(account)
            with self.subTest(role=account.role):
                self.assertEqual(self.patch_vehicle({'color': 'Rojo'}).status_code, 403)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.color, 'Azul')

    def test_missing_or_deleted_chain_and_out_of_range_ids_return_404(self):
        from django.utils import timezone
        self.client.force_login(self.administrator)
        for vehicle_id in (0, (1 << 63) - 1, 1 << 63):
            response = self.client.patch(f'/api/vehicles/{vehicle_id}/', data='{"color":"Rojo"}', content_type='application/json')
            self.assertEqual(response.status_code, 404)
        for entity in (self.vehicle, self.customer, self.workshop):
            with self.subTest(model=type(entity).__name__):
                type(entity).all_objects.filter(pk=entity.pk).update(deleted_at=timezone.now())
                self.assertEqual(self.patch_vehicle({'color': 'Rojo'}).status_code, 404)
                type(entity).all_objects.filter(pk=entity.pk).update(deleted_at=None)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.color, 'Azul')

    def test_csrf_required_and_valid_token_allows_patch(self):
        from django.test import Client as HttpClient
        browser = HttpClient(enforce_csrf_checks=True)
        browser.force_login(self.administrator)
        denied = browser.patch(self.url, data='{"color":"Rojo"}', content_type='application/json')
        self.assertEqual(denied.status_code, 403)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.color, 'Azul')
        token_response = browser.get('/api/auth/csrf/')
        self.assertEqual(token_response.status_code, 200)
        token = browser.cookies['csrftoken'].value
        allowed = browser.patch(self.url, data='{"color":"Rojo"}', content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(allowed.status_code, 200)

    def test_lookup_preserves_vin_and_reports_new_plate_after_update(self):
        self.client.force_login(self.receptionist)
        self.assertEqual(self.patch_vehicle({'plate': 'XYZ-321-A'}).status_code, 200)
        by_vin = self.client.get('/api/vehicles/lookup/', {'field': 'vin', 'value': self.vehicle.vin})
        self.assertEqual(by_vin.status_code, 200)
        self.assertEqual(by_vin.json()['vehicle']['plate'], 'XYZ-321-A')
        old_plate = self.client.get('/api/vehicles/lookup/', {'field': 'plate', 'value': 'ABC-123-D'})
        self.assertEqual(old_plate.status_code, 404)
        new_plate = self.client.get('/api/vehicles/lookup/', {'field': 'plate', 'value': 'XYZ-321-A'})
        self.assertEqual(new_plate.json()['vehicle']['id'], self.vehicle.id)
