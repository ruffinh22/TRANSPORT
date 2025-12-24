# 🚀 Guide Déploiement FeexPay en Production

## Pré-requis


- ✅ Compte FeexPay actif avec clés API réelles
- ✅ Domaine configuré (ex: www.rumorush.com)
- ✅ Certificat SSL/TLS (HTTPS obligatoire)
- ✅ Base de données PostgreSQL en production
- ✅ Redis configuré pour le cache et Celery
- ✅ Logs centralisés (Sentry, ELK, etc.)


---


## 1️⃣ Configuration des Secrets en Production

### Variables d'EnvironnementFRONTEND-copy.

Créez un fichier `.env.production` **sécurisé** (ne jamais commiter):

```dotenv
# FeexPay - Secrets de production
FEEXPAY_API_KEY=fp_live_your_real_api_key_here
FEEXPAY_SHOP_ID=67d68239474b2509dcde6d10
FEEXPAY_WEBHOOK_SECRET=rhXMItO8

# Django
DEBUG=False
SECRET_KEY=your_long_random_secret_key_here
ALLOWED_HOSTS=www.rumorush.com,rumorush.com,api.rumorush.com

# Base de données
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rumo_rush_prod
DB_USER=rumo_rush_user
DB_PASSWORD=secure_password_here
DB_HOST=prod-db-server.example.com
DB_PORT=5432

# Redis
REDIS_URL=redis://prod-redis-server.example.com:6379/0
CELERY_BROKER_URL=redis://prod-redis-server.example.com:6379/1

# Email
EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
SENDGRID_API_KEY=sg_live_your_sendgrid_key

# URLs
FRONTEND_URL=https://www.rumorush.com
BACKEND_URL=https://api.rumorush.com

# Monitoring
SENTRY_DSN=https://your_sentry_dsn_here
```

### Stockage Sécurisé des Secrets

**Option 1: Variables d'environnement système**
```bash
# Sur le serveur
export FEEXPAY_API_KEY="fp_live_..."
export FEEXPAY_WEBHOOK_SECRET="..."
```

**Option 2: Secrets Manager (AWS Secrets Manager, HashiCorp Vault)**
```python
# Dans settings/production.py
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='rumo_rush/feexpay')
FEEXPAY_API_KEY = secret['SecretString']
```

**Option 3: .env.production chiffré**
```bash
# Créer le fichier
openssl enc -aes-256-cbc -in .env.production -out .env.production.enc -k "your_password"

# Décrypter au démarrage
openssl enc -d -aes-256-cbc -in .env.production.enc -k "your_password" > .env.production
source .env.production
python manage.py runserver
```

---

## 2️⃣ Configuration Django pour Production

Modifiez `rumo_rush/settings/production.py`:

```python
from .base import *
import os

# === SÉCURITÉ ===
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# === ALLOWED HOSTS ===
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'www.rumorush.com',
    'rumorush.com',
    'api.rumorush.com',
])

# === DATABASE ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
}

# === CACHE ===
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': False,  # Alerter sur erreurs Redis
        }
    }
}

# === CELERY ===
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_TASK_ALWAYS_EAGER = False  # Mode async en production

# === SENTRY (Monitoring) ===
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN', default=''),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # 10% des traces
    send_default_pii=False,
    environment='production'
)

# === LOGGING ===
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/rumo_rush/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'sentry'],
    },
    'loggers': {
        'apps.payments': {
            'level': 'INFO',
            'handlers': ['file', 'sentry'],
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'WARNING',
            'handlers': ['file'],
        },
    },
}

# === STATIC FILES (CloudFront/S3) ===
STATIC_URL = 'https://cdn.rumorush.com/static/'
STATIC_ROOT = '/var/www/rumorush/staticfiles'

# Si utilisant AWS S3
# STATIC_URL = 'https://s3.amazonaws.com/rumorush-static/'
# STORAGES = {
#     'default': {
#         'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
#         'OPTIONS': {...}
#     }
# }
```

---

## 3️⃣ Migration de la Base de Données

```bash
# Sur le serveur de production
cd /home/lidruf/rhumo_rush/backend

# Appliquer les migrations
python manage.py migrate --noinput

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Vérifier la configuration
python manage.py check --deploy
```

---

## 4️⃣ Configuration Nginx

