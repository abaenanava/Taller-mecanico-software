from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from .models import Client, User


PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32


class ClientRegistrationApiTests(TestCase):
    """Prueba el recorrido REST completo que consumen Administrador y Recepcionista."""

    def setUp(self):
        self.administrator = User.objects.create_user(username='admin_test', password='PruebaSegura2026!', role=User.Role.ADMIN)
        self.receptionist = User.objects.create_user(username='reception_test', password='PruebaSegura2026!', role=User.Role.RECEPTION)
        self.viewer = User.objects.create_user(username='viewer_test', password='PruebaSegura2026!', role=User.Role.VIEWER)

    def payload(self, **overrides):
        data = {
            'full_name': 'María López Hernández', 'alternate_contact_name': 'José López', 'age': '30',
            'birth_date': date(1996, 5, 12).isoformat(), 'personal_phone': '5512345678', 'work_phone': '5587654321',
            'street': 'Av. Reforma 100', 'neighborhood': 'Centro', 'municipality': 'Cuauhtémoc',
            'state': 'Ciudad de México', 'postal_code': '06000', 'personal_email': 'maria@example.com',
            'work_email': 'maria.trabajo@example.com',
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
                self.assertEqual(created.status_code, 201)
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
