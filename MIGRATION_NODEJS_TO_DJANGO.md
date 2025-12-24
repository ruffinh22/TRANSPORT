# Migration Node.js/Express → Django

## 📋 Résumé des changements technologiques

Cette documentation décrit la migration de l'architecture backend de **Node.js/Express** vers **Django/Python**.

---

## 🔄 Comparaison Avant/Après

| Aspect | Avant (Node.js) | Après (Django) |
|--------|-----------------|----------------|
| **Runtime** | Node.js 18+ LTS | Python 3.11+ |
| **Framework** | Express.js 4.x | Django 4.2 LTS |
| **Langage** | TypeScript | Python |
| **ORM** | Sequelize / TypeORM | Django ORM (built-in) |
| **Validation** | Joi | DRF Serializers + Pydantic |
| **Authentification** | jsonwebtoken + bcrypt | djangorestframework-simplejwt + bcrypt |
| **Autorisation** | Middleware custom | Django Permissions + RBAC |
| **Cache** | Redis | Redis + Django Cache Framework |
| **Task Queue** | node-cron | Celery + Celery Beat |
| **Logging** | winston | Python logging + Django logging |
| **Testing** | Jest + Supertest | pytest + pytest-django |
| **API Docs** | Swagger/OpenAPI | drf-spectacular (OpenAPI) |
| **Rest API** | Express.js routes | Django REST Framework (DRF) |

---

## ✅ Avantages de Django

### 1. **Framework "Batteries Included"**
- ORM complète (pas besoin de Sequelize)
- Admin interface automatique (gestion DB)
- Migrations intégrées
- Authentification built-in
- Permissions & RBAC natives

### 2. **Django REST Framework (DRF)**
- Serializers automatiques
- Viewsets génériques (CRUD automatique)
- Pagination, Filtering, Search built-in
- Versioning API
- Throttling & Rate Limiting

### 3. **Écosystème Mature**
- Communauté très active
- Nombreuses librairies tierces
- Bien documenté
- Production-ready

### 4. **Sécurité**
- CSRF Protection automatique
- SQL Injection prevention (ORM)
- XSS Protection
- Password hashing natif
- OWASP compliance

### 5. **Performance**
- Caching framework intégré
- Database connection pooling
- QuerySet optimization (select_related, prefetch_related)
- Async views avec Django 3.1+

### 6. **Scalabilité**
- Celery pour async tasks
- Redis pour caching
- Load balancing facile
- Stateless architecture native

---

## 📦 Structure Fichiers

### Node.js Structure
```
backend/
├── src/
│   ├── controllers/
│   ├── models/
│   ├── routes/
│   ├── middleware/
│   ├── services/
│   └── utils/
├── tests/
├── package.json
└── tsconfig.json
```

### Django Structure (Nouvelle)
```
backend/
├── config/
│   ├── settings.py        ✨ Remplace .env + config
│   ├── urls.py            ✨ Remplace routes
│   ├── wsgi.py
│   ├── celery.py          ✨ Nouveau
│   └── asgi.py
├── apps/
│   ├── users/
│   │   ├── models.py      ✨ Remplace models
│   │   ├── serializers.py ✨ Remplace pas d'équivalent
│   │   ├── views.py       ✨ Remplace controllers
│   │   ├── urls.py        ✨ Remplace routes
│   │   └── tests.py
│   ├── trips/
│   ├── tickets/
│   ├── ...
│   └── common/
│       ├── models.py
│       ├── permissions.py
│       └── exceptions.py
├── tasks/                 ✨ Nouveau (Celery tasks)
├── middleware/
├── manage.py              ✨ CLI Django
├── requirements.txt       ✨ Remplace package.json
├── .env.example
└── pytest.ini
```

---

## 🔄 Correspondances de Concepts

### Express Routes → Django URLs

#### Avant (Express)
```typescript
// routes/users.ts
router.post('/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findOne({ where: { email } });
  
  if (!user || !bcrypt.compareSync(password, user.passwordHash)) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  
  const token = jwt.sign({ userId: user.id }, SECRET_KEY);
  res.json({ access: token });
});

router.get('/users', authenticateJWT, async (req, res) => {
  const users = await User.findAll();
  res.json(users);
});
```

#### Après (Django)
```python
# apps/users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

class LoginView(TokenObtainPairView):
    # JWT login automatique avec djangorestframework-simplejwt
    pass

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        users = User.objects.all()
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

# apps/users/urls.py
router = DefaultRouter()
router.register(r'users', UserViewSet)
urlpatterns = router.urls
```

