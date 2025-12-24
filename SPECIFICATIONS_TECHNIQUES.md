# Spécifications Techniques - Système TKF

## 1. Stack Technologique

### 1.1 Frontend
- **Framework** : React 18+ avec TypeScript
- **État Global** : Redux Toolkit + Redux Thunk
- **Routage** : React Router v6
- **UI Components** : Material-UI (MUI) v5
- **Formulaires** : React Hook Form + Zod (validation)
- **HTTP Client** : Axios avec intercepteurs
- **Mapping** : Leaflet + react-leaflet
- **Graphiques** : Chart.js / Recharts
- **Build Tool** : Vite
- **Package Manager** : npm

### 1.2 Backend
- **Runtime** : Python 3.11+ 
- **Framework** : Django 4.2+ LTS
- **REST API** : Django REST Framework (DRF)
- **Langage** : Python
- **ORM** : Django ORM (built-in)
- **Validation** : Serializers DRF + Pydantic
- **Authentification** : JWT (djangorestframework-simplejwt) + bcrypt
- **Autorisation** : Role-Based Access Control (RBAC) + Django Permissions
- **Cache** : Redis + Django Cache Framework
- **Task Scheduler** : Celery + Beat
- **Logging** : Python logging + Django logging
- **Testing** : pytest + pytest-django
- **API Documentation** : drf-spectacular (OpenAPI/Swagger)
- **Background Jobs** : Celery

### 1.3 Base de Données
- **Système Principal** : PostgreSQL 14+
- **Cache** : Redis 7+
- **Migrations** : Sequelize CLI ou Knex
- **Backup** : Sauvegarde quotidienne

### 1.4 Infrastructure & DevOps
- **Containerisation** : Docker + Docker Compose
- **Orchestration** : Kubernetes (optionnel, production)
- **CI/CD** : GitHub Actions
- **Déploiement** : 
  - Développement : Docker Compose local
  - Production : Cloud (AWS EC2 / Azure / Digital Ocean)
- **Reverse Proxy** : Nginx
- **Monitoring** : Prometheus + Grafana
- **Logs** : ELK Stack (Elasticsearch, Logstash, Kibana)

### 1.5 Sécurité & Authentification
- **Authentification** : JWT Token (Access + Refresh Token)
- **Hash Passwords** : bcrypt (10 rounds minimum)
- **CORS** : Configuré par domaine
- **Rate Limiting** : express-rate-limit
- **Input Validation** : Joi schemas
- **HTTPS/TLS** : Certificat SSL obligatoire
- **OWASP Compliance** : Protection XSS, CSRF, SQL Injection

### 1.6 APIs & Intégrations
- **Format API** : REST + JSON
- **Documentation** : Swagger UI
- **Versioning** : /api/v1, /api/v2
- **Pagination** : Limit + Offset
- **Paiements** : Intégration Stripe / Wave Money
- **SMS** : Intégration Twilio / Orange Money API
- **Email** : SendGrid / Nodemailer
- **Mapping/Géolocalisation** : OpenStreetMap / Google Maps API
- **Notifications** : Firebase Cloud Messaging (FCM)

## 2. Architecture Système

