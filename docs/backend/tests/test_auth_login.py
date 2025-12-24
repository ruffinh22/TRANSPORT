from django.test import TestCase
from rest_framework.test import APIClient

from tests.utils.user_verifier import UserVerifier


class AuthLoginTestCase(TestCase):
    """Tests pour l'endpoint de connexion (/api/v1/auth/login/)."""

    def setUp(self):
        self.client = APIClient()
        # Créer un utilisateur de test
        self.username = 'login_user'
        self.email = 'login_user@example.com'
        self.password = 'StrongPass123'
        UserVerifier.create_test_user(
            username=self.username,
            email=self.email,
            password=self.password,
            role='user'
        )

    def tearDown(self):
        UserVerifier.delete_test_user(self.username)

    def test_login_with_email(self):
        """La connexion doit fonctionner lorsque l'on envoie l'email dans `username`."""
        url = '/api/v1/auth/login/'
        data = {'username': self.email, 'password': self.password}
        resp = self.client.post(url, data, format='json', HTTP_X_FORWARDED_FOR='1.1.1.1')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_with_username(self):
        """La connexion doit fonctionner lorsque l'on envoie le username."""
        url = '/api/v1/auth/login/'
        data = {'username': self.username, 'password': self.password}
        resp = self.client.post(url, data, format='json', HTTP_X_FORWARDED_FOR='2.2.2.2')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_with_email_field(self):
        """La connexion doit fonctionner lorsque l'API reçoit explicitement `email`."""
        url = '/api/v1/auth/login/'
        data = {'email': self.email, 'password': self.password}
        resp = self.client.post(url, data, format='json', HTTP_X_FORWARDED_FOR='3.3.3.3')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
