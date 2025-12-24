# ==================================================
# 5. rumo_rush/celery.py - Configuration Celery Complète
# ==================================================

import os
from celery import Celery
from django.conf import settings
from kombu import Queue, Exchange

# Configuration environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.production')

# Création de l'instance Celery
app = Celery('rumo_rush')

# Configuration depuis les settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuration avancée des queues
app.conf.task_routes = {
    # Queue haute priorité pour les actions de jeu
    'apps.games.tasks.process_move': {'queue': 'high_priority'},
    'apps.games.tasks.check_timeout': {'queue': 'high_priority'},
    'apps.games.tasks.end_game': {'queue': 'high_priority'},
    
    # Queue paiements
    'apps.payments.tasks.*': {'queue': 'payments'},
    'apps.payments.tasks.process_payment': {'queue': 'payments'},
    'apps.payments.tasks.verify_payment': {'queue': 'payments'},
    
    # Queue analytics (moins prioritaire)
    'apps.analytics.tasks.*': {'queue': 'analytics'},
    'apps.referrals.tasks.*': {'queue': 'analytics'},
    
    # Queue maintenance (tâches lourdes)
    'apps.core.tasks.*': {'queue': 'maintenance'},
    'apps.games.tasks.cleanup_*': {'queue': 'maintenance'},
}

# Définition des queues avec priorités
app.conf.task_queues = (
    Queue('high_priority', 
          Exchange('high_priority'), 
          routing_key='high_priority',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('games', 
          Exchange('games'), 
          routing_key='games',
          queue_arguments={'x-max-priority': 5}),
    
    Queue('payments', 
          Exchange('payments'), 
          routing_key='payments',
          queue_arguments={'x-max-priority': 8}),
    
    Queue('analytics', 
          Exchange('analytics'), 
          routing_key='analytics',
          queue_arguments={'x-max-priority': 2}),
    
    Queue('maintenance', 
          Exchange('maintenance'), 
          routing_key='maintenance',
          queue_arguments={'x-max-priority': 1}),
)

# Configuration des tâches périodiques (Celery Beat)
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ============ TÂCHES HAUTE FRÉQUENCE ============
    
    # Vérification des timeouts de jeu toutes les 15 secondes
    'check-game-timeouts': {
        'task': 'apps.games.tasks.check_all_game_timeouts',
        'schedule': 15.0,
        'options': {'queue': 'high_priority'},
    },
    
    # Nettoyage des connexions WebSocket toutes les 30 secondes
    'cleanup-websocket-connections': {
        'task': 'apps.games.tasks.cleanup_disconnected_users',
        'schedule': 30.0,
        'options': {'queue': 'high_priority'},
    },
    
    # ============ TÂCHES MOYENNES FRÉQUENCE ============
    
    # Vérification des paiements en attente toutes les 2 minutes
    'check-pending-payments': {
        'task': 'apps.payments.tasks.check_pending_payments',
        'schedule': crontab(minute='*/2'),
        'options': {'queue': 'payments'},
    },
    
    # Vérification des payouts FeexPay en attente toutes les 10 minutes
    'check-pending-payouts': {
        'task': 'payments.check_all_pending_payouts',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'payments'},
    },
    
    # Mise à jour des classements toutes les 5 minutes
    'update-leaderboards': {
        'task': 'apps.games.tasks.update_live_leaderboards',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'games'},
    },
    
    # Nettoyage des invitations expirées toutes les 10 minutes
    'cleanup-expired-invitations': {
        'task': 'apps.games.tasks.cleanup_expired_invitations',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'maintenance'},
    },
    
    # Calcul des métriques temps réel toutes les 15 minutes
    'update-realtime-metrics': {
        'task': 'apps.analytics.tasks.update_realtime_metrics',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'analytics'},
    },
    
    # ============ TÂCHES QUOTIDIENNES ============
    
    # Calcul des commissions quotidiennes à 1h du matin
    'calculate-daily-commissions': {
        'task': 'apps.referrals.tasks.calculate_daily_commissions',
        'schedule': crontab(hour=1, minute=0),
        'options': {'queue': 'payments'},
    },
    
    # Nettoyage des parties abandonnées à 2h du matin
    'cleanup-abandoned-games': {
        'task': 'apps.games.tasks.cleanup_abandoned_games',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'maintenance'},
    },
    
    # Sauvegarde des statistiques quotidiennes à 3h du matin
    'backup-daily-stats': {
        'task': 'apps.analytics.tasks.backup_daily_statistics',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'maintenance'},
    },
    
    # Envoi du rapport quotidien à 8h du matin
    'send-daily-report': {
        'task': 'apps.core.tasks.send_daily_admin_report',
        'schedule': crontab(hour=8, minute=0),
        'options': {'queue': 'analytics'},
    },
    
    # Nettoyage des logs anciens à 23h
    'cleanup-old-logs': {
        'task': 'apps.core.tasks.cleanup_old_logs',
        'schedule': crontab(hour=23, minute=0),
        'options': {'queue': 'maintenance'},
    },
    
    # ============ TÂCHES HEBDOMADAIRES ============
    
    # Sauvegarde complète le dimanche à 2h du matin
    'weekly-full-backup': {
        'task': 'apps.core.tasks.create_full_backup',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
        'options': {'queue': 'maintenance'},
    },
    
    # Calcul des classements hebdomadaires le lundi à 6h
    'calculate-weekly-rankings': {
        'task': 'apps.games.tasks.calculate_weekly_rankings',
        'schedule': crontab(hour=6, minute=0, day_of_week=1),
        'options': {'queue': 'analytics'},
    },
    
    # Nettoyage approfondi de la base le samedi à 3h
    'deep-database-cleanup': {
        'task': 'apps.core.tasks.deep_database_cleanup',
        'schedule': crontab(hour=3, minute=0, day_of_week=6),
        'options': {'queue': 'maintenance'},
    },
    
    # ============ TÂCHES MENSUELLES ============
    
    # Archivage des données anciennes le 1er de chaque mois à 1h
    'monthly-data-archiving': {
        'task': 'apps.core.tasks.archive_old_data',
        'schedule': crontab(hour=1, minute=0, day_of_month=1),
        'options': {'queue': 'maintenance'},
    },
    
    # Rapport mensuel complet le 1er à 9h
    'monthly-admin-report': {
        'task': 'apps.analytics.tasks.generate_monthly_report',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),
        'options': {'queue': 'analytics'},
    },
}

