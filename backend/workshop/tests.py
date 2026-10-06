from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from .models import Client, PostalCode, User, Workshop


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

    def test_admin_creates_workshop_and_reception_cannot(self):
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
        workshop['rfc'] = 'DEF010101AAA'
        self.assertEqual(self.client.post('/api/talleres/', workshop).status_code, 403)

    def test_only_administrator_suspends_client_and_list_paginates(self):
        self.client.force_login(self.administrator)
        for number in range(12):
            data = self.payload(full_name=f'Cliente Lista {number} Prueba', personal_phone=f'5530000{number:03d}', personal_email=f'lista{number}@example.com')
            self.assertEqual(self.client.post('/api/clients/register/', data).status_code, 201)
        listed = self.client.get('/api/clients/?page=1&order=full_name&direction=asc')
        self.assertEqual(len(listed.json()['clients']), 10)
        self.assertEqual(listed.json()['total'], 12)
        client_id = listed.json()['clients'][0]['id']
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/suspend/').status_code, 200)
        self.assertEqual(Client.objects.get(pk=client_id).status, 'SUSPENDIDO')
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/activate/').status_code, 200)
        self.assertEqual(Client.objects.get(pk=client_id).status, 'ACTIVO')
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/suspend/').status_code, 200)
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/suspend/').status_code, 403)
        self.assertEqual(self.client.post(f'/api/clients/{client_id}/activate/').status_code, 403)