```nginx
# /etc/nginx/sites-available/rumorush

upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name www.rumorush.com rumorush.com api.rumorush.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.rumorush.com rumorush.com api.rumorush.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/rumorush.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rumorush.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Logs
    access_log /var/log/nginx/rumorush_access.log;
    error_log /var/log/nginx/rumorush_error.log;

    # Media files
    location /media/ {
        alias /var/www/rumorush/media/;
    }

    # Static files
    location /static/ {
        alias /var/www/rumorush/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## 5️⃣ Systemd Service

```ini
# /etc/systemd/system/rumorush-django.service

[Unit]
Description=RUMO RUSH Django Application
After=network.target redis.service postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data

WorkingDirectory=/home/lidruf/rhumo_rush/backend

# Environment
EnvironmentFile=/home/lidruf/rhumo_rush/backend/.env.production
Environment="PATH=/home/lidruf/anaconda3/envs/envrl/bin"
Environment="PYTHONUNBUFFERED=1"

# Start
ExecStart=/home/lidruf/anaconda3/envs/envrl/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/rumorush/gunicorn_access.log \
    --error-logfile /var/log/rumorush/gunicorn_error.log \
    rumo_rush.wsgi:application

# Restart policy
Restart=always
RestartSec=10

# Security
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Démarrer le service:
```bash
sudo systemctl daemon-reload
sudo systemctl start rumorush-django
sudo systemctl enable rumorush-django
```

---

## 6️⃣ Configuration Celery (Tâches Asynchrones)

```ini
# /etc/systemd/system/rumorush-celery.service

[Unit]
Description=RUMO RUSH Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data

WorkingDirectory=/home/lidruf/rhumo_rush/backend
EnvironmentFile=/home/lidruf/rhumo_rush/backend/.env.production
Environment="PATH=/home/lidruf/anaconda3/envs/envrl/bin"

ExecStart=/home/lidruf/anaconda3/envs/envrl/bin/celery -A rumo_rush worker \
    --loglevel=info \
    --logfile=/var/log/rumorush/celery.log \
    --pidfile=/var/run/celery.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 7️⃣ Déploiement avec CI/CD (GitHub Actions)

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Deploy to server
      env:
        SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
        SERVER_HOST: ${{ secrets.SERVER_HOST }}
        SERVER_USER: ${{ secrets.SERVER_USER }}
      run: |
        mkdir -p ~/.ssh
        echo "$SSH_PRIVATE_KEY" > ~/.ssh/deploy_key
        chmod 600 ~/.ssh/deploy_key
        ssh -i ~/.ssh/deploy_key $SERVER_USER@$SERVER_HOST << 'EOF'
          cd /home/lidruf/rhumo_rush/backend
          git pull origin main
          python manage.py migrate --noinput
          python manage.py collectstatic --noinput
          sudo systemctl restart rumorush-django rumorush-celery
        EOF
```

---

## ✅ Checklist Déploiement Production

- [ ] Secrets `.env.production` configurés
- [ ] Database PostgreSQL créée et migrée
- [ ] Redis configuré et testé
- [ ] Django check `--deploy` sans erreurs
- [ ] Nginx configuré avec SSL/TLS
- [ ] Gunicorn service systemd créé
- [ ] Celery worker configuré
- [ ] Logs centralisés (Sentry, ELK)
- [ ] Monitoring CPU/Mémoire/Disk configuré
- [ ] Backups base de données programmés
- [ ] Certificate SSL auto-renew (Let's Encrypt)
- [ ] URL webhook FeexPay mise à jour en production
- [ ] HTTPS obligatoire
- [ ] Rate limiting configuré
- [ ] CDN configuré pour les assets statiques

---

## 🔍 Vérification Post-Déploiement

```bash
# Vérifier le service Django
sudo systemctl status rumorush-django

# Vérifier les logs
sudo tail -f /var/log/rumorush/django.log

# Tester l'API
curl https://api.rumorush.com/health/

# Vérifier les migrations
python manage.py migrate --check

# Tester FeexPay
python manage.py shell
>>> from apps.payments.feexpay_client import FeexPayClient
>>> client = FeexPayClient()
>>> providers = client.get_supported_providers()
>>> print(f"✅ FeexPay OK - {len(providers)} providers")
```