# Configuration du timezone pour les tâches
app.conf.timezone = 'UTC'

# Auto-découverte des tâches dans les applications Django
app.autodiscover_tasks()

# Configuration pour le monitoring et debugging
@app.task(bind=True)
def debug_task(self):
    """Tâche de debug pour vérifier le bon fonctionnement de Celery."""
    print(f'Request: {self.request!r}')
    return 'Debug task completed successfully'

# Configuration des signaux pour monitoring
from celery.signals import task_prerun, task_postrun, task_failure

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwargs_extra):
    """Signal exécuté avant chaque tâche."""
    print(f"Début tâche: {task.name} (ID: {task_id})")

@task_postrun.connect  
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwargs_extra):
    """Signal exécuté après chaque tâche."""
    print(f"Fin tâche: {task.name} (ID: {task_id}) - État: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Signal exécuté en cas d'échec de tâche."""
    print(f"ÉCHEC tâche: {sender.name} (ID: {task_id}) - Erreur: {exception}")
    # Ici vous pourriez envoyer une alerte (Slack, Discord, Email)

# Configuration pour les workers en production
app.conf.update(
    # Optimisations de performance
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Sérialisation optimisée
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Compression pour économiser la bande passante
    task_compression='gzip',
    result_compression='gzip',
    
    # Configuration des résultats
    result_expires=3600,  # Les résultats expirent après 1 heure
    
    # Configuration avancée
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

print("⚡ Celery configuré avec succès pour RUMO RUSH")
try:
    print(f"📋 {len(app.conf.beat_schedule)} tâches périodiques programmées")
    print(f"🔄 {len(app.conf.task_queues)} queues de priorités configurées")
except Exception as e:
    print("📋 Configuration des tâches périodiques en cours...")
    print(f"🔄 Configuration des queues en cours...")
