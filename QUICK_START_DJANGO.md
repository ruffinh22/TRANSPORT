# 🚀 Quick Start Guide - TKF Django Backend

Guide pour démarrer rapidement le développement du backend TKF.

## 📦 Installation Rapide (5 minutes)

### 1. Cloner et entrer dans le répertoire
```bash
cd /home/lidruf/TRANSPORT/backend
```

### 2. Créer l'environnement virtuel
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 4. Copier et configurer .env
```bash
cp .env.example .env
nano .env  # Éditer si nécessaire
```

### 5. Initialiser la base de données
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Démarrer le serveur
```bash
python manage.py runserver
```

✅ L'API est maintenant accessible à : **http://localhost:8000**

---

## 🐳 Démarrage avec Docker (3 minutes)

### 1. Depuis la racine du projet
```bash
cd /home/lidruf/TRANSPORT
```

### 2. Copier .env.example
```bash
cp backend/.env.example backend/.env
```

### 3. Démarrer tous les services
```bash
docker-compose up -d
```

### 4. Créer le super utilisateur
```bash
docker-compose exec backend python manage.py createsuperuser
```

### 5. Vérifier le statut
```bash
docker-compose ps
```

✅ Services disponibles :
- **API** : http://localhost:8000
- **Frontend** : http://localhost:3000
- **Docs API** : http://localhost:8000/api/v1/docs/
- **Admin Django** : http://localhost:8000/admin/

---

## 🧭 Les Commandes Essentielles

### Gestion de la Base de Données
```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Revenir à une migration précédente
python manage.py migrate apps.users 0001

# Voir l'état des migrations
python manage.py showmigrations
```

### Créer une Nouvelle App Django
```bash
python manage.py startapp apps/mon_app
```

### Tests
```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_users.py

# Avec couverture
pytest --cov=apps

# Verbose
pytest -v
```

### Shell Django
```bash
python manage.py shell
# Puis dans le shell:
# >>> from apps.users.models import User
# >>> User.objects.all()
```

### Collecte des assets statiques
```bash
python manage.py collectstatic
```

### Nettoyer les données de test
```bash
python manage.py flush --no-input
```

---

## 🔄 Avec Celery (Tâches asynchrones)

### Terminal 1 : Serveur Django
```bash
python manage.py runserver
```

### Terminal 2 : Celery Worker
```bash
celery -A config worker --loglevel=info
```

### Terminal 3 : Celery Beat (Scheduler)
```bash
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Monitorer Celery
```bash
celery -A config events
```

---

## 🔍 Accès à l'Admin Django

1. Allez sur : **http://localhost:8000/admin/**
2. Connectez-vous avec vos identifiants super utilisateur
3. Gérez les utilisateurs, les données, etc.

---

## 📚 Documentation API

### Swagger UI
```
http://localhost:8000/api/v1/docs/
```

### ReDoc
```
http://localhost:8000/api/v1/redoc/
```

### Schema OpenAPI JSON
```
http://localhost:8000/api/v1/schema/
```

---

## 🐛 Dépannage

### Erreur : Port 8000 déjà utilisé
```bash
# Trouver le processus
lsof -i :8000

# Tuer le processus
kill -9 <PID>
```

### Erreur de connexion à PostgreSQL
```bash
# Vérifier que PostgreSQL est démarré
sudo service postgresql status

# Ou avec Docker
docker-compose up -d postgres
```

### Erreur de migration
```bash
# Réinitialiser les migrations (ATTENTION: données perdues)
python manage.py migrate --fake apps.mon_app zero
python manage.py migrate apps.mon_app
```

### Vider le cache Redis
```bash
redis-cli FLUSHALL
```

---

## 📝 Créer une Feature Complète

### 1. Créer la Model
```bash
# models.py
from django.db import models
from apps.common.models import BaseModel

class MonModele(BaseModel):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    
    class Meta:
        app_label = 'mon_app'
        verbose_name = 'Mon Modèle'
```

### 2. Créer le Serializer
```bash
# serializers.py
from rest_framework import serializers
from .models import MonModele

class MonModeleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonModele
        fields = ['id', 'nom', 'description', 'created_at']
```

### 3. Créer la Vue
```bash
# views.py
from rest_framework import viewsets
from .models import MonModele
from .serializers import MonModeleSerializer

class MonModeleViewSet(viewsets.ModelViewSet):
    queryset = MonModele.objects.all()
    serializer_class = MonModeleSerializer
```

### 4. Enregistrer les routes
```bash
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonModeleViewSet

router = DefaultRouter()
router.register(r'mon-modele', MonModeleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

### 5. Migrer
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 📦 Ajouter une nouvelle dépendance

```bash
# Installer la dépendance
pip install nouvelle-librairie

# Ajouter à requirements.txt
pip freeze | grep nouvelle-librairie >> requirements.txt

# Ou manuellement
echo "nouvelle-librairie==version" >> requirements.txt
```

---

## 🌍 Variables d'environnement essentielles

```bash
DEBUG=False
DJANGO_SECRET_KEY=your-super-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,api.example.com
DB_NAME=tkf_db
DB_USER=postgres
DB_PASSWORD=yourpassword
REDIS_HOST=localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## 🎯 Prochaines étapes

1. ✅ Installer et tester l'environnement
2. 📖 Lire la [documentation Django](https://docs.djangoproject.com/)
3. 📖 Lire la [documentation DRF](https://www.django-rest-framework.org/)
4. 🔗 Parcourir `SPECIFICATIONS_TECHNIQUES.md` pour l'architecture
5. 💻 Créer votre première app
6. 🧪 Écrire vos premiers tests
7. 📝 Consulter les endpoints dans le Swagger

---

## 📞 Besoin d'aide ?

- Documentation : https://docs.tkf.com
- Issues : GitHub Issues
- Email : support@tkf.com

---

**Happy Coding! 🚀**
