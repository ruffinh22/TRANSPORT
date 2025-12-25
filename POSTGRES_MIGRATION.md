# 🗄️ Guide de Migration: SQLite → PostgreSQL

## 📊 Vue d'ensemble

Ce guide explique comment migrer la base de données de développement (SQLite) vers PostgreSQL (production).

---

## Phase 1: Préparation

### 1. Vérifier la configuration actuelle

```bash
cd backend

# Vérifier la base SQLite
ls -lh db.sqlite3

# Checker les migrations
python manage.py showmigrations
```

### 2. Installer PostgreSQL localement

```bash
# macOS
brew install postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Démarrer le service
sudo service postgresql start

# Vérifier l'installation
psql --version
```

### 3. Créer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer l'utilisateur
CREATE USER tkf_user WITH PASSWORD 'secure_password_here';

# Créer la base
CREATE DATABASE tkf_db OWNER tkf_user;

# Configurations de performance
ALTER ROLE tkf_user SET client_encoding TO 'utf8';
ALTER ROLE tkf_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tkf_user SET default_transaction_deferrable TO on;
ALTER ROLE tkf_user SET default_transaction_level TO 'read committed';
ALTER ROLE tkf_user SET timezone TO 'UTC';

# Quitter psql
\q
```

---

## Phase 2: Configuration Django

### 1. Installer le driver PostgreSQL

```bash
# Activation de l'environnement Conda
conda activate tkf

# Installer psycopg2
pip install psycopg2-binary==2.9.9
pip install django-environ

# Mettre à jour requirements.txt
pip freeze > requirements.txt
```

### 2. Configurer .env pour PostgreSQL

```env
# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=tkf_db
DB_USER=tkf_user
DB_PASSWORD=secure_password_here
DB_HOST=localhost
DB_PORT=5432
DB_CONN_MAX_AGE=600

# Debug mode
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### 3. Mettre à jour settings.py

```python
# backend/config/settings.py

import os
from pathlib import Path
import environ

# Load environment variables
env = environ.Env()
environ.Env.read_env()

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env('DB_NAME', default=os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': env('DB_USER', default=''),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default=''),
        'PORT': env('DB_PORT', default=''),
        'CONN_MAX_AGE': int(env('DB_CONN_MAX_AGE', default=600)),
        'OPTIONS': {
            'connect_timeout': 10,
        } if env('DB_ENGINE', default='').startswith('postgres') else {},
    }
}

# Connection pooling for production
if env('DB_ENGINE', default='').startswith('postgres'):
    DATABASES['default']['CONN_MAX_AGE'] = 600
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000'  # 30 second timeout
    }
```

---

## Phase 3: Migration des Données

### 1. Export des données de SQLite

```bash
# Exporter les données en JSON
python manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 2 > dump.json

# Taille du fichier
ls -lh dump.json
```

### 2. Passer à PostgreSQL et appliquer les migrations

```bash
# Tester la connexion PostgreSQL
python manage.py dbshell

# Appliquer les migrations
python manage.py migrate --verbosity 2

# Status des migrations
python manage.py showmigrations
```

### 3. Charger les données

```bash
# Charger le dump JSON
python manage.py loaddata dump.json --verbosity 2

# Vérifier le chargement
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.count()
>>> # Devrait afficher le nombre d'utilisateurs
```

### 4. Vérifier l'intégrité des données

```bash
# Checker les inconsistencies
python manage.py check --deploy

# Vérifier les statistiques
python manage.py shell << EOF
from apps.employees.models import Employee
from apps.cities.models import City
from apps.trips.models import Trip

print(f"Employees: {Employee.objects.count()}")
print(f"Cities: {City.objects.count()}")
print(f"Trips: {Trip.objects.count()}")
EOF
```

---

## Phase 4: Optimisation PostgreSQL

### 1. Créer les index manquants

```sql
-- Se connecter à la base
psql -U tkf_user -d tkf_db

-- Index pour recherches fréquentes
CREATE INDEX idx_employee_status ON employees_employee(status);
CREATE INDEX idx_employee_department ON employees_employee(department);
CREATE INDEX idx_city_code ON cities_city(code);
CREATE INDEX idx_trip_departure_time ON trips_trip(departure_time);
CREATE INDEX idx_payment_status ON payments_payment(status);

-- Vérifier les index
\d
```

### 2. Optimiser la configuration

```bash
# Éditer postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Paramètres recommandés:
# shared_buffers = 256MB (pour 4GB RAM)
# effective_cache_size = 1GB
# work_mem = 16MB
# maintenance_work_mem = 64MB
# max_connections = 100

# Redémarrer PostgreSQL
sudo service postgresql restart
```

