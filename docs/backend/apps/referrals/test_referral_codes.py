"""
Tests pour le système de gestion des codes de parrainage.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from decimal import Decimal

from ..models import ReferralCode, ReferralCodeClick, ReferralCodeShare, Referral, ReferralProgram

User = get_user_model()


class ReferralCodeModelTests(TestCase):
    """Tests pour le modèle ReferralCode."""
    
    def setUp(self):
        """Initialiser les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_referral_code(self):
        """Tester la création d'un code de parrainage."""
        code = ReferralCode.objects.create(user=self.user)
        
        self.assertEqual(code.user, self.user)
        self.assertIsNotNone(code.code)
        self.assertTrue(code.code.startswith('REF-'))
        self.assertEqual(code.status, 'active')
        self.assertTrue(code.is_active)
    
    def test_referral_code_uniqueness(self):
        """Tester l'unicité des codes."""
        code1 = ReferralCode.objects.create(user=self.user)
        code2 = ReferralCode.objects.create(user=self.user)
        
        self.assertNotEqual(code1.code, code2.code)
    
    def test_referral_code_has_capacity(self):
        """Tester la capacité des codes."""
        code = ReferralCode.objects.create(
            user=self.user,
            max_uses=10,
            current_uses=5
        )
        
        self.assertTrue(code.has_capacity)
        self.assertEqual(code.current_uses, 5)
    
    def test_referral_code_no_capacity(self):
        """Tester quand le code atteint sa limite."""
        code = ReferralCode.objects.create(
            user=self.user,
            max_uses=10,
            current_uses=10
        )
        
        self.assertFalse(code.has_capacity)
    
    def test_referral_code_unlimited_capacity(self):
        """Tester les codes sans limite d'utilisation."""
        code = ReferralCode.objects.create(
            user=self.user,
            max_uses=0,  # Illimité
            current_uses=1000
        )
        
        self.assertTrue(code.has_capacity)
    
    def test_referral_code_expiration(self):
        """Tester l'expiration des codes."""
        # Code expiré
        expired_code = ReferralCode.objects.create(
            user=self.user,
            expiration_date=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(expired_code.is_active)
        
        # Code actif
        active_code = ReferralCode.objects.create(
            user=self.user,
            expiration_date=timezone.now() + timedelta(days=1)
        )
        self.assertTrue(active_code.is_active)
    
    def test_referral_code_full_url(self):
        """Tester la génération de l'URL complète."""
        code = ReferralCode.objects.create(user=self.user)
        
        self.assertIn('signup', code.full_url.lower())
        self.assertIn(code.code, code.full_url)
    
    def test_referral_code_short_url(self):
        """Tester la génération de l'URL courte."""
        code = ReferralCode.objects.create(user=self.user)
        
        self.assertIsNotNone(code.short_url)
        self.assertIn(code.code[:6], code.short_url)
    
    def test_deactivate_referral_code(self):
        """Tester la désactivation d'un code."""
        code = ReferralCode.objects.create(user=self.user)
        self.assertTrue(code.is_active)
        
        code.deactivate()
        self.assertEqual(code.status, 'inactive')
        self.assertFalse(code.is_active)
    
    def test_activate_referral_code(self):
        """Tester l'activation d'un code."""
        code = ReferralCode.objects.create(
            user=self.user,
            status='inactive'
        )
        self.assertFalse(code.is_active)
        
        code.activate()
        self.assertEqual(code.status, 'active')
        self.assertTrue(code.is_active)


class ReferralCodeClickTests(TestCase):
    """Tests pour le tracking des clics."""
    
    def setUp(self):
        """Initialiser les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.code = ReferralCode.objects.create(user=self.user)
    
    def test_track_click(self):
        """Tester l'enregistrement d'un clic."""
        click = ReferralCodeClick.objects.create(
            code=self.code,
            visitor_ip='192.168.1.1',
            user_agent='Mozilla/5.0'
        )
        
        self.assertEqual(click.code, self.code)
        self.assertEqual(click.visitor_ip, '192.168.1.1')
        self.assertIsNotNone(click.clicked_at)
    
    def test_track_conversion(self):
        """Tester le tracking de conversion."""
        converted_user = User.objects.create_user(
            username='converted',
            email='converted@example.com',
            password='pass123'
        )
        
        click = ReferralCodeClick.objects.create(
            code=self.code,
            visitor_ip='192.168.1.1'
        )
        
        click.track_conversion(converted_user)
        
        self.assertEqual(click.converted_user, converted_user)
        self.assertIsNotNone(click.converted_at)
    
    def test_multiple_clicks_per_code(self):
        """Tester plusieurs clics sur le même code."""
        for i in range(5):
            ReferralCodeClick.objects.create(
                code=self.code,
                visitor_ip=f'192.168.1.{i}'
            )
        
        self.assertEqual(self.code.clicks.count(), 5)


class ReferralCodeShareTests(TestCase):
    """Tests pour le partage de codes."""
    
    def setUp(self):
        """Initialiser les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.code = ReferralCode.objects.create(user=self.user)
    
    def test_create_share(self):
        """Tester la création d'un partage."""
        share = ReferralCodeShare.objects.create(
            code=self.code,
            channel='whatsapp'
        )
        
        self.assertEqual(share.code, self.code)
        self.assertEqual(share.channel, 'whatsapp')
        self.assertIsNotNone(share.shared_at)
    
    def test_multiple_shares_per_channel(self):
        """Tester plusieurs partages sur le même canal."""
        for i in range(3):
            ReferralCodeShare.objects.create(
                code=self.code,
                channel='whatsapp'
            )
        
        shares = ReferralCodeShare.objects.filter(
            code=self.code,
            channel='whatsapp'
        )
        self.assertEqual(shares.count(), 3)
    
    def test_different_share_channels(self):
        """Tester les différents canaux de partage."""
        channels = ['whatsapp', 'telegram', 'email', 'facebook']
        
        for channel in channels:
            ReferralCodeShare.objects.create(
                code=self.code,
                channel=channel
            )
        
        self.assertEqual(self.code.shares.count(), 4)


class ReferralCodeAPITests(APITestCase):
    """Tests pour les endpoints API des codes de parrainage."""
    
    def setUp(self):
        """Initialiser les données de test."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_referral_codes(self):
        """Tester la liste des codes."""
        ReferralCode.objects.create(user=self.user)
        ReferralCode.objects.create(user=self.user)
        
        response = self.client.get('/api/v1/referrals/codes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_retrieve_referral_code(self):
        """Tester la récupération d'un code."""
        code = ReferralCode.objects.create(user=self.user)
        
        response = self.client.get(f'/api/v1/referrals/codes/{code.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], code.code)
    
    def test_create_referral_code_api(self):
        """Tester la création d'un code via API."""
        data = {
            'max_uses': 500,
            'expiration_date': None
        }
        
        response = self.client.post('/api/v1/referrals/codes/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('code', response.data)
    
    def test_share_referral_code(self):
        """Tester le partage d'un code."""
        code = ReferralCode.objects.create(user=self.user)
        
        data = {
            'channel': 'whatsapp',
            'message': 'Rejoins-moi!'
        }
        
        response = self.client.post(
            f'/api/v1/referrals/codes/{code.id}/share/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_get_code_stats(self):
        """Tester l'obtention des statistiques."""
        code = ReferralCode.objects.create(user=self.user)
        
        # Créer quelques clics
        for i in range(5):
            ReferralCodeClick.objects.create(
                code=code,
                visitor_ip=f'192.168.1.{i}'
            )
        
        response = self.client.get(f'/api/v1/referrals/codes/{code.id}/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_clicks'], 5)
    
    def test_deactivate_code_api(self):
        """Tester la désactivation via API."""
        code = ReferralCode.objects.create(user=self.user)
        
        response = self.client.post(f'/api/v1/referrals/codes/{code.id}/deactivate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier la désactivation
        code.refresh_from_db()
        self.assertEqual(code.status, 'inactive')
    
    def test_activate_code_api(self):
        """Tester l'activation via API."""
        code = ReferralCode.objects.create(user=self.user, status='inactive')
        
        response = self.client.post(f'/api/v1/referrals/codes/{code.id}/activate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier l'activation
        code.refresh_from_db()
        self.assertEqual(code.status, 'active')
    
    def test_get_conversions(self):
        """Tester l'obtention des conversions."""
        code = ReferralCode.objects.create(user=self.user)
        
        # Créer un utilisateur converti
        converted_user = User.objects.create_user(
            username='converted',
            email='converted@example.com',
            password='pass123'
        )
        
        click = ReferralCodeClick.objects.create(
            code=code,
            visitor_ip='192.168.1.1'
        )
        click.track_conversion(converted_user)
        
        response = self.client.get(f'/api/v1/referrals/codes/{code.id}/conversions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_conversions'], 1)
    
    def test_get_analytics(self):
        """Tester les analytiques globales."""
        ReferralCode.objects.create(user=self.user)
        ReferralCode.objects.create(user=self.user)
        
        response = self.client.get('/api/v1/referrals/codes/analytics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_codes'], 2)


class ReferralCodeSignalTests(TestCase):
    """Tests pour les signaux automatiques."""
    
    def test_auto_create_code_on_user_signup(self):
        """Tester la création automatique d'un code à l'inscription."""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='pass123'
        )
        
        # Vérifier que le code a été créé automatiquement
        code = ReferralCode.objects.filter(user=user).first()
        
        self.assertIsNotNone(code)
        self.assertEqual(code.user, user)
        self.assertTrue(code.is_active)


class ReferralCodeIntegrationTests(TestCase):
    """Tests d'intégration complets."""
    
    def setUp(self):
        """Initialiser les données de test."""
        # Créer le programme de parrainage
        self.program = ReferralProgram.objects.create(
            name='Programme de parrainage standard',
            description='Programme standard',
            commission_type='percentage',
            commission_rate=Decimal('10.00'),
            status='active',
            is_default=True
        )
        
        self.referrer = User.objects.create_user(
            username='referrer',
            email='referrer@example.com',
            password='pass123'
        )
        
        self.referred = User.objects.create_user(
            username='referred',
            email='referred@example.com',
            password='pass123'
        )
    
    def test_complete_referral_flow(self):
        """Tester le flux complet de parrainage."""
        # 1. Obtenir le code du parrain
        referrer_code = ReferralCode.objects.get(user=self.referrer)
        
        # 2. Simuler un clic
        click = ReferralCodeClick.objects.create(
            code=referrer_code,
            visitor_ip='192.168.1.1'
        )
        
        # 3. Marquer comme conversion
        click.track_conversion(self.referred)
        
        # 4. Créer la relation de parrainage
        referral = Referral.objects.create(
            referrer=self.referrer,
            referred=self.referred,
            program=self.program
        )
        
        # 5. Vérifier le résultat
        self.assertEqual(referral.referrer, self.referrer)
        self.assertEqual(referral.referred, self.referred)
        self.assertTrue(click.converted_user == self.referred)
        
        # 6. Vérifier les statistiques
        stats = referrer_code.clicks.filter(converted_user__isnull=False).count()
        self.assertEqual(stats, 1)
