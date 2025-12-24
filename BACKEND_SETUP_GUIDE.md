# 🚀 Guide de Démarrage - Backend Django Professionnel

## Phase 1 : Initialisation (5 minutes)

### 1.1 Configuration de l'environnement

```bash
cd /home/lidruf/TRANSPORT/backend

# Copier le fichier d'exemple
cp .env.example .env

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 1.2 Installer les dépendances

```bash
# Dépendances de production
pip install -r requirements.txt

# Dépendances de développement (optionnel)
pip install -r requirements-dev.txt
```

### 1.3 Initialiser la base de données

```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superuser (admin)
python manage.py createsuperuser

# Initialiser les rôles et permissions système
python manage.py init_roles
```

### 1.4 Tester localement

```bash
# Lancer le serveur de développement
python manage.py runserver

# Accès
# API: http://localhost:8000/api/v1/
# Admin: http://localhost:8000/admin
# Docs: http://localhost:8000/api/v1/docs/
```

---

## Phase 2 : Authentification et Users (10 minutes)

### 2.1 Créer un utilisateur

```bash
# Via Django shell
python manage.py shell

>>> from apps.users.models import User
>>> user = User.objects.create_user(
...     email='john@example.com',
...     phone='+237670000000',
...     first_name='John',
...     last_name='Doe',
...     password='SecurePassword123'
... )
>>> print(user.get_full_name())
John Doe
```

### 2.2 Tester l'API d'authentification

#### Inscription
```bash
curl -X POST http://localhost:8000/api/v1/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "phone": "+237670000000",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePassword123",
    "password2": "SecurePassword123"
  }'
```

#### Connexion
```bash
curl -X POST http://localhost:8000/api/v1/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": { ... }
}
```

#### Utiliser le token pour les requêtes protégées
```bash
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 2.3 Vérifier les permissions

```bash
# Donner un rôle à un utilisateur (via Admin ou Django shell)
python manage.py shell

>>> from apps.users.models import User
>>> from apps.common.models import Role
>>> user = User.objects.get(email='user@example.com')
>>> admin_role = Role.objects.get(code='ADMIN')
>>> user.roles.add(admin_role)
>>> user.has_role('ADMIN')
True
```

---

## Phase 3 : Tests (5 minutes)

### 3.1 Exécuter les tests unitaires

```bash
# Tous les tests users
pytest apps/users/tests.py -v

# Tests spécifiques
pytest apps/users/tests.py::TestUserModel::test_create_user -v

# Avec coverage
pytest apps/users/tests.py --cov=apps.users --cov-report=html
```

### 3.2 Résultats attendus

```
test_create_user PASSED
test_create_superuser PASSED
test_user_email_unique PASSED
test_verify_email PASSED
test_verify_phone PASSED
test_block_user PASSED
test_unblock_user PASSED
test_lock_login PASSED
test_is_fully_verified PASSED

===== 9 passed in 0.45s =====
```

---

## Phase 4 : Avec Docker (3 minutes)

### 4.1 Lancer le stack complet

```bash
# Aller à la racine du projet
cd /home/lidruf/TRANSPORT

# Lancer tous les services
docker-compose up -d

# Vérifier le statut
docker-compose ps
```

### 4.2 Initialiser la base de données avec Docker

```bash
# Accéder au conteneur Django
docker-compose exec backend bash

# À l'intérieur du conteneur
python manage.py migrate
python manage.py init_roles
python manage.py createsuperuser
```

### 4.3 Accès aux services

```
Frontend:     http://localhost:3000
Backend API:  http://localhost:8000/api/v1/
Admin:        http://localhost:8000/admin
Docs:         http://localhost:8000/api/v1/docs/
PostgreSQL:   localhost:5432
Redis:        localhost:6379
```

---

## Phase 5 : Structure du Projet

