# Module Utilisateurs et Authentification

## Description

Module de gestion complète des utilisateurs, authentification JWT, et autorisation basée sur les rôles (RBAC).

## Caractéristiques

- ✅ **User Model personnalisé** avec email au lieu de username
- ✅ **Authentification JWT** avec djangorestframework-simplejwt
- ✅ **RBAC** (Role-Based Access Control)
- ✅ **Vérification multi-étapes** (email, téléphone, document)
- ✅ **Gestion des sessions** avec refresh tokens
- ✅ **Sécurité** : blocage de compte, verrouillage après tentatives, hachage bcrypt
- ✅ **Audit trail** automatique
- ✅ **Admin panel** complet avec filtrage avancé

## Structure des Modèles

### User
Modèle utilisateur personnalisé avec :
- Authentification par email et téléphone
- Vérification d'email, téléphone, et document
- Support de profils employés/chauffeurs
- Gestion bancaire
- Préférences de notification
- Sécurité (blocage, verrouillage)

### UserSession
Gestion des sessions utilisateurs :
- Refresh tokens
- Expiration de session
- Logout (déconnexion)
- Tracking de device et IP

## API Endpoints

### Authentification

**POST** `/api/v1/users/auth/register/`
```json
{
  "email": "user@example.com",
  "phone": "+237670000000",
  "first_name": "John",
  "last_name": "Doe",
  "password": "password123",
  "password2": "password123"
}
```

**POST** `/api/v1/users/auth/login/`
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": { /* UserDetailSerializer */ }
}
```

**POST** `/api/v1/users/auth/refresh/`
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**POST** `/api/v1/users/auth/logout/`
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Profil Utilisateur

**GET** `/api/v1/users/me/`
Retourne les infos de l'utilisateur actuel

**PUT/PATCH** `/api/v1/users/update_profile/`
Mettre à jour le profil utilisateur

**POST** `/api/v1/users/change_password/`
```json
{
  "old_password": "password123",
  "new_password": "newpassword123",
  "new_password2": "newpassword123"
}
```

### Vérification

**POST** `/api/v1/users/{id}/verify_email/`
Vérifier l'email de l'utilisateur

**POST** `/api/v1/users/{id}/verify_phone/`
Vérifier le téléphone de l'utilisateur

### Gestion des Sessions

**GET** `/api/v1/users/sessions/`
Lister toutes les sessions actives de l'utilisateur

**POST** `/api/v1/users/logout_all/`
Terminer toutes les autres sessions

### Admin (Rôle requis: ADMIN)

**GET** `/api/v1/users/`
Lister tous les utilisateurs

**POST** `/api/v1/users/{id}/block/`
Bloquer un utilisateur
```json
{
  "reason": "Motif du blocage"
}
```

**POST** `/api/v1/users/{id}/unblock/`
Débloquer un utilisateur

## Usage

### Créer un utilisateur (en Python)
```python
from apps.users.models import User

user = User.objects.create_user(
    email='user@example.com',
    phone='+237670000000',
    first_name='John',
    last_name='Doe',
    password='password123'
)
```

### Vérifier les permissions
```python
user = User.objects.get(email='user@example.com')

# Vérifier un rôle
if user.has_role('ADMIN'):
    # L'utilisateur est admin
    pass

# Vérifier une permission
if user.has_permission('users.manage_users'):
    # L'utilisateur peut gérer les utilisateurs
    pass
```

### Bloquer/Débloquer un utilisateur
```python
user = User.objects.get(email='user@example.com')

# Bloquer
user.block('Raison du blocage')

# Débloquer
user.unblock()
```

## Permissions

Les permissions sont gérées à travers les rôles. Les rôles système disponibles :

- **SUPER_ADMIN** : Accès complet
- **ADMIN** : Gestion administrative
- **MANAGER** : Gestion opérationnelle
- **DRIVER** : Chauffeur
- **EMPLOYEE** : Employé
- **CUSTOMER** : Client

## Tests

Exécuter les tests :
```bash
pytest apps/users/tests.py -v

# Avec coverage
pytest apps/users/tests.py --cov=apps.users --cov-report=html
```

## Logging et Audit

Chaque création/modification d'utilisateur est automatiquement enregistrée dans :
- **AuditTrail** : Historique complet des modifications
- **SystemLog** : Logs système pour debugging

## Sécurité

- Mots de passe hashés avec bcrypt
- Tokens JWT avec expiration
- Sessions avec refresh tokens
- Verrouillage après 5 tentatives échouées (30 min)
- CORS configuré
- Rate limiting recommandé au niveau du reverse proxy (Nginx)

## Configuration

Variables d'environnement dans `.env` :
```
# JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=3600  # 1 heure
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 jours

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Intégration

Ce module s'intègre avec :
- **apps.common** : Modèles de base, Rôles, Permissions
- **Celery** : Tasks asynchrones (email, SMS)
- **Django Admin** : Interface administrative complète
