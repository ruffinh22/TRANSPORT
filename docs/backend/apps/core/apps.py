# apps/core/apps.py
# =====================

from django.apps import AppConfig
from django.core.management.color import no_style
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    """Configuration de l'application Core pour RUMO RUSH."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core - Utilitaires et Services'
    
    def ready(self):
        """
        Méthode appelée quand Django a fini de charger l'application.
        Configure les composants transversaux.
        """
        try:
            # Vérifier la configuration
            self.validate_configuration()
            
            # Initialiser les services
            self.initialize_services()
            
            # Configurer le monitoring
            self.setup_monitoring()
            
            logger.info("Application Core initialisée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Core: {e}")
            raise
    
    def validate_configuration(self):
        """Valider la configuration requise."""
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured
        
        # Vérifier les settings obligatoires
        required_settings = {
            'CACHES': dict,
            'DATABASES': dict,
            'SECRET_KEY': str,
        }
        
        for setting_name, expected_type in required_settings.items():
            if not hasattr(settings, setting_name):
                raise ImproperlyConfigured(f"Setting manquant: {setting_name}")
            
            setting_value = getattr(settings, setting_name)
            if not isinstance(setting_value, expected_type):
                raise ImproperlyConfigured(
                    f"Setting {setting_name} doit être de type {expected_type.__name__}"
                )
        
        # Vérifier la configuration spécifique à RUMO RUSH
        self.validate_rumo_rush_config()
        
        logger.debug("Configuration validée")
    
    def validate_rumo_rush_config(self):
        """Valider la configuration spécifique à RUMO RUSH."""
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured
        from . import SUPPORTED_CURRENCIES, BUSINESS_LIMITS
        
        # Vérifier les devises
        if not SUPPORTED_CURRENCIES:
            raise ImproperlyConfigured("Aucune devise configurée")
        
        # Vérifier les limites métier
        required_limits = [
            'MIN_BET_AMOUNT', 'MAX_BET_AMOUNT', 
            'PLATFORM_COMMISSION_RATE', 'GAME_TIMEOUT_SECONDS'
        ]
        
        for limit in required_limits:
            if limit not in BUSINESS_LIMITS:
                raise ImproperlyConfigured(f"Limite métier manquante: {limit}")
        
        # Vérifier que les taux sont valides
        if not (0 < BUSINESS_LIMITS['PLATFORM_COMMISSION_RATE'] < 1):
            raise ImproperlyConfigured("PLATFORM_COMMISSION_RATE doit être entre 0 et 1")
        
        logger.debug("Configuration RUMO RUSH validée")
    
    def initialize_services(self):
        """Initialiser les services transversaux."""
        
        # Initialiser le cache
        self.initialize_cache()
        
        # Configurer les taux de change
        self.initialize_exchange_rates()
        
        # Préparer les validateurs
        self.initialize_validators()
        
        logger.debug("Services initialisés")
    
    def initialize_cache(self):
        """Initialiser et tester le cache."""
        from django.core.cache import cache
        from django.core.cache.backends.base import InvalidCacheBackendError
        
        try:
            # Test de connexion au cache
            cache.set('_health_check', 'ok', 10)
            if cache.get('_health_check') != 'ok':
                raise InvalidCacheBackendError("Cache non fonctionnel")
            
            cache.delete('_health_check')
            logger.debug("Cache initialisé et testé")
            
        except Exception as e:
            logger.error(f"Erreur de cache: {e}")
            # Ne pas faire échouer le démarrage pour le cache
    
    def initialize_exchange_rates(self):
        """Initialiser les taux de change par défaut."""
        from django.core.cache import cache
        from . import DEFAULT_EXCHANGE_RATES
        
        try:
            # Mettre les taux par défaut en cache
            for from_currency, rates in DEFAULT_EXCHANGE_RATES.items():
                for to_currency, rate in rates.items():
                    cache_key = f"exchange_rate:{from_currency}:{to_currency}"
                    cache.set(cache_key, rate, 86400)  # 24h
            
            logger.debug("Taux de change par défaut initialisés")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation des taux de change: {e}")
    
    def initialize_validators(self):
        """Pré-compiler les validateurs regex pour les performances."""
        try:
            import re
            from . import REGEX_PATTERNS
            
            # Compiler les patterns regex
            compiled_patterns = {}
            for name, pattern in REGEX_PATTERNS.items():
                compiled_patterns[name] = re.compile(pattern)
            
            # Stocker dans le module pour réutilisation
            import apps.core
            apps.core.COMPILED_PATTERNS = compiled_patterns
            
            logger.debug("Validateurs regex compilés")
            
        except Exception as e:
            logger.error(f"Erreur de compilation des regex: {e}")
    
    def setup_monitoring(self):
        """Configurer le monitoring et les métriques."""
        
        # Enregistrer les signaux pour monitoring
        self.connect_monitoring_signals()
        
        # Initialiser les métriques de santé
        self.initialize_health_metrics()
        
        logger.debug("Monitoring configuré")
    
    def connect_monitoring_signals(self):
        """Connecter les signaux pour le monitoring."""
        from django.db.models.signals import post_save, post_delete
        from django.contrib.auth.signals import user_logged_in, user_logged_out
        
        # Signaux d'authentification
        user_logged_in.connect(self.on_user_login, dispatch_uid='core_user_login')
        user_logged_out.connect(self.on_user_logout, dispatch_uid='core_user_logout')
        
        logger.debug("Signaux de monitoring connectés")
    
    def on_user_login(self, sender, request, user, **kwargs):
        """Handler pour connexion utilisateur."""
        try:
            from django.core.cache import cache
            from .utils import get_client_ip
            
            # Compter les connexions
            daily_logins = cache.get('daily_logins', 0)
            cache.set('daily_logins', daily_logins + 1, 86400)
            
            # Log pour audit
            logger.info(f"User login: {user.username} from {get_client_ip(request)}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de connexion: {e}")
    
    def on_user_logout(self, sender, request, user, **kwargs):
        """Handler pour déconnexion utilisateur."""
        try:
            if user:
                logger.info(f"User logout: {user.username}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement de déconnexion: {e}")
    
    def initialize_health_metrics(self):
        """Initialiser les métriques de santé de l'application."""
        from django.core.cache import cache
        
        try:
            # Réinitialiser certaines métriques au démarrage
            metrics = {
                'app_start_time': self.get_current_timestamp(),
                'total_requests': 0,
                'error_count': 0,
                'maintenance_mode': False
            }
            
            for key, value in metrics.items():
                cache.set(f'health_metric:{key}', value, None)  # Pas d'expiration
            
            logger.debug("Métriques de santé initialisées")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation des métriques: {e}")
    
    def get_current_timestamp(self):
        """Obtenir le timestamp actuel."""
        from django.utils import timezone
        return timezone.now().isoformat()
    
    def health_check(self):
        """Vérification de santé de l'application core."""
        try:
            checks = {
                'cache': self.check_cache_health(),
                'database': self.check_database_health(),
                'configuration': self.check_configuration_health()
            }
            
            all_healthy = all(checks.values())
            
            return all_healthy, checks
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_cache_health(self):
        """Vérifier la santé du cache."""
        try:
            from django.core.cache import cache
            
            test_key = '_core_health_check'
            test_value = 'healthy'
            
            cache.set(test_key, test_value, 10)
            retrieved = cache.get(test_key)
            cache.delete(test_key)
            
            return retrieved == test_value
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False
    
    def check_database_health(self):
        """Vérifier la santé de la base de données."""
        try:
            # Test de connexion simple
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            return result == (1,)
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def check_configuration_health(self):
        """Vérifier la santé de la configuration."""
        try:
            # Vérifier que les imports essentiels fonctionnent
            from . import SUPPORTED_CURRENCIES, BUSINESS_LIMITS, ERROR_MESSAGES
            
            # Vérifier que les données essentielles sont présentes
            if not SUPPORTED_CURRENCIES or not BUSINESS_LIMITS or not ERROR_MESSAGES:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration health check failed: {e}")
            return False
    
    @classmethod
    def get_app_info(cls):
        """Informations sur l'application."""
        return {
            'name': cls.verbose_name,
            'version': '1.0.0',
            'description': 'Services transversaux et utilitaires pour RUMO RUSH',
            'components': [
                'Middleware de sécurité et performance',
                'Système de permissions granulaire', 
                'Pagination intelligente',
                'Gestion d\'exceptions centralisée',
                'Validateurs métier',
                'Décorateurs utilitaires',
                'Utilitaires de conversion et formatage',
                'Cache et optimisations'
            ],
            'dependencies': [
                'Django >= 4.2',
                'Django REST Framework',
                'Redis (cache)',
                'PostgreSQL',
                'bcrypt (hash)',
                'cryptography (chiffrement)'
            ],
            'features': {
                'security': [
                    'Rate limiting intelligent',
                    'Validation des entrées',
                    'Chiffrement AES-256',
                    'Audit trail complet'
                ],
                'performance': [
                    'Cache multi-niveaux',
                    'Pagination optimisée',
                    'Compression des réponses',
                    'Monitoring des performances'
                ],
                'business': [
                    'Gestion multi-devises',
                    'Calculs financiers précis',
                    'Validation métier',
                    'Workflows automatisés'
                ]
            }
        }
