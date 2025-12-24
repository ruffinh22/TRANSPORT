# apps/referrals/apps.py
# ======================

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_migrate
from django.db import models
import logging

logger = logging.getLogger(__name__)


class ReferralsConfig(AppConfig):
    """Configuration de l'application Referrals pour RUMO RUSH."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.referrals'
    verbose_name = _('Système de Parrainage')
    
    def ready(self):
        """
        Méthode appelée lors du démarrage de Django.
        Configure les signaux et vérifie les settings (SANS accès DB).
        """
        try:
            # Import des signaux pour automatisation
            import apps.referrals.signals
            logger.info("Signaux de parrainage chargés avec succès")
            
            # Vérification de la configuration (sans DB)
            self.check_referral_settings()
            
            # Connecter les initialisations DB APRÈS les migrations
            post_migrate.connect(self.post_migrate_handler, sender=self)
            
            logger.info("Application referrals initialisée (DB ops différées)")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'app referrals: {e}")
            raise
    
    def post_migrate_handler(self, sender, **kwargs):
        """
        Handler exécuté APRÈS les migrations.
        C'est ici qu'on fait les opérations DB.
        """
        try:
            # Initialisation des programmes par défaut
            self.setup_default_programs()
            
            # Configuration des tâches périodiques
            self.setup_periodic_tasks()
            
            logger.info("Initialisation post-migration terminée")
            
        except Exception as e:
            logger.warning(f"Erreur post-migration (non bloquante): {e}")
    
    def check_referral_settings(self):
        """Vérifier que tous les settings requis sont présents."""
        from django.conf import settings
        
        # Settings obligatoires
        required_settings = [
            'REFERRAL_SETTINGS',
            'GAME_SETTINGS',
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ImproperlyConfigured(
                f"Settings manquants pour l'app referrals: {', '.join(missing_settings)}"
            )
        
        # Vérifier la structure des settings
        self.validate_referral_settings_structure()
        
        logger.info("Configuration de parrainage validée")
    
    def validate_referral_settings_structure(self):
        """Valider la structure des settings de parrainage."""
        from django.conf import settings
        
        referral_settings = settings.REFERRAL_SETTINGS
        
        # Vérifier les clés obligatoires
        required_keys = [
            'COMMISSION_RATE',
            'PREMIUM_PRICE',
            'FREE_GAMES_LIMIT'
        ]
        
        for key in required_keys:
            if key not in referral_settings:
                raise ImproperlyConfigured(
                    f"Clé manquante dans REFERRAL_SETTINGS: {key}"
                )
        
        # Vérifier les types de données
        if not isinstance(referral_settings['COMMISSION_RATE'], (int, float)):
            raise ImproperlyConfigured(
                "COMMISSION_RATE doit être un nombre"
            )
        
        if referral_settings['COMMISSION_RATE'] <= 0 or referral_settings['COMMISSION_RATE'] > 50:
            raise ImproperlyConfigured(
                "COMMISSION_RATE doit être entre 0 et 50%"
            )
        
        # Vérifier la structure des prix premium
        premium_price = referral_settings['PREMIUM_PRICE']
        if not isinstance(premium_price, dict):
            raise ImproperlyConfigured(
                "PREMIUM_PRICE doit être un dictionnaire"
            )
        
        required_currencies = ['FCFA', 'EUR', 'USD']
        for currency in required_currencies:
            if currency not in premium_price:
                raise ImproperlyConfigured(
                    f"Devise manquante dans PREMIUM_PRICE: {currency}"
                )
    
    def setup_default_programs(self):
        """
        Créer le programme de parrainage par défaut si nécessaire.
        APPELÉ UNIQUEMENT APRÈS LES MIGRATIONS via post_migrate signal.
        """
        try:
            # Importer ici pour éviter les imports circulaires
            from apps.referrals.models import ReferralProgram
            from django.conf import settings
            
            # Vérifier si un programme par défaut existe
            default_program = ReferralProgram.objects.filter(is_default=True).first()
            
            if not default_program:
                # Créer le programme par défaut
                referral_settings = settings.REFERRAL_SETTINGS
                
                default_program = ReferralProgram.objects.create(
                    name="Programme Standard RUMO RUSH",
                    description="Programme de parrainage par défaut avec commission de 10%",
                    commission_type='percentage',
                    commission_rate=referral_settings['COMMISSION_RATE'],
                    min_bet_for_commission=settings.GAME_SETTINGS.get('MIN_BET_AMOUNTS', {}).get('FCFA', 1000),
                    free_games_limit=referral_settings['FREE_GAMES_LIMIT'],
                    status='active',
                    is_default=True
                )
                
                logger.info(f"Programme de parrainage par défaut créé: {default_program.name}")
            else:
                logger.info(f"Programme par défaut existant: {default_program.name}")
            
        except Exception as e:
            # Ne pas faire échouer le démarrage
            logger.warning(f"Impossible de créer le programme par défaut: {e}")
    
    def setup_periodic_tasks(self):
        """
        Configurer les tâches périodiques pour Celery Beat.
        APPELÉ UNIQUEMENT APRÈS LES MIGRATIONS via post_migrate signal.
        """
        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
            import json
            
            # Tâche de calcul des commissions (toutes les heures)
            hourly_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,  # À chaque heure pile
                hour='*',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            PeriodicTask.objects.get_or_create(
                name='Calcul des commissions de parrainage',
                defaults={
                    'crontab': hourly_schedule,
                    'task': 'apps.referrals.tasks.calculate_pending_commissions',
                    'enabled': True,
                }
            )
            
            # Tâche de nettoyage des bonus expirés (quotidien à 2h)
            daily_cleanup_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=2,
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            PeriodicTask.objects.get_or_create(
                name='Nettoyage des bonus expirés',
                defaults={
                    'crontab': daily_cleanup_schedule,
                    'task': 'apps.referrals.tasks.cleanup_expired_bonuses',
                    'enabled': True,
                }
            )
            
            # Tâche de calcul des statistiques (quotidien à 1h)
            stats_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=1,
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            PeriodicTask.objects.get_or_create(
                name='Calcul des statistiques de parrainage',
                defaults={
                    'crontab': stats_schedule,
                    'task': 'apps.referrals.tasks.update_referral_statistics',
                    'enabled': True,
                }
            )
            
            # Tâche de vérification des abonnements premium (quotidien à 6h)
            subscription_check_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=6,
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            PeriodicTask.objects.get_or_create(
                name='Vérification des abonnements premium',
                defaults={
                    'crontab': subscription_check_schedule,
                    'task': 'apps.referrals.tasks.check_premium_subscriptions',
                    'enabled': True,
                }
            )
            
            logger.info("Tâches périodiques de parrainage configurées")
            
        except Exception as e:
            logger.warning(f"Impossible de configurer les tâches périodiques: {e}")
    
    def health_check(self):
        """Vérification de santé de l'application."""
        try:
            from apps.referrals.models import ReferralProgram
            
            # Vérifier qu'un programme par défaut existe
            default_program = ReferralProgram.objects.filter(is_default=True, status='active').first()
            if not default_program:
                return False, "Aucun programme de parrainage par défaut actif"
            
            # Vérifier les settings
            from django.conf import settings
            if not hasattr(settings, 'REFERRAL_SETTINGS'):
                return False, "Configuration REFERRAL_SETTINGS manquante"
            
            return True, "Application referrals opérationnelle"
            
        except Exception as e:
            return False, f"Erreur dans l'app referrals: {str(e)}"
    
    @classmethod
    def get_app_info(cls):
        """Informations sur l'application."""
        return {
            'name': cls.verbose_name,
            'version': '1.0.0',
            'description': 'Système de parrainage multi-niveaux avec commissions automatiques',
            'features': [
                'Programmes de parrainage configurables',
                'Commissions automatiques sur les parties',
                'Abonnements premium pour gains augmentés',
                'Système de bonus et récompenses',
                'Statistiques détaillées',
                'Limites anti-abus',
                'Notifications temps réel'
            ],
            'models_count': 7,
            'supports_currencies': ['FCFA', 'EUR', 'USD'],
            'commission_types': ['percentage', 'fixed', 'tiered']
        } 
