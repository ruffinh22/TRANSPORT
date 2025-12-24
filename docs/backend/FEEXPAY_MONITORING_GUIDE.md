# 📊 Guide Monitoring FeexPay et Logs

## Configuration Sentry pour Monitoring

Sentry capture tous les erreurs et les événements critiques en production.

### Installation

```bash
cd /home/lidruf/rhumo_rush/backend
pip install sentry-sdk
```

### Configuration dans Django

Dans `rumo_rush/settings/production.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn="https://your_sentry_dsn@sentry.io/project_id",
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% des traces
    profiles_sample_rate=0.1,  # 10% des profiles
    send_default_pii=False,
    environment="production",
    debug=False,
)
```

### Signaler les Erreurs Manuellement

```python
import sentry_sdk

try:
    # Code risqué
    result = process_payment()
except Exception as e:
    sentry_sdk.capture_exception(e)
    # ou pour les messages simples
    sentry_sdk.capture_message("Payment processing error", level="error")
```

---

## 📋 Logging FeexPay

### Structure des Logs

```
/var/log/rumorush/
├── django.log              # Logs généraux
├── django.json.log         # Format JSON pour ELK
├── django.error.log        # Erreurs uniquement
├── feexpay.log             # Logs spécifiques FeexPay
└── celery.log              # Tâches asynchrones
```

### Configuration Python Logging

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'handlers': {
        'feexpay_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/rumorush/feexpay.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'feexpay_json': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/rumorush/feexpay.json.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'loggers': {
        'apps.payments.feexpay': {
            'handlers': ['feexpay_file', 'feexpay_json', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Utilisation des Logs dans le Code

```python
import logging

logger = logging.getLogger('apps.payments.feexpay')

def process_payment(transaction_id, amount, currency):
    logger.info(
        "Payment initiated",
        extra={
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': currency,
            'timestamp': timezone.now(),
        }
    )
    
    try:
        # Process payment
        result = client.initiate_payment(...)
        
        logger.info(
            "Payment successful",
            extra={'transaction_id': transaction_id, 'result': result}
        )
        return result
        
    except Exception as e:
        logger.error(
            "Payment failed",
            exc_info=True,
            extra={'transaction_id': transaction_id, 'error': str(e)}
        )
        raise
```

---

## 📈 Métriques à Monitorer

### Métriques Critiques

| Métrique | Seuil d'Alerte | Vérifier |
|----------|----------------|---------|
| Taux de succès des paiements | < 90% | `/admin/payments/` |
| Temps de réponse FeexPay API | > 5s | Logs |
| Erreurs webhook | > 5/heure | Sentry |
| Disponibilité API | < 99% | Health check |
| Temps d'attente Celery | > 60s | Celery flower |
| Utilisation Redis | > 80% | `redis-cli INFO` |
| Espace disque logs | > 90% | `df -h` |

### Prometheus + Grafana (Avancé)

```yaml
# docker-compose.yml
version: '3'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Métriques Django

```python
# Ajouter django-prometheus
pip install django-prometheus

# Dans INSTALLED_APPS
INSTALLED_APPS = [
    'django_prometheus',
    ...
]

# Dans urls.py
from django.urls import path
from django_prometheus import urls as prometheus_urls

urlpatterns = [
    ...
    path('prometheus/', include(prometheus_urls)),
]
```

---

## 🔔 Alertes

### Créer des Alertes Sentry

1. Allez dans le dashboard Sentry
2. **Alerts** → **Create Alert Rule**
3. Configurez:
   - **Condition**: `Transaction duration > 5 seconds`
   - **Filter**: `environment:production`
   - **Action**: Email, Slack, etc.

### Alertes par Email

```python
# Envoyer un email en cas d'erreur
from django.core.mail import send_mail
import logging

logger = logging.getLogger('apps.payments')

class EmailHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            send_mail(
                subject=f"FeexPay Error: {record.getMessage()}",
                message=self.format(record),
                from_email="alerts@rumorush.com",
                recipient_list=["admin@rumorush.com"],
            )

logger.addHandler(EmailHandler())
```

### Alertes Slack

```python
# Installer slack SDK
pip install slack-sdk

from slack_sdk import WebClient

client = WebClient(token='xoxb-your-token')

def alert_slack(message, level='warning'):
    emoji = '⚠️' if level == 'warning' else '🔴'
    client.chat_postMessage(
        channel='#alerts',
        text=f"{emoji} FeexPay Alert: {message}"
    )
```

---

## 📊 Dashboard de Suivi FeexPay

### Requêtes SQL Utiles

```sql
-- Nombre de paiements par jour
SELECT DATE(created_at) as date, COUNT(*) as count
FROM feexpay_transactions
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Taux de succès
SELECT 
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM feexpay_transactions
WHERE created_at >= NOW() - INTERVAL 24 HOUR
GROUP BY status;

-- Montants par monnaie
SELECT currency, SUM(amount) as total, COUNT(*) as count
FROM feexpay_transactions
WHERE status = 'completed'
GROUP BY currency;

-- Erreurs récentes
SELECT * FROM feexpay_transactions
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

### Dashboard Django Admin Personnalisé

```python
# Créer une page dashboard dans Django admin
from django.contrib import admin
from django.views.generic import TemplateView
from django.urls import path
from django.utils.html import format_html

class FeexPayDashboardView(TemplateView):
    template_name = 'admin/feexpay_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum, Count
        from datetime import timedelta
        from django.utils import timezone
        
        last_24h = timezone.now() - timedelta(hours=24)
        
        context['total_today'] = FeexPayTransaction.objects.filter(
            created_at__gte=last_24h
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['success_rate'] = (
            FeexPayTransaction.objects.filter(
                created_at__gte=last_24h,
                status='completed'
            ).count() / 
            max(FeexPayTransaction.objects.filter(
                created_at__gte=last_24h
            ).count(), 1) * 100
        )
        
        return context

# Ajouter à l'admin
admin.site.add_view(
    path('feexpay-dashboard/', FeexPayDashboardView.as_view()),
    name='feexpay_dashboard'
)
```

---

## 🎯 Checklist Monitoring

- [ ] Sentry configuré et testé
- [ ] Logs centralisés (ELK, Datadog, etc.)
- [ ] Alertes email configurées
- [ ] Alertes Slack en place
- [ ] Prometheus + Grafana déployés
- [ ] Dashboard FeexPay accessible
- [ ] Métriques remontées dans APM
- [ ] Notifications en cas d'erreur
- [ ] Rapports hebdomadaires générés
- [ ] Logs archivés pour audit

