from django.test import TestCase
from tests.utils.user_verifier import UserVerifier


class UserVerifierTestCase(TestCase):
    """Tests pour l'utilitaire UserVerifier."""
    
    def tearDown(self):
        """Nettoie les utilisateurs de test après chaque test."""
        UserVerifier.delete_test_user('testuser')
        UserVerifier.delete_test_user('admin_user')
    
    def test_create_regular_user(self):
        """Test la création d'un utilisateur régulier."""
        user = UserVerifier.create_test_user(username='testuser')
        self.assertTrue(UserVerifier.verify_user_exists('testuser'))
        self.assertTrue(UserVerifier.verify_user_active(user))
        self.assertTrue(UserVerifier.verify_user_role(user, 'user'))
    
    def test_create_admin_user(self):
        """Test la création d'un utilisateur admin."""
        user = UserVerifier.create_test_user(
            username='admin_user',
            role='admin'
        )
        self.assertTrue(UserVerifier.verify_user_role(user, 'admin'))
    
    def test_get_user_info(self):
        """Test la récupération des infos utilisateur."""
        user = UserVerifier.create_test_user(username='testuser')
        info = UserVerifier.get_user_info(user)
        self.assertEqual(info['username'], 'testuser')
        self.assertEqual(info['email'], 'test@example.com')
        self.assertIn('user', info['roles'])
