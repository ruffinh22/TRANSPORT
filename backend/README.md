# TKF Backend - Django REST API

API REST pour le système de gestion de transport **TKF** construit avec Django et Django REST Framework.

## 📋 Table des matières

- [Technologies](#technologies)
- [Installation](#installation)
- [Configuration](#configuration)
- [Démarrage](#démarrage)
- [Structure du Projet](#structure-du-projet)
- [API Endpoints](#api-endpoints)
- [Tests](#tests)
- [Déploiement](#déploiement)

## 🛠️ Technologies

- **Python 3.11+**
- **Django 4.2 LTS**
- **Django REST Framework (DRF)**
- **PostgreSQL 14+**
- **Redis 7+**
- **Celery** (Task Queue)
- **Gunicorn** (WSGI Server)
- **Docker & Docker Compose**

## 🚀 Installation

### Prérequis

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optionnel)

### Installation Locale

1. **Cloner le repository**
```bash
cd /home/lidruf/TRANSPORT/backend
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

5. **Effectuer les migrations**
```bash
python manage.py migrate
```

6. **Créer un super utilisateur**
```bash
python manage.py createsuperuser
```

7. **Collecter les fichiers statiques**
```bash
python manage.py collectstatic --noinput
```

## ⚙️ Configuration

### Variables d'environnement (.env)

```bash
# Django
DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database PostgreSQL
DB_NAME=tkf_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800

# Email (SendGrid)
EMAIL_HOST_PASSWORD=your-sendgrid-api-key

# Paiements (Stripe)
STRIPE_PUBLIC_KEY=pk_test_xxxxxxxx
STRIPE_SECRET_KEY=sk_test_xxxxxxxx

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

## 🎯 Démarrage

### Mode Développement Local

```bash
# Démarrer le serveur de développement
python manage.py runserver

# Démarrer Celery Worker (autre terminal)
celery -A config worker --loglevel=info

# Démarrer Celery Beat (autre terminal)
celery -A config beat --loglevel=info
```

L'API sera disponible à : `http://localhost:8000`

### Avec Docker Compose

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f backend

# Arrêter les services
docker-compose down
```

## 📁 Structure du Projet

```
backend/
├── config/                          # Configuration Django
│   ├── settings.py                 # Paramètres principaux
│   ├── urls.py                     # Routes API
│   ├── wsgi.py                     # WSGI Config
│   ├── asgi.py                     # ASGI Config
│   └── celery.py                   # Celery Config
├── apps/                            # Applications Django
│   ├── users/                      # Authentification & Utilisateurs
│   │   ├── models.py              # Modèle User
│   │   ├── serializers.py         # Serializers
│   │   ├── views.py               # ViewSets
│   │   └── urls.py                # Routes
│   ├── cities/                     # Gestion des villes
│   ├── vehicles/                   # Gestion des véhicules
│   ├── employees/                  # Gestion du personnel
│   ├── trips/                      # Gestion des trajets
│   ├── tickets/                    # Vente de billets
│   ├── parcels/                    # Gestion des colis
│   ├── payments/                   # Paiements
│   ├── revenues/                   # Recettes
│   └── common/                     # Services communs
│       ├── models.py              # Modèles abstraits
│       ├── serializers.py         # Serializers génériques
│       ├── permissions.py         # Permissions RBAC
│       └── exceptions.py          # Exceptions custom
├── middleware/                      # Middlewares custom
├── tasks/                           # Tâches Celery
├── static/                          # Assets statiques
├── media/                           # Fichiers uploadés
├── logs/                            # Fichiers log
├── tests/                           # Tests
├── manage.py                        # CLI Django
├── requirements.txt                 # Dépendances
├── .env.example                     # Variables d'environnement exemple
├── Dockerfile                       # Image Docker
└── pytest.ini                       # Configuration pytest
```

## 📡 API Endpoints

### Authentification
- `POST /api/v1/auth/register` - Inscription
- `POST /api/v1/auth/login` - Connexion
- `POST /api/v1/auth/refresh` - Rafraîchir token
- `POST /api/v1/auth/logout` - Déconnexion

### Villes & Itinéraires
- `POST /api/v1/cities/` - Créer ville
- `GET /api/v1/cities/` - Lister villes
- `PUT /api/v1/cities/{id}/` - Modifier ville
- `DELETE /api/v1/cities/{id}/` - Supprimer ville

### Véhicules
- `POST /api/v1/vehicles/` - Enregistrer véhicule
- `GET /api/v1/vehicles/` - Lister véhicules
- `PUT /api/v1/vehicles/{id}/` - Modifier véhicule
- `GET /api/v1/vehicles/{id}/maintenance/` - Suivi entretien

### Personnel
- `POST /api/v1/employees/` - Créer employé
- `GET /api/v1/employees/` - Lister employés
- `PUT /api/v1/employees/{id}/` - Modifier employé

### Trajets
- `POST /api/v1/trips/` - Créer trajet
- `GET /api/v1/trips/` - Lister trajets
- `PUT /api/v1/trips/{id}/` - Mettre à jour trajet

### Billets
- `POST /api/v1/tickets/` - Vendre billet
- `GET /api/v1/tickets/` - Lister billets
- `PUT /api/v1/tickets/{id}/` - Modifier billet

### Colis
- `POST /api/v1/parcels/` - Enregistrer colis
- `GET /api/v1/parcels/` - Lister colis
- `PUT /api/v1/parcels/{id}/` - Modifier colis

### Paiements
- `GET /api/v1/payments/` - Lister paiements
- `POST /api/v1/payments/` - Créer paiement

### Recettes
- `GET /api/v1/revenues/` - Consulter recettes
- `GET /api/v1/revenues/daily/` - Recettes journalières
- `GET /api/v1/revenues/monthly/` - Recettes mensuelles

## 🧪 Tests

### Exécuter tous les tests
```bash
pytest
```

### Avec couverture de code
```bash
pytest --cov=apps --cov-report=html
```

### Tests spécifiques
```bash
pytest tests/test_users.py
pytest tests/test_vehicles.py
```

### Avec verbosité
```bash
pytest -v
```

## 📚 Documentation API

La documentation API (Swagger/OpenAPI) est disponible à :
- **Swagger UI** : `http://localhost:8000/api/v1/docs/`
- **ReDoc** : `http://localhost:8000/api/v1/redoc/`
- **Schema OpenAPI** : `http://localhost:8000/api/v1/schema/`

## 🔐 Sécurité

- ✅ JWT Authentication (Access + Refresh Tokens)
- ✅ CORS configuré
- ✅ Rate Limiting activé
- ✅ Input Validation avec Serializers
- ✅ HTTPS obligatoire en production
- ✅ CSRF Protection
- ✅ Password Hashing (bcrypt)
- ✅ SQL Injection Protection (ORM Django)

## 🚢 Déploiement

### Production avec Docker

```bash
# Build images
docker build -t tkf-backend:latest ./backend

# Push vers registry
docker push myregistry/tkf-backend:latest

# Déployer
docker-compose -f docker-compose.prod.yml up -d
```

### Avec Gunicorn

```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync \
  --max-requests 1000 \
  --timeout 30
```

### Avec Systemd (Linux)

Créer `/etc/systemd/system/tkf-backend.service` :
```ini
[Unit]
Description=TKF Backend Django Service
After=network.target postgres.service redis.service

[Service]
Type=notify
User=django
WorkingDirectory=/home/django/tkf/backend
ExecStart=/home/django/tkf/venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Démarrer le service :
```bash
sudo systemctl daemon-reload
sudo systemctl start tkf-backend
sudo systemctl enable tkf-backend
```

## 📊 Monitoring

### Logs
```bash
# Logs en temps réel
tail -f logs/tkf.log

# Docker logs
docker-compose logs -f backend
```

### Health Check
```bash
curl http://localhost:8000/api/v1/health/
```

### Métriques Celery
```bash
celery -A config events
```

## 🤝 Contribution

1. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
2. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
3. Push vers la branche (`git push origin feature/AmazingFeature`)
4. Ouvrir une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou problème :
- Email: support@tkf.com
- Documentation: https://docs.tkf.com
- Issues: GitHub Issues

---

**Développé avec ❤️ pour TKF**