### 3. Activer l'autovacuum

```sql
-- Vérifier le statut
SELECT autovacuum FROM pg_database WHERE datname = 'tkf_db';

-- Configurer
ALTER DATABASE tkf_db SET autovacuum = on;

-- Réduire le délai
ALTER DATABASE tkf_db SET autovacuum_vacuum_scale_factor = 0.1;
ALTER DATABASE tkf_db SET autovacuum_analyze_scale_factor = 0.05;
```

---

## Phase 5: Tests & Validation

### 1. Tests de performance

```bash
# Mesurer le temps de réponse
time python manage.py test --keepdb

# Checker les requêtes lentes
python manage.py shell << EOF
from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True
reset_queries()

from apps.employees.models import Employee
Employee.objects.select_related('user').count()

for query in connection.queries:
    print(f"Time: {query['time']}")
    print(f"SQL: {query['sql'][:100]}...")
    print("---")
EOF
```

### 2. Tests de capacité

```bash
# Backup test
pg_dump -U tkf_user -d tkf_db > /tmp/tkf_backup_test.sql

# Restore test (into temporary database)
createdb -U tkf_user tkf_db_test
psql -U tkf_user -d tkf_db_test < /tmp/tkf_backup_test.sql

# Verify
psql -U tkf_user -d tkf_db_test -c "SELECT COUNT(*) FROM employees_employee;"

# Cleanup
dropdb -U tkf_user tkf_db_test
```

### 3. Tests de connexion

```bash
# Django test connection
python manage.py dbshell -c "\dt"

# Test with Django ORM
python manage.py test apps.employees apps.cities --verbosity 2
```

---

## Phase 6: Déploiement en Production

### 1. Stratégie de migration (Zero-downtime)

```bash
# 1. Créer la base PostgreSQL en production
# 2. Exporter les données de SQLite
# 3. Importer dans PostgreSQL
# 4. Mettre à jour settings.py
# 5. Redémarrer l'application
# 6. Vérifier les logs
```

### 2. Backup avant migration

```bash
# Backup de la base SQLite
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# Backup de PostgreSQL
pg_dump -U tkf_user -d tkf_db | gzip > tkf_backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 3. Scripts de migration automation

```bash
#!/bin/bash
# scripts/migrate_to_postgres.sh

set -e

echo "🔄 Starting migration to PostgreSQL..."

# 1. Export from SQLite
echo "📤 Exporting data from SQLite..."
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > /tmp/dump.json

# 2. Switch to PostgreSQL
echo "🔌 Switching to PostgreSQL..."
export DB_ENGINE=django.db.backends.postgresql
export DB_NAME=tkf_db
export DB_USER=tkf_user
export DB_HOST=localhost

# 3. Migrate schema
echo "📊 Applying migrations..."
python manage.py migrate --verbosity 2

# 4. Load data
echo "📥 Loading data into PostgreSQL..."
python manage.py loaddata /tmp/dump.json

# 5. Verify
echo "✅ Verifying data integrity..."
python manage.py check --deploy

echo "🎉 Migration complete!"
```

---

## Phase 7: Rollback (si nécessaire)

```bash
# Si la migration échoue, revenir à SQLite:

# 1. Arrêter Django
pkill -f "python manage.py runserver"

# 2. Restaurer .env avec SQLite
export DB_ENGINE=django.db.backends.sqlite3
export DB_NAME=db.sqlite3

# 3. Restaurer la base SQLite
cp db.sqlite3.backup.20241225_120000 db.sqlite3

# 4. Redémarrer Django
python manage.py runserver
```

---

## Checklist de Migration

- [ ] Backup SQLite créé
- [ ] Base PostgreSQL créée
- [ ] Driver psycopg2 installé
- [ ] .env configuré pour PostgreSQL
- [ ] settings.py mis à jour
- [ ] Données exportées en JSON
- [ ] Migrations appliquées
- [ ] Données chargées
- [ ] Intégrité vérifiée
- [ ] Index créés
- [ ] Performance testée
- [ ] Backup PostgreSQL validé
- [ ] Logs nettoyés
- [ ] SQLite archivé

---

## Ressources

- [PostgreSQL Official](https://www.postgresql.org/docs/)
- [Django PostgreSQL](https://docs.djangoproject.com/en/4.2/ref/settings/#databases)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Database Migration Best Practices](https://www.postgresql.org/docs/current/backup.html)

---

**Version**: 2.0.0  
**Dernière mise à jour**: 25 Décembre 2024