### ORM: Sequelize → Django ORM

#### Avant (Sequelize)
```typescript
// models/User.ts
const User = sequelize.define('User', {
  id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
  email: { type: DataTypes.STRING, unique: true },
  passwordHash: { type: DataTypes.STRING },
  firstName: { type: DataTypes.STRING },
  role: { type: DataTypes.ENUM('ADMIN', 'USER') },
  isActive: { type: DataTypes.BOOLEAN, defaultValue: true },
  createdAt: { type: DataTypes.DATE },
  updatedAt: { type: DataTypes.DATE }
});

// Usage
const user = await User.findByPk(1);
const users = await User.findAll({ where: { isActive: true } });
```

#### Après (Django ORM)
```python
# apps/users/models.py
class User(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN'
        USER = 'USER'
    
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'users'

# Usage
user = User.objects.get(pk=1)
users = User.objects.filter(is_active=True)
```

### Middleware: Custom → Django Middleware

#### Avant (Express)
```typescript
// middleware/auth.ts
export const authenticateJWT = (req: Request, res: Response, next: Function) => {
  const token = req.headers.authorization?.split(' ')[1];
  
  if (!token) return res.status(401).json({ error: 'No token' });
  
  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    (req as any).userId = decoded.userId;
    next();
  } catch (err) {
    res.status(401).json({ error: 'Invalid token' });
  }
};

router.get('/trips', authenticateJWT, getTripHandler);
```

#### Après (Django)
```python
# config/middleware.py
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth = JWTAuthentication()
        try:
            user, validated_token = auth.authenticate(request)
            request.user = user
            request.token = validated_token
        except:
            pass
        return None

# config/settings.py
MIDDLEWARE = [
    # ... autres
    'config.middleware.JWTMiddleware',
]

# Ou plus simplement, utiliser les permissions DRF
# apps/trips/views.py
class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
```

### Validation: Joi → DRF Serializers

#### Avant (Joi)
```typescript
// schemas/tripSchema.ts
const tripSchema = Joi.object({
  routeId: Joi.number().required(),
  vehicleId: Joi.number().required(),
  departureDateTime: Joi.date().required(),
  pricePerSeat: Joi.number().min(0).required(),
  status: Joi.string().valid('PLANNED', 'IN_PROGRESS', 'COMPLETED')
});

router.post('/trips', async (req, res) => {
  const { error, value } = tripSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.message });
  
  const trip = await Trip.create(value);
  res.json(trip);
});
```

#### Après (Django)
```python
# apps/trips/serializers.py
class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'route', 'vehicle', 'departure_datetime', 
                  'price_per_seat', 'status']
        read_only_fields = ['id']
    
    def validate_price_per_seat(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate(self, data):
        if data['departure_datetime'] <= timezone.now():
            raise serializers.ValidationError("Departure must be in future")
        return data

# apps/trips/views.py
class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]
    # Validation automatique via serializer
```

### Task Queue: node-cron → Celery

#### Avant (node-cron)
```typescript
// tasks/scheduler.ts
import cron from 'node-cron';

cron.schedule('0 0 * * *', async () => {
  console.log('Running daily task');
  const trips = await Trip.findAll({ 
    where: { departureDate: today } 
  });
  // Process trips
  await sendNotifications(trips);
});

cron.schedule('*/30 * * * *', async () => {
  console.log('Running every 30 minutes');
  await updateTicketStatus();
});
```

#### Après (Celery)
```python
# apps/trips/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Trip

@shared_task
def generate_daily_trips():
    """Générer les trajets quotidiens à 00:00"""
    print('Running daily task')
    today = timezone.now().date()
    trips = Trip.objects.filter(departure_date=today)
    # Process trips
    send_notifications(trips)

@shared_task
def update_ticket_status():
    """Mettre à jour statut des billets toutes les 30 min"""
    print('Running every 30 minutes')
    # Update logic

# config/celery.py (Configuration)
app.conf.beat_schedule = {
    'generate-daily-trips': {
        'task': 'apps.trips.tasks.generate_daily_trips',
        'schedule': crontab(hour=0, minute=0),
    },
    'update-ticket-status': {
        'task': 'apps.trips.tasks.update_ticket_status',
        'schedule': crontab(minute='*/30'),
    },
}
```

### Testing: Jest → pytest

