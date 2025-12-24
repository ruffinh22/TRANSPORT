# 🚀 RUMO RUSH Backend - Deployment Guide

**Version**: 1.0.0  
**Last Updated**: 15 November 2025

---

## 📋 Table des Matières

1. [Pre-requisites](#-pre-requisites)
2. [Environment Setup](#-environment-setup)
3. [Database Migration](#-database-migration)
4. [Docker Deployment](#-docker-deployment)
5. [Production Setup](#-production-setup)
6. [Monitoring & Logging](#-monitoring--logging)
7. [SSL/TLS Configuration](#-ssltls-configuration)
8. [Troubleshooting](#-troubleshooting)

---

## ✅ Pre-requisites

### Server Requirements

```
- Ubuntu 20.04 LTS ou CentOS 8+
- CPU: Minimum 2 cores (recommandé 4+)
- RAM: Minimum 2GB (recommandé 4GB+)
- Disk: Minimum 20GB (SSD recommandé)
- Internet: Connection stable pour webhooks
```

### Software Requirements

```bash
# Python et dépendances système
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  python3.10 \
  python3.10-venv \
  postgresql \
  postgresql-contrib \
  redis-server \
  nginx \
  certbot \
  python3-certbot-nginx \
  git \
  curl \
  wget

# Node.js (optionnel, pour frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 🔧 Environment Setup

### 1. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/ruffinh22/rhumo_rush.git
sudo chown -R $USER:$USER rhumo_rush
cd rhumo_rush/backend
```

### 2. Python Virtual Environment

```bash
# Créer venv
python3.10 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Environment Variables

```bash
# Copier le template
cp .env.example .env

# Éditer .env
nano .env
```

**Configuration minimale pour production** :

```env
# Django
SECRET_KEY=your-secret-key-generate-with-secrets.token_urlsafe()
DEBUG=False
ALLOWED_HOSTS=api.rumorush.com,www.rumorush.com,rumorush.com

# Database PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rumo_rush
DB_USER=rumo_rush_user
DB_PASSWORD=strong_password_here
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Email (SendGrid ou Postmark)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-sendgrid-api-key

# Verimail Email Verification
VERIMAIL_API_KEY=your-verimail-api-key

# Payments - Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Sentry (Error Tracking)
SENTRY_DSN=https://...@sentry.io/...

# Admin URL (change for security)
ADMIN_URL=admin/secret-path/
```

### 4. PostgreSQL Setup

```bash
# Créer utilisateur PostgreSQL
sudo -u postgres psql <<EOF
CREATE USER rumo_rush_user WITH PASSWORD 'strong_password_here';
ALTER ROLE rumo_rush_user SET client_encoding TO 'utf8';
ALTER ROLE rumo_rush_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE rumo_rush_user SET default_transaction_deferrable TO on;
ALTER ROLE rumo_rush_user SET timezone TO 'UTC';
CREATE DATABASE rumo_rush OWNER rumo_rush_user;
GRANT ALL PRIVILEGES ON DATABASE rumo_rush TO rumo_rush_user;
EOF

# Tester connexion
psql -U rumo_rush_user -d rumo_rush -h localhost
```

### 5. Redis Setup

```bash
# Installer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérifier Redis
redis-cli ping
# Réponse: PONG
```

---

## 📦 Database Migration

```bash
# Activer venv
source venv/bin/activate

# Créer migrations (si nécessaire)
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Créer superuser
python manage.py createsuperuser

# Charger les données initiales
python manage.py loaddata fixtures/initial_data.json

# Collecter fichiers statiques
python manage.py collectstatic --noinput

# Vérifier configuration
python manage.py check --deploy
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier application
COPY . .

# Exposer port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "rumo_rush.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    container_name: rumo_rush_db
    environment:
      POSTGRES_DB: rumo_rush
      POSTGRES_USER: rumo_rush_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - rumo_rush_network

  redis:
    image: redis:7-alpine
    container_name: rumo_rush_redis
    ports:
      - "6379:6379"
    networks:
      - rumo_rush_network

  backend:
    build: .
    container_name: rumo_rush_backend
    command: >
      sh -c "
      python manage.py migrate &&
      gunicorn rumo_rush.wsgi:application --bind 0.0.0.0:8000 --workers 4
      "
    environment:
      - DEBUG=False
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    networks:
      - rumo_rush_network

  celery_worker:
    build: .
    container_name: rumo_rush_celery_worker
    command: celery -A rumo_rush worker -l info
    environment:
      - DEBUG=False
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    networks:
      - rumo_rush_network

  celery_beat:
    build: .
    container_name: rumo_rush_celery_beat
    command: celery -A rumo_rush beat -l info
    environment:
      - DEBUG=False
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    networks:
      - rumo_rush_network

  nginx:
    image: nginx:latest
    container_name: rumo_rush_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - backend
    networks:
      - rumo_rush_network

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  rumo_rush_network:
    driver: bridge
```

### Deploy with Docker

```bash
# Build et start
docker-compose up -d

# Vérifier logs
docker-compose logs -f backend

# Migrations
docker-compose exec backend python manage.py migrate

# Créer superuser
docker-compose exec backend python manage.py createsuperuser

# Arrêter
docker-compose down
```

---

## 🏭 Production Setup

### 1. Gunicorn Configuration

```bash
# /etc/systemd/system/rumo-rush.service
[Unit]
Description=RUMO RUSH Gunicorn Application
After=network.target

[Service]
User=rumo_rush
Group=www-data
WorkingDirectory=/opt/rhumo_rush/backend
Environment="PATH=/opt/rhumo_rush/backend/venv/bin"
ExecStart=/opt/rhumo_rush/backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind unix:/run/gunicorn.sock \
    --access-logfile - \
    --error-logfile - \
    rumo_rush.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/rumo-rush
upstream rumo_rush {
    server unix:/run/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name api.rumorush.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.rumorush.com;

    ssl_certificate /etc/letsencrypt/live/api.rumorush.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.rumorush.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 10M;

    location / {
        proxy_pass http://rumo_rush;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /opt/rhumo_rush/backend/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /opt/rhumo_rush/backend/media/;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://rumo_rush;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 3. Celery Configuration

```bash
# /etc/systemd/system/rumo-rush-celery-worker.service
[Unit]
Description=RUMO RUSH Celery Worker
After=network.target

[Service]
Type=forking
User=rumo_rush
Group=www-data
WorkingDirectory=/opt/rhumo_rush/backend
Environment="PATH=/opt/rhumo_rush/backend/venv/bin"
ExecStart=/opt/rhumo_rush/backend/venv/bin/celery -A rumo_rush worker -l info

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/rumo-rush-celery-beat.service
[Unit]
Description=RUMO RUSH Celery Beat
After=network.target

[Service]
Type=simple
User=rumo_rush
Group=www-data
WorkingDirectory=/opt/rhumo_rush/backend
Environment="PATH=/opt/rhumo_rush/backend/venv/bin"
ExecStart=/opt/rhumo_rush/backend/venv/bin/celery -A rumo_rush beat -l info

[Install]
WantedBy=multi-user.target
```

### 4. Start Services

```bash
# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable rumo-rush.service
sudo systemctl start rumo-rush.service
sudo systemctl enable rumo-rush-celery-worker.service
sudo systemctl start rumo-rush-celery-worker.service
sudo systemctl enable rumo-rush-celery-beat.service
sudo systemctl start rumo-rush-celery-beat.service

# Vérifier statut
sudo systemctl status rumo-rush.service
```

---

## 📊 Monitoring & Logging

### Sentry Setup

```python
# Dans settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True,
)
```

### Health Check

```bash
# Endpoint santé
curl https://api.rumorush.com/health/

# Response
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "celery": "ok"
  }
}
```

### Logs

```bash
# Logs Gunicorn
sudo journalctl -u rumo-rush.service -f

# Logs Celery
sudo journalctl -u rumo-rush-celery-worker.service -f

# Application logs
tail -f /opt/rhumo_rush/backend/logs/django.log
```

---

## 🔒 SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Installer Certbot
sudo apt install -y certbot python3-certbot-nginx

# Générer certificat
sudo certbot certonly --standalone -d api.rumorush.com -d rumorush.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Vérifier
sudo systemctl status certbot.timer
```

### Auto-renewal with Cron

```bash
# Ajouter à crontab
sudo crontab -e

# Ajouter:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Tester connexion
psql -U rumo_rush_user -d rumo_rush -h localhost

# Vérifier permissions
sudo -u postgres psql -c "\l"
```

### Celery Tasks Not Running

```bash
# Vérifier worker
celery -A rumo_rush worker --pool=solo -l debug

# Vérifier Redis
redis-cli
> ping
PONG
```

### Static Files Not Loading

```bash
# Recollect static files
python manage.py collectstatic --noinput

# Vérifier permissions
sudo chown -R www-data:www-data /opt/rhumo_rush/backend/staticfiles
```

### Memory Issues

```bash
# Vérifier usage
free -h

# Optimiser Gunicorn workers
# Formule: (2 × CPU cores) + 1
# Pour 4 cores: 9 workers
```

---

## 📋 Pre-Production Checklist

```
☑ DEBUG=False
☑ SECRET_KEY changé
☑ ALLOWED_HOSTS configuré
☑ Database migrations appliquées
☑ Static files collectés
☑ SSL/TLS configuré
☑ Email backend configuré
☑ Sentry DSN ajouté
☑ Redis connecté
☑ Celery worker running
☑ Celery beat running
☑ Backups configurés
☑ Monitoring actif
☑ Health check OK
☑ API responding
```

---

## 🆘 Support

- **Documentation** : https://docs.rumorush.com
- **Issues** : https://github.com/ruffinh22/rhumo_rush/issues
- **Email** : ops@rumorush.com

---

**Last Updated**: 15 November 2025  
**Maintainer**: RUMO RUSH DevOps Team
