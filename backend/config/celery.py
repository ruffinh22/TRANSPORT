"""
Celery configuration for TKF Project
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('tkf')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery Beat Schedule - Tâches planifiées
app.conf.beat_schedule = {
    # Générer les trajets quotidiens à 00:00
    'generate-daily-trips': {
        'task': 'apps.trips.tasks.generate_daily_trips',
        'schedule': crontab(hour=0, minute=0),
    },
    
    # Envoyer les rappels de trajets 1 heure avant
    'send-trip-reminders': {
        'task': 'apps.trips.tasks.send_trip_reminders',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
    },
    
    # Mettre à jour le statut des billets expirés
    'update-expired-tickets': {
        'task': 'apps.tickets.tasks.update_expired_tickets',
        'schedule': crontab(hour='*/1', minute=0),  # Chaque heure
    },
    
    # Réconcilier les paiements
    'reconcile-payments': {
        'task': 'apps.payments.tasks.reconcile_payments',
        'schedule': crontab(hour=2, minute=0),  # À 2h du matin
    },
    
    # Générer les rapports de recettes quotidiens
    'generate-daily-revenue-report': {
        'task': 'apps.revenues.tasks.generate_daily_report',
        'schedule': crontab(hour=23, minute=59),  # À 23h59
    },
    
    # Nettoyer les fichiers temporaires
    'cleanup-temp-files': {
        'task': 'apps.common.tasks.cleanup_temp_files',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Chaque dimanche à 3h
    },
    
    # Envoyer alertes de maintenance des véhicules
    'send-maintenance-alerts': {
        'task': 'apps.vehicles.tasks.send_maintenance_alerts',
        'schedule': crontab(hour=6, minute=0),  # À 6h du matin
    },
    
    # Archiver les anciennes données
    'archive-old-data': {
        'task': 'apps.common.tasks.archive_old_data',
        'schedule': crontab(day_of_week=6, hour=4, minute=0),  # Samedi à 4h
    },
}

# Configuration Celery
app.conf.update(
    # Timezone
    timezone='Africa/Bamako',
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_extended=True,
    
    # Task routing
    task_routes={
        'apps.emails.tasks.*': {'queue': 'emails'},
        'apps.payments.tasks.*': {'queue': 'payments'},
        'apps.trips.tasks.*': {'queue': 'trips'},
        'apps.parcels.tasks.*': {'queue': 'parcels'},
    },
    
    # Task compression
    task_compression='gzip',
    result_compression='gzip',
    
    # Error handling
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

@app.task(bind=True)
def debug_task(self):
    """Task de test pour vérifier le bon fonctionnement"""
    print(f'Request: {self.request!r}')