#### Avant (Jest)
```typescript
// tests/users.test.ts
describe('User API', () => {
  test('POST /api/users/login should return token', async () => {
    const response = await request(app)
      .post('/api/users/login')
      .send({ email: 'user@test.com', password: 'password123' });
    
    expect(response.status).toBe(200);
    expect(response.body.access).toBeDefined();
  });
  
  test('GET /api/users should return user list', async () => {
    const response = await request(app)
      .get('/api/users')
      .set('Authorization', `Bearer ${token}`);
    
    expect(response.status).toBe(200);
    expect(Array.isArray(response.body)).toBe(true);
  });
});
```

#### Après (pytest)
```python
# tests/test_users.py
import pytest
from django.test import APIClient
from apps.users.models import User

@pytest.mark.django_db
class TestUserAPI:
    @pytest.fixture
    def client(self):
        return APIClient()
    
    def test_login_returns_token(self, client):
        response = client.post('/api/v1/auth/login/', {
            'email': 'user@test.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert 'access' in response.data
    
    def test_list_users_requires_auth(self, client):
        response = client.get('/api/v1/users/')
        assert response.status_code == 401
    
    def test_list_users_with_auth(self, client):
        user = User.objects.create_user(
            email='user@test.com',
            password='password123'
        )
        client.force_authenticate(user=user)
        response = client.get('/api/v1/users/')
        
        assert response.status_code == 200
        assert isinstance(response.data, list)
```

---

## 🚀 Avantages Spécifiques pour TKF

### 1. **Admin Interface Django**
- Gestion automatique des utilisateurs, trajets, billets
- Pas besoin de développer une interface admin séparée
- Permissions granulaires

### 2. **Celery + Celery Beat**
- Meilleure intégration pour les tâches asynchrones
- Monitoring intégré
- Retry automatique avec backoff exponentiel
- Priorités de tâches

### 3. **Django ORM pour Requêtes Complexes**
```python
# Requête complexe simple en Django
trips = Trip.objects \
    .filter(status='COMPLETED') \
    .select_related('vehicle', 'route') \
    .prefetch_related('tickets') \
    .aggregate(
        total_revenue=Sum('tickets__price'),
        avg_seats_sold=Avg('tickets__count')
    )
```

### 4. **Migrations Intégrées**
```bash
python manage.py makemigrations  # Créer migration auto
python manage.py migrate         # Appliquer
python manage.py showmigrations  # Voir l'état
```

### 5. **Permissions RBAC Native**
```python
class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return Trip.objects.all()
        return Trip.objects.filter(driver=self.request.user)
```

---

## 📊 Comparaison Performance

| Métrique | Node.js | Django | Vainqueur |
|----------|---------|--------|----------|
| **Startup** | ~500ms | ~1-2s | Node.js |
| **Memory Usage** | ~50MB | ~80MB | Node.js |
| **Throughput (req/s)** | ~1000 | ~1500 | Django |
| **ORM Queries** | Explicit | Optimized | Django |
| **Built-in Features** | Minimal | Extensive | Django |

*Note: Django est plus lourd au démarrage mais plus performant en production avec optimisations ORM*

---

## 📈 Migration Timeline

| Phase | Durée | Activités |
|-------|-------|-----------|
| **Phase 1: Setup** | 1 semaine | Configurer Django, PostgreSQL, Redis |
| **Phase 2: Models** | 2 semaines | Créer modèles Django (Users, Trips, Tickets, etc.) |
| **Phase 3: APIs** | 3 semaines | Créer ViewSets DRF, Serializers, Tests |
| **Phase 4: Celery** | 1 semaine | Configurer Celery tasks, Beat scheduler |
| **Phase 5: Testing** | 1 semaine | Tests unitaires, intégration, coverage |
| **Phase 6: Deploy** | 1 semaine | Docker, CI/CD, monitoring |
| **Total** | **9 semaines** | Environ 2 mois pour migration complète |

---

## ✨ Conclusion

La migration vers **Django** offre :
- ✅ Framework mature et éprouvé en production
- ✅ Écosystème riche et communauté active
- ✅ Sécurité et performance améliorées
- ✅ Maintenance à long terme facilitée
- ✅ Scalabilité supérieure
- ✅ Admin interface gratuite
- ✅ Meilleur support des tâches asynchrones

**Django est le choix optimal pour une application d'entreprise comme TKF.**

---

**Document créé**: Décembre 2024  
**Version**: 1.0  
**Status**: Approuvé
