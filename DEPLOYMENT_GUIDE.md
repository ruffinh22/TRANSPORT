# 🚀 Guide de Déploiement - Portail TKF

## 📋 Table des Matières
1. [Prérequis](#prérequis)
2. [Déploiement Local](#déploiement-local)
3. [Déploiement Docker](#déploiement-docker)
4. [Déploiement Azure](#déploiement-azure)
5. [Configuration Production](#configuration-production)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prérequis

### Système
- **OS**: Linux (Ubuntu 20.04+) ou macOS
- **CPU**: 2+ cores
- **RAM**: 4GB minimum (8GB recommandé)
- **Disque**: 20GB SSD

### Outils
- Git
- Docker & Docker Compose (pour containerization)
- Python 3.12+
- Node.js 18+
- Conda (optionnel)

### Accès
- Compte GitHub avec rights de push
- Compte Azure (pour déploiement cloud)
- Variables d'environnement configurées

---

## Déploiement Local

### 1. Cloner le Repository

```bash
git clone https://github.com/ruffinh22/TRANSPORT.git
cd TRANSPORT
```

### 2. Configurer l'Environnement

```bash
# Copier le fichier .env
cp .env.example .env

# Éditer .env avec vos paramètres
nano .env  # ou vi .env
```

**Variables essentielles:**
```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=tkf_db
DB_USER=postgres
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Frontend
REACT_APP_API_URL=http://localhost:8000/api/v1

# Email (optionnel)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Backend Setup

```bash
cd backend

# Créer l'environnement Conda
conda create -n tkf python=3.12
conda activate tkf

# Installer les dépendances
pip install -r requirements.txt

# Migrations
python manage.py migrate

# Créer superuser
python manage.py createsuperuser

# Seed les données
python manage.py seed_cities

# Démarrer le serveur
python manage.py runserver 0.0.0.0:8000
```

### 4. Frontend Setup

```bash
cd frontend

# Installer les dépendances
npm install

# Démarrer le dev server
npm run dev  # http://localhost:5173
```

### 5. Accès Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/v1
- **Admin Django**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/v1/docs

---

## Déploiement Docker

### 1. Builder les Images

```bash
docker-compose build
```

### 2. Démarrer les Services

```bash
# Démarrage complet
docker-compose up -d

# Vérifier le statut
docker-compose ps

# Logs en temps réel
docker-compose logs -f
```

### 3. Initialiser la Base de Données

```bash
# Dans le conteneur backend
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py seed_cities
```

### 4. Accès Services

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |
| pgAdmin | http://localhost:5050 |

### 5. Arrêter les Services

```bash
# Stop sans supprimer les données
docker-compose down

# Stop et supprime tout
docker-compose down -v
```

---

## Déploiement Azure

### 1. Préparation

```bash
# Installer Azure CLI
# https://learn.microsoft.com/cli/azure/install-azure-cli

# Se connecter à Azure
az login

# Créer un groupe de ressources
az group create --name tkf-rg --location eastus
```

### 2. Configuration Deployment

```bash
# Initialiser Azure Dev CLI
azd init

# Configurer les variables
azd env set SUBSCRIPTION_ID your-subscription-id
azd env set RESOURCE_GROUP tkf-rg
```

### 3. Provisionner les Ressources

```bash
# Provisionner l'infrastructure (Bicep/Terraform)
azd provision

# Déployer l'application
azd deploy
```

### 4. Configuration DNS

```bash
# Récupérer l'IP de la resource
az container show \
  --resource-group tkf-rg \
  --name tkf-app \
  --query ipAddress.ip
```

---

## Configuration Production

### 1. Sécurité

```python
# settings.py

# HTTPS obligatoire
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers de sécurité
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS sécurisé
CORS_ALLOWED_ORIGINS = [
    "https://tkf.bf",
    "https://www.tkf.bf",
]

# Rate limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### 2. Base de Données Production

```bash
# Backup automatique
pg_dump -h host -U user -d tkf_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip < backup_20241225.sql.gz | psql -h host -U user -d tkf_db
```

### 3. Logging & Monitoring

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/tkf/app.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 4. Performance Optimization

```python
# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Database optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

---

## Monitoring & Maintenance

### 1. Health Checks

```bash
# Backend health
curl http://localhost:8000/api/v1/health/

# Database
pg_isready -h localhost -U postgres

# Redis
redis-cli ping
```

### 2. Logs

```bash
# Django logs
tail -f /var/log/tkf/app.log

# Nginx logs (si utilisé)
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### 3. Maintenance Tasks

```bash
# Mise à jour dépendances
pip install -r requirements.txt --upgrade

# Migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Clear cache
python manage.py clear_cache
```

### 4. Backup Strategy

```bash
# Daily backups
0 2 * * * /home/ubuntu/backups/backup.sh

# Weekly exports
0 3 * * 0 /home/ubuntu/backups/export.sh

# Monthly archives
0 4 1 * * /home/ubuntu/backups/archive.sh
```

---

## Troubleshooting

### Backend Issues

```bash
# Check logs
docker-compose logs backend

# Database connection
docker-compose exec backend python manage.py dbshell

# Django shell
docker-compose exec backend python manage.py shell
```

### Frontend Issues

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build

# Check port
lsof -i :5173
```

### Docker Issues

```bash
# Restart services
docker-compose restart

# Remove and recreate
docker-compose down
docker-compose up --build -d

# Check resources
docker stats
```

---

## Support & Contacts

**Équipe Technique**: tech@tkf.bf  
**Hotline**: +226 25 30 00 00  
**Documentation**: https://github.com/ruffinh22/TRANSPORT/wiki  

---

**Version**: 2.0.0  
**Dernière mise à jour**: 25 Décembre 2024  
**Status**: ✅ Production Ready
