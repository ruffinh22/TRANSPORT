"""Tests pour les modèles utilisateurs"""
import pytest
from django.contrib.auth import authenticate
from django.utils import timezone
from apps.users.models import User, UserSession
from apps.common.models import Role, Permission


@pytest.mark.django_db
class TestUserModel:
    """Tests pour le modèle User"""
    
    def test_create_user(self):
        """Test la création d'un utilisateur"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        assert user.email == 'test@example.com'
        assert user.phone == '+237670000000'
        assert user.get_full_name() == 'John Doe'
        assert user.check_password('password123')
        assert user.is_active is True
        assert user.email_verified is False
    
    def test_create_superuser(self):
        """Test la création d'un superuser"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            phone='+237670000001',
            first_name='Admin',
            last_name='User',
            password='password123'
        )
        
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.is_active is True
    
    def test_user_email_unique(self):
        """Test l'unicité de l'email"""
        User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        with pytest.raises(Exception):
            User.objects.create_user(
                email='test@example.com',
                phone='+237670000001',
                first_name='Jane',
                last_name='Doe',
                password='password123'
            )
    
    def test_verify_email(self):
        """Test la vérification de l'email"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        assert user.email_verified is False
        user.verify_email()
        
        assert user.email_verified is True
        assert user.email_verified_at is not None
    
    def test_verify_phone(self):
        """Test la vérification du téléphone"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        assert user.phone_verified is False
        user.verify_phone()
        
        assert user.phone_verified is True
        assert user.phone_verified_at is not None
    
    def test_block_user(self):
        """Test le blocage d'un utilisateur"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        assert user.is_blocked is False
        user.block('Raison de blocage')
        
        assert user.is_blocked is True
        assert user.block_reason == 'Raison de blocage'
        assert user.blocked_at is not None
    
    def test_unblock_user(self):
        """Test le déblocage d'un utilisateur"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        user.block('Test')
        assert user.is_blocked is True
        
        user.unblock()
        assert user.is_blocked is False
        assert user.blocked_at is None
    
    def test_lock_login(self):
        """Test le verrouillage de la connexion"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        assert user.failed_login_attempts == 0
        
        # 5 tentatives
        for _ in range(5):
            user.lock_login()
        
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
    
    def test_is_fully_verified(self):
        """Test la vérification complète"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        assert user.is_fully_verified is False
        
        user.verify_email()
        assert user.is_fully_verified is False
        
        user.verify_phone()
        assert user.is_fully_verified is False
        
        user.verify_document(user)
        assert user.is_fully_verified is True


@pytest.mark.django_db
class TestUserSession:
    """Tests pour les sessions utilisateurs"""
    
    def test_create_session(self):
        """Test la création d'une session"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        session = UserSession.objects.create(
            user=user,
            refresh_token='test_token',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        assert session.is_active is True
        assert session.user == user
    
    def test_logout_session(self):
        """Test la déconnexion d'une session"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        session = UserSession.objects.create(
            user=user,
            refresh_token='test_token',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        session.logout()
        
        assert session.is_active is False
        assert session.logged_out_at is not None
    
    def test_is_expired(self):
        """Test la vérification d'expiration"""
        user = User.objects.create_user(
            email='test@example.com',
            phone='+237670000000',
            first_name='John',
            last_name='Doe',
            password='password123'
        )
        
        # Session expirée
        expired_session = UserSession.objects.create(
            user=user,
            refresh_token='expired_token',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        
        assert expired_session.is_expired() is True
        
        # Session valide
        valid_session = UserSession.objects.create(
            user=user,
            refresh_token='valid_token',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        assert valid_session.is_expired() is False