### 2.1 Architecture Frontend
```
frontend/
├── public/
├── src/
│   ├── components/        # Composants réutilisables
│   ├── pages/            # Pages principales
│   ├── services/         # Services API
│   ├── store/            # Redux store
│   ├── hooks/            # Custom hooks
│   ├── types/            # TypeScript interfaces
│   ├── utils/            # Utilitaires
│   ├── assets/           # Images, icônes, styles
│   └── App.tsx
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 2.2 Architecture Backend
```
backend/
├── manage.py               # Point d'entrée Django
├── config/                 # Configuration projet
│   ├── settings.py         # Paramètres Django
│   ├── urls.py             # Routing principal
│   ├── wsgi.py             # WSGI config
│   ├── asgi.py             # ASGI config (WebSocket)
│   └── celery.py           # Configuration Celery
├── apps/
│   ├── cities/             # App gestion villes
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── vehicles/           # App gestion véhicules
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── employees/          # App gestion personnel
│   ├── trips/              # App gestion trajets
│   ├── tickets/            # App vente billets
│   ├── parcels/            # App gestion colis
│   ├── payments/           # App paiements
│   ├── revenues/           # App recettes
│   ├── users/              # App utilisateurs & authentification
│   └── common/             # Services communs
│       ├── models.py       # Modèles abstraits
│       ├── serializers.py  # Serializers génériques
│       ├── permissions.py  # Permissions RBAC
│       ├── exceptions.py   # Exceptions custom
│       └── utils.py        # Utilitaires
├── middleware/             # Middlewares custom
├── tasks/                  # Tâches Celery
├── static/                 # Assets statiques
├── media/                  # Fichiers uploadés
├── requirements.txt        # Dépendances Python
├── .env.example            # Variables d'environnement
├── docker-compose.yml      # Docker Compose config
├── Dockerfile              # Image Docker
└── pytest.ini              # Configuration pytest
```

## 3. Modules Fonctionnels

### 3.1 Gestion des Villes & Itinéraires
- **API Endpoints** :
  - `POST /api/v1/cities` - Créer ville
  - `GET /api/v1/cities` - Lister villes
  - `PUT /api/v1/cities/:id` - Modifier ville
  - `DELETE /api/v1/cities/:id` - Supprimer ville
  - `POST /api/v1/routes` - Créer itinéraire
  - `GET /api/v1/routes` - Lister itinéraires

### 3.2 Gestion des Véhicules
- **API Endpoints** :
  - `POST /api/v1/vehicles` - Enregistrer véhicule
  - `GET /api/v1/vehicles` - Lister véhicules
  - `PUT /api/v1/vehicles/:id` - Modifier véhicule
  - `GET /api/v1/vehicles/:id/maintenance` - Suivi entretien
  - `POST /api/v1/vehicles/:id/fuel-log` - Enregistrer consommation

### 3.3 Gestion du Personnel
- **Rôles** : Chauffeur, Receveur, Guichetier, Contrôleur, Agent Courrier, Admin
- **API Endpoints** :
  - `POST /api/v1/employees` - Créer employé
  - `GET /api/v1/employees` - Lister employés
  - `POST /api/v1/employees/:id/assign-trip` - Affecter trajet

### 3.4 Vente de Tickets
- **API Endpoints** :
  - `POST /api/v1/tickets` - Créer billet
  - `GET /api/v1/tickets/:id` - Détails billet
  - `PUT /api/v1/tickets/:id/status` - Changer statut
  - `GET /api/v1/tickets/validate` - Validation billet

### 3.5 Gestion des Trajets
- **API Endpoints** :
  - `POST /api/v1/trips` - Créer trajet
  - `GET /api/v1/trips` - Lister trajets
  - `PUT /api/v1/trips/:id/status` - Mettre à jour statut
  - `GET /api/v1/trips/:id/tracking` - Suivi en temps réel

### 3.6 Gestion des Courriers
- **API Endpoints** :
  - `POST /api/v1/parcels` - Enregistrer colis
  - `GET /api/v1/parcels` - Lister colis
  - `PUT /api/v1/parcels/:id/status` - Changer statut
  - `GET /api/v1/parcels/:id/tracking` - Suivi colis

### 3.7 Gestion des Recettes
- **API Endpoints** :
  - `GET /api/v1/revenues` - Consulter recettes
  - `GET /api/v1/revenues/daily` - Recettes journalières
  - `GET /api/v1/revenues/monthly` - Recettes mensuelles

### 3.8 Tableau de Bord
- **Dashboards** :
  - Dashboard Administrateur (KPIs globaux)
  - Dashboard Opérateur (Trajets actifs)
  - Dashboard Finance (Recettes, dépenses)
  - Dashboard Courrier (Parcels tracking)

## 4. Modèle de Données (PostgreSQL)

### Tables Principales
- `users` - Utilisateurs et authentification
- `employees` - Personnel
- `cities` - Villes
- `routes` - Itinéraires
- `vehicles` - Véhicules
- `vehicle_maintenance` - Entretien véhicules
- `trips` - Trajets
- `trip_employees` - Affectation personnel/trajets
- `tickets` - Billets
- `parcels` - Colis/Courriers
- `parcel_shipments` - Expéditions colis
- `payments` - Paiements
- `revenue_logs` - Logs recettes
- `audit_logs` - Logs d'audit

## 5. Flux de Sécurité

### 5.1 Authentification
1. User POST `/api/v1/auth/login` avec email + password
2. Backend valide + retourne JWT (Access Token 1h + Refresh Token 7j)
3. Frontend stocke tokens en localStorage/sessionStorage
4. Chaque requête inclut token en header `Authorization: Bearer <token>`
5. Middleware vérifie signature JWT

### 5.2 Autorisation
- Rôles : ADMIN, MANAGER, DRIVER, CASHIER, CONTROLLER, PARCEL_AGENT
- Permissions par endpoint
- Middleware RBAC vérifie permission avant exécution

## 6. Déploiement

### 6.1 Développement Local
```bash
docker-compose up -d
# Lance PostgreSQL, Redis, Frontend, Backend
```

### 6.2 Production
```bash
# Build images Docker
docker build -t tkf-frontend ./frontend
docker build -t tkf-backend ./backend

# Push vers registry
docker push myregistry/tkf-frontend
docker push myregistry/tkf-backend

# Déployer sur serveur (AWS/Azure/Digital Ocean)
kubectl apply -f k8s/deployment.yaml
```

### 6.3 CI/CD Pipeline
- GitHub Actions: test, build, deploy
- Tests automatiques sur chaque PR
- Staging environment avant production
- Blue-green deployment

## 7. Performance & Scalabilité

- **Caching** : Redis pour sessions, queries
- **Database Indexing** : Indexes sur colonnes critiques
- **Connection Pooling** : PgBouncer / node-pool
- **Load Balancing** : Nginx reverse proxy
- **CDN** : CloudFlare pour assets statiques
- **Pagination** : 50 items par défaut

## 8. Monitoring & Observabilité

- **Application Metrics** : Prometheus
- **Dashboards** : Grafana
- **Logs** : ELK Stack
- **Error Tracking** : Sentry
- **APM** : New Relic (optionnel)

## 9. Compliance & Standards

- ✅ OWASP Top 10
- ✅ GDPR (si données EU)
- ✅ PCI DSS (si paiements)
- ✅ Audit logs pour traçabilité
- ✅ Sauvegarde données (Daily backup)

---

**Date** : 24 Décembre 2024  
**Version** : 1.0  
**Statut** : Approuvé
