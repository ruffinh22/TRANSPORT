# 🚀 Commandes de Déploiement TKF Transport

## ✅ Requirements - Status

Le fichier `requirements.txt` est **COMPLET et CORRECT** ✓

Contient:
- ✓ Django 4.2.8 + DRF
- ✓ JWT Authentication (djangorestframework-simplejwt)
- ✓ PostgreSQL support (psycopg2)
- ✓ Redis & Celery pour tasks async
- ✓ Email (django-anymail)
- ✓ File Storage (S3 via django-storages)
- ✓ Stripe & Twilio intégration
- ✓ Sentry pour monitoring
- ✓ Gunicorn pour production
- ✓ Testing tools (pytest, factory-boy)
- ✓ Code quality (black, flake8, isort)

---

## 🔧 Commandes de Déploiement Essentielles

### 1️⃣ **Setup Initial Complet**
```bash
cd backend
make setup
# Exécute: install + migrate + init-roles + seed-users
```

### 2️⃣ **Installation des dépendances**
```bash
make install
# ou manuellement:
pip install -r requirements.txt
```

### 3️⃣ **Migrations de base de données**
```bash
make migrate
# ou:
python manage.py migrate
```

### 4️⃣ **Initialiser les rôles et permissions**
```bash
make init-roles
# Crée: ADMIN, COMPTABLE, GUICHETIER, CHAUFFEUR, CONTROLEUR, GESTIONNAIRE_COURRIER, CLIENT
```

### 5️⃣ **Créer les utilisateurs par défaut**
```bash
make seed-users
# Crée 7 utilisateurs de test avec leurs rôles:
# - admin@transport.bf (ADMIN)
# - comptable@transport.bf (COMPTABLE)
# - guichetier@transport.bf (GUICHETIER)
# - chauffeur@transport.bf (CHAUFFEUR)
# - controleur@transport.bf (CONTROLEUR)
# - gestionnaire@transport.bf (GESTIONNAIRE_COURRIER)
# - client@transport.bf (CLIENT)
```

### 6️⃣ **Créer un super-utilisateur custom**
```bash
make superuser
# ou:
python manage.py createsuperuser
```

### 7️⃣ **Démarrer le serveur de développement**
```bash
make run
# Accessible à:
# - API: http://localhost:8000/api/v1/
# - Admin: http://localhost:8000/admin
# - Docs: http://localhost:8000/api/v1/docs/
```

### 8️⃣ **Production avec Gunicorn**
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
# ou avec systemd (voir deployment guide)
```

---

## 🔄 Commandes de Base de Données

### Réinitialiser la BD (ATTENTION ⚠️ données perdues)
```bash
make reset-db
# Flush + Migrate + Init roles + Seed users
```

### Backup de la BD
```bash
make dumpdata
# Crée: backup_YYYYMMDD_HHMMSS.json
```

### Restaurer une sauvegarde
```bash
make loaddata
# Demande le fichier de backup
```

---

## 🧪 Tests et Qualité du Code

### Exécuter tous les tests
```bash
make test
# ou:
pytest
```

### Tests du module users
```bash
make test-users
# ou:
pytest apps/users/tests/
```

### Coverage report
```bash
make coverage
# ou:
pytest --cov=apps --cov-report=html
```

### Linting
```bash
make lint
# Exécute: black, flake8, isort
```

### Formatage du code
```bash
make format
# black + isort
```

### Type checking
```bash
make mypy
# Vérification des types Python
```

---

## 📝 Configuration Environnement (.env)

Fichier `.env` requis:
```env
DEBUG=False
SECRET_KEY=votre-clé-secrète-très-longue
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com

# Database PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=tkf_db
DB_USER=tkf_user
DB_PASSWORD=votre-mot-de-passe
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
SENDGRID_API_KEY=votre-clé-sendgrid

# AWS S3
AWS_ACCESS_KEY_ID=votre-clé
AWS_SECRET_ACCESS_KEY=votre-secret
AWS_STORAGE_BUCKET_NAME=votre-bucket

# Stripe
STRIPE_PUBLIC_KEY=pk_...
STRIPE_SECRET_KEY=sk_...

# Sentry
SENTRY_DSN=votre-dsn-sentry

# Twilio (SMS)
TWILIO_ACCOUNT_SID=votre-sid
TWILIO_AUTH_TOKEN=votre-token
```

---

## 📋 Checklist Déploiement Production

- [ ] Cloner le repo
- [ ] Créer `.env` en production avec secrets
- [ ] `make setup` pour installer + migrer + créer rôles/users
- [ ] Changer mots de passe des utilisateurs de test
- [ ] Créer un vrai superuser: `make superuser`
- [ ] Configurer PostgreSQL (migration depuis SQLite si nécessaire)
- [ ] Configurer Redis pour cache/tasks
- [ ] Configurer Gunicorn/systemd
- [ ] Configurer Nginx en reverse proxy
- [ ] Configurer SSL/TLS (Let's Encrypt)
- [ ] Configurer Email (SendGrid/AWS SES)
- [ ] Configurer S3 pour fichiers statiques
- [ ] Activer Sentry pour monitoring
- [ ] Tester avec quelques requêtes API
- [ ] Lancer les tests: `make test`
- [ ] Vérifier les logs d'erreur

---

## 🚨 Commandes Utiles Supplémentaires

### Shell Django interactif
```bash
python manage.py shell
```

### Faire une migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Nettoyer les fichiers temporaires
```bash
make clean
```

### Vérifier la configuration Django
```bash
make check
```

### Créer une dump SQL brute
```bash
pg_dump -U tkf_user tkf_db > backup.sql
```

---

## 📚 Documentation Complète

- Frontend: `/QUICK_START_DJANGO.md`
- Backend: `/backend/README.md`
- Architecture: `/ARCHITECTURE.md`
- Déploiement: `/DEPLOYMENT_GUIDE.md`
- Spécifications: `/SPECIFICATIONS_TECHNIQUES.md`

