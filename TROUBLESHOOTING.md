# 🔧 Guide de Troubleshooting & Maintenance - TKF

## 📋 Table des Matières

1. [Problèmes Courants](#problèmes-courants)
2. [Performance & Optimization](#performance--optimization)
3. [Backup & Disaster Recovery](#backup--disaster-recovery)
4. [Maintenance Régulière](#maintenance-régulière)
5. [Logs & Diagnostics](#logs--diagnostics)
6. [Commandes Utiles](#commandes-utiles)

---

## Problèmes Courants

### ❌ Le serveur Django ne démarre pas

```bash
# Vérifier les migrations
python manage.py showmigrations

# Appliquer les migrations
python manage.py migrate --verbosity 3

# Vérifier les erreurs
python manage.py check

# Voir les logs détaillés
python manage.py runserver --debug --verbosity 3
```

### ❌ Erreur de connexion à la base de données

```bash
# Vérifier la configuration .env
cat .env | grep DB_

# Tester la connexion
python manage.py dbshell
\dt  # Liste les tables

# Si PostgreSQL:
pg_isready -h localhost -U postgres

# Vérifier les credentials
psql -h localhost -U tkf_user -d tkf_db
```

### ❌ Frontend ne charge pas (CORS error)

```bash
# Vérifier les CORS settings dans settings.py
grep -A 5 "CORS_ALLOWED_ORIGINS" backend/config/settings.py

# Ajouter l'origin manquant:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://tkf.bf",
]

# Redémarrer Django
python manage.py runserver
```

### ❌ API retourne 404

```bash
# Vérifier les URLs
cat backend/config/urls.py

# Tester l'endpoint
curl -v http://localhost:8000/api/v1/employees/

# Si 404, vérifier que l'app est incluse dans INSTALLED_APPS
grep "INSTALLED_APPS" backend/config/settings.py
```

### ❌ Erreur d'authentification (401 Unauthorized)

```bash
# Vérifier le token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Token inclus dans les requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/employees/

# Vérifier l'expiration du token
python manage.py shell << EOF
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

user = User.objects.get(username='admin')
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")
EOF
```

### ❌ Erreur: "Permission Denied"

```bash
# Vérifier les permissions de l'utilisateur
python manage.py shell << EOF
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

user = User.objects.get(username='admin')
print(f"Permissions: {user.get_all_permissions()}")
print(f"Groups: {user.groups.all()}")
EOF

# Ajouter des permissions
python manage.py shell << EOF
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from apps.employees.models import Employee

user = User.objects.get(username='admin')
content_type = ContentType.objects.get_for_model(Employee)
permission = Permission.objects.get(codename='add_employee', content_type=content_type)
user.user_permissions.add(permission)
EOF
```

### ❌ Port déjà utilisé

```bash
# Trouver le process utilisant le port
lsof -i :8000
lsof -i :5173
lsof -i :5432

# Tuer le process
kill -9 PID

# Ou utiliser un autre port
python manage.py runserver 0.0.0.0:8001
npm run dev -- --port 5174
```

### ❌ Migration échouée

```bash
# Voir l'état des migrations
python manage.py showmigrations

# Revenir en arrière
python manage.py migrate apps.employees 0001

# Supprimer les migrations échouées
python manage.py makemigrations --dry-run --verbosity 3

# Créer une nouvelle migration
python manage.py makemigrations apps.employees --name fix_issue
python manage.py migrate
```

### ❌ Erreur: "static files not found"

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput --verbosity 2

# Vérifier les paramètres
grep -E "STATIC_ROOT|STATIC_URL" backend/config/settings.py

# Nettoyer les vieux fichiers
python manage.py collectstatic --clear
```

---

## Performance & Optimization

### ⚡ Optimiser les requêtes

```python
# ❌ Mauvais: N+1 queries
employees = Employee.objects.all()
for emp in employees:
    print(emp.user.username)  # Requête supplémentaire par emploi

# ✅ Bon: select_related
employees = Employee.objects.select_related('user').all()
for emp in employees:
    print(emp.user.username)  # Pas de requête supplémentaire

# ✅ Bon: prefetch_related (pour les relations many-to-many)
employees = Employee.objects.prefetch_related('leaves').all()
for emp in employees:
    print(emp.leaves.count())  # Pas de requête supplémentaire
```

### 💾 Activer le cache

```python
# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Dans les views
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache 5 minutes
def get_statistics(request):
    # ...
    return Response(data)
```

### 📊 Indexer les colonnes fréquemment recherchées

```python
# models.py
class Employee(models.Model):
    status = models.CharField(max_length=20, db_index=True)
    department = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

# Créer les index manuellement
python manage.py shell << EOF
from django.db import connection
cursor = connection.cursor()
cursor.execute("CREATE INDEX idx_employee_status ON employees_employee(status);")
cursor.execute("CREATE INDEX idx_employee_department ON employees_employee(department);")
EOF
```

### 🔍 Profiler les performances

```bash
# Utiliser Django Debug Toolbar (développement)
pip install django-debug-toolbar

# Dans settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']

# Profiler avec Python
python -m cProfile -s cumulative manage.py runserver
```

---

## Backup & Disaster Recovery

### 💾 Backup complet

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/tkf"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup base de données
pg_dump -U tkf_user -d tkf_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup fichiers media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz backend/media/

# Backup fichiers statiques
tar -czf $BACKUP_DIR/static_$DATE.tar.gz backend/staticfiles/

# Vérifier la taille
du -sh $BACKUP_DIR/

# Archiver les anciens backups
find $BACKUP_DIR -mtime +30 -exec rm {} \;

echo "✅ Backup complété: $DATE"
```

### 📤 Restaurer un backup

```bash
# Restaurer base de données
gunzip < /backups/tkf/db_20241225_120000.sql.gz | \
  psql -U tkf_user -d tkf_db

# Restaurer media
tar -xzf /backups/tkf/media_20241225_120000.tar.gz -C backend/

# Vérifier l'intégrité
python manage.py check --deploy
```

### ☁️ Backup cloud (Azure)

```bash
#!/bin/bash
# scripts/backup-to-azure.sh

STORAGE_ACCOUNT="tkfstorage"
CONTAINER_NAME="backups"
BACKUP_FILE="db_$(date +%Y%m%d_%H%M%S).sql.gz"

# Créer le backup local
pg_dump -U tkf_user -d tkf_db | gzip > /tmp/$BACKUP_FILE

# Uploader vers Azure
az storage blob upload \
  --account-name $STORAGE_ACCOUNT \
  --container-name $CONTAINER_NAME \
  --name $BACKUP_FILE \
  --file /tmp/$BACKUP_FILE

# Nettoyer les anciens backups (garder 14 jours)
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --container-name $CONTAINER_NAME \
  --query "[?properties.creationTime < '$(date -d '14 days ago' -Iseconds)'].name" \
  --output tsv | \
  xargs -I {} az storage blob delete \
  --account-name $STORAGE_ACCOUNT \
  --container-name $CONTAINER_NAME \
  --name {}

rm /tmp/$BACKUP_FILE
echo "✅ Backup uploadé: $BACKUP_FILE"
```

---

## Maintenance Régulière

### 📅 Tâches hebdomadaires

```bash
# Nettoyer les sessions expirées
python manage.py clearsessions

# Checker l'intégrité des données
python manage.py check --deploy

# Optimiser la base de données PostgreSQL
psql -U tkf_user -d tkf_db -c "VACUUM ANALYZE;"

# Vérifier les logs
tail -100 /var/log/tkf/app.log
```

### 📅 Tâches mensuelles

```bash
# Créer un backup complet
./scripts/backup.sh

# Mettre à jour les dépendances
pip list --outdated
pip install -r requirements.txt --upgrade

# Vérifier les sécurité Django
python manage.py check --deploy --tag security

# Analyser les logs pour les patterns
grep ERROR /var/log/tkf/app.log | sort | uniq -c
```

### 📅 Tâches trimestrielles

```bash
# Audit de sécurité complet
python manage.py check --deploy
bandit -r backend/ -f json > security_report.json

# Performance review
python manage.py showmigrations --plan
django-extensions-commands

# Réconciliation des données
python manage.py shell << EOF
from apps.employees.models import Employee
from apps.cities.models import City

# Vérifier les données orphelines
orphaned_employees = Employee.objects.filter(user__isnull=True)
print(f"Orphaned employees: {orphaned_employees.count()}")
EOF
```

---

## Logs & Diagnostics

### 📝 Vérifier les logs

```bash
# Django logs
tail -f /var/log/tkf/app.log

# Nginx logs (si utilisé)
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Système logs
tail -f /var/log/syslog

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Logs filtrés
grep "ERROR" /var/log/tkf/app.log | tail -20
grep "WARNING" /var/log/tkf/app.log | wc -l
```

### 🔍 Diagnostic détaillé

```bash
# Vérifier la santé du système
python manage.py shell << EOF
import os
import django

print("=== Django Configuration ===")
print(f"DEBUG: {django.conf.settings.DEBUG}")
print(f"Allowed hosts: {django.conf.settings.ALLOWED_HOSTS}")
print(f"Installed apps: {len(django.conf.settings.INSTALLED_APPS)}")

print("\n=== Database ===")
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT VERSION();")
print(f"DB Version: {cursor.fetchone()[0]}")

print("\n=== Cache ===")
from django.core.cache import cache
cache.set('test', 'value', 10)
print(f"Cache working: {cache.get('test') == 'value'}")

print("\n=== File Storage ===")
print(f"MEDIA_ROOT: {django.conf.settings.MEDIA_ROOT}")
print(f"STATIC_ROOT: {django.conf.settings.STATIC_ROOT}")
print(f"File storage: {type(django.conf.settings.DEFAULT_FILE_STORAGE)}")
EOF
```

---

## Commandes Utiles

### 🛠️ Django Management

```bash
# Créer un superuser
python manage.py createsuperuser

# Seed les données
python manage.py seed_cities
python manage.py seed_employees

# Vider la cache
python manage.py clear_cache

# Collecter les static files
python manage.py collectstatic --noinput

# Profiler une commande
python -m cProfile -s cumulative manage.py migrate

# Shell interactif
python manage.py shell_plus  # Avec django-extensions
```

### 🐳 Docker

```bash
# Voir l'état
docker-compose ps
docker-compose stats

# Logs
docker-compose logs -f --tail=100

# Exec dans un conteneur
docker-compose exec backend python manage.py shell
docker-compose exec postgres psql -U tkf_user

# Rebuild et redémarrer
docker-compose down
docker-compose build
docker-compose up -d

# Nettoyer les resources
docker system prune -a
```

### 🔐 Sécurité

```bash
# Vérifier les secrets
grep -r "SECRET_KEY" backend/ --exclude-dir=.git

# Scan de sécurité
bandit -r backend/

# Dépendances vulnérables
pip-audit

# Check HTTPS
curl -I https://tkf.bf | grep "Strict-Transport-Security"
```

### 📊 Monitoring

```bash
# Vérifier les processus
ps aux | grep python
ps aux | grep node

# Utilisation des ressources
top
htop
free -h
df -h

# Connexions réseau
netstat -tlnp | grep -E ":8000|:5173|:5432"
```

---

## 📞 Support & Escalation

**Équipe Support**: support@tkf.bf  
**Hotline 24/7**: +226 25 30 00 00  
**Documentation**: https://github.com/ruffinh22/TRANSPORT/wiki  
**Issues**: https://github.com/ruffinh22/TRANSPORT/issues  

---

**Version**: 2.0.0  
**Dernière mise à jour**: 25 Décembre 2024  
**Status**: ✅ Production Ready