```
backend/
├── config/                      # Configuration Django
│   ├── settings.py             # Settings (JWT, DB, Cache, Celery)
│   ├── urls.py                 # URL routing
│   ├── celery.py               # Configuration Celery
│   ├── wsgi.py                 # WSGI server
│   └── asgi.py                 # ASGI server
│
├── apps/
│   ├── common/                 # Modèles communs
│   │   ├── models.py          # BaseModel, Role, Permission, Audit
│   │   ├── admin.py           # Admin panels
│   │   ├── signals.py         # Django signals
│   │   └── management/        # Management commands
│   │
│   ├── users/                  # Users & Authentication ✨ COMPLET
│   │   ├── models.py          # User, UserSession
│   │   ├── serializers.py      # Serializers pour API
│   │   ├── views.py           # ViewSets & Views
│   │   ├── permissions.py      # Permissions personnalisées
│   │   ├── urls.py            # URL routing
│   │   ├── admin.py           # Admin panels
│   │   ├── tests.py           # Tests unitaires
│   │   └── README.md          # Documentation module
│   │
│   ├── cities/                 # À créer
│   ├── vehicles/               # À créer
│   ├── employees/              # À créer
│   ├── trips/                  # À créer
│   ├── tickets/                # À créer
│   ├── parcels/                # À créer
│   ├── payments/               # À créer
│   └── revenues/               # À créer
│
├── tasks/                       # Celery tasks
├── manage.py                    # Django CLI
├── requirements.txt             # Dépendances prod
├── requirements-dev.txt         # Dépendances dev
├── pytest.ini                   # Configuration pytest
├── .env.example                 # Variables d'exemple
└── Dockerfile                   # Conteneurisation
```

---

## 🔐 Rôles Système Créés

Après `python manage.py init_roles`, les rôles suivants sont disponibles :

```
SUPER_ADMIN   → Accès complet
ADMIN         → Gestion administrative
MANAGER       → Gestion opérationnelle
DRIVER        → Chauffeur
EMPLOYEE      → Employé
CUSTOMER      → Client
```

---

## 📊 Dashboard Admin

1. Accédez à `http://localhost:8000/admin`
2. Connectez-vous avec votre superuser
3. Managez :
   - **Users** : Créer, éditer, bloquer, vérifier documents
   - **Roles** : Créer des rôles personnalisés
   - **Permissions** : Gérer les permissions granulaires
   - **Audit Trail** : Voir l'historique complet
   - **System Logs** : Déboguer les problèmes
   - **Notifications** : Envoyer des notifications
   - **Files** : Gérer les uploads

---

## 🧪 Commandes Utiles

```bash
# Développement
python manage.py runserver
python manage.py shell

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py migrate --fake

# Tests
pytest                                    # Tous les tests
pytest apps/users/ -v                    # Tests users verbeux
pytest --cov=apps --cov-report=html     # Coverage

# Nettoyage
python manage.py flush                    # Réinitialiser DB
python manage.py dumpdata > backup.json   # Backup DB
python manage.py loaddata backup.json     # Restore DB

# Admin
python manage.py createsuperuser          # Créer un admin
python manage.py changepassword username  # Changer mot de passe

# Celery
celery -A config worker -l info
celery -A config beat -l info
```

---

## 🐛 Troubleshooting

### Port déjà utilisé
```bash
# Changer le port
python manage.py runserver 8001

# Ou tuer le processus
lsof -i :8000
kill -9 <PID>
```

### Migrations non appliquées
```bash
python manage.py showmigrations
python manage.py migrate --run-syncdb
```

### Cache Redis pas accessible
```bash
# Vérifier Redis
redis-cli ping  # Doit retourner PONG

# Ou avec Docker
docker-compose exec redis redis-cli ping
```

### Erreur JWT Token
```bash
# Régénérer les tokens (se reconnecter)
# Les tokens expirent après 1 heure par défaut
# Utiliser le refresh token pour renouveler
```

---

## ✅ Prochaines Étapes

1. ✅ **Backend Users** - COMPLÉTÉ
2. ⏭️ **Créer les modèles Transport** (Cities, Vehicles, Trips)
3. ⏭️ **Créer les modèles Métier** (Tickets, Parcels, Payments)
4. ⏭️ **Intégration Frontend** (React + Redux)
5. ⏭️ **Tests & Coverage**
6. ⏭️ **Déploiement Production**

---

**Date** : Décembre 2024  
**Version** : 1.0 - Backend Professionnel  
**Status** : ✅ Ready for Development
