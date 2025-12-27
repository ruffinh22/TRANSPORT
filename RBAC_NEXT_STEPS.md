# 🚀 Prochaines Étapes RBAC Integration

## Statut Actuel: Infrastructure Complète ✅

La structure RBAC est en place. Il reste à intégrer dans l'application et tester.

---

## 📋 Checklist d'Intégration - Phase 1

### Frontend Integration (2-3 heures)

- [ ] **App.tsx - Remplacer routes protégées**
  ```tsx
  // Avant
  <Route path="/trips" element={<TripsPage />} />
  
  // Après
  <Route path="/trips" element={
    <RoleBasedRoute requiredRoles={['ADMIN', 'MANAGER', 'CHAUFFEUR']}>
      <TripsPage />
    </RoleBasedRoute>
  } />
  ```
  
  **Pages à protéger:**
  - `/trips` → ['ADMIN', 'MANAGER', 'CHAUFFEUR']
  - `/tickets` → ['ADMIN', 'MANAGER', 'GUICHETIER', 'CONTROLEUR']
  - `/parcels` → ['ADMIN', 'MANAGER', 'GESTIONNAIRE_COURRIER']
  - `/payments` → ['ADMIN', 'COMPTABLE', 'GUICHETIER']
  - `/employees` → ['ADMIN', 'MANAGER']
  - `/cities` → ['ADMIN', 'MANAGER']
  - `/reports` → ['ADMIN', 'MANAGER', 'COMPTABLE']
  - `/settings` → ['ADMIN']
  - `/dashboard` → [tous]

- [ ] **ResponsiveAppBar - Intégrer RoleBasedMenu**
  ```tsx
  import { RoleBasedMenu } from '../components'
  
  <Drawer>
    <RoleBasedMenu onNavigate={(path) => navigate(path)} />
  </Drawer>
  ```

- [ ] **Pages - Cacher les boutons selon permissions**
  ```tsx
  const { hasRole } = useRoleBasedAccess()
  
  // Bouton Ajouter
  {(hasRole('ADMIN') || hasRole('MANAGER')) && (
    <Button onClick={handleAdd}>Ajouter</Button>
  )}
  ```

- [ ] **Test chaque page avec différents rôles**

---

### Backend Integration (2-3 heures)

- [ ] **ViewSets - Ajouter @require_permission**
  
  **TripsViewSet** (`/backend/apps/trips/views.py`):
  ```python
  from apps.common.decorators import require_permission
  
  class TripsViewSet(viewsets.ModelViewSet):
      def list(self, request, *args, **kwargs):
          if not request.user.has_permission('trips.view_trip'):
              return Response({...}, status=403)
          return super().list(...)
      
      def create(self, request, *args, **kwargs):
          if not request.user.has_permission('trips.manage_trips'):
              return Response({...}, status=403)
          return super().create(...)
  ```
  
  **ViewSets à protéger:**
  - TripsViewSet
  - TicketsViewSet
  - ParcelsViewSet
  - PaymentsViewSet
  - VehiclesViewSet
  - EmployeesViewSet (Users)
  - CitiesViewSet
  - ReportsViewSet

- [ ] **Filtering - Filtrer les données selon rôles**
  ```python
  def get_queryset(self):
      user = self.request.user
      
      # Chauffeur ne voit que ses trajets
      if user.has_role('CHAUFFEUR'):
          return Trip.objects.filter(driver=user.employee)
      
      # Admin voit tous les trajets
      return Trip.objects.all()
  ```

- [ ] **Utilitaire - Ajouter helper à User model**
  ```python
  # /backend/apps/users/models.py
  
  class User(AbstractUser):
      def has_role(self, role_code):
          return self.roles.filter(code=role_code).exists()
      
      def has_permission(self, permission_code):
          perms = []
          for role in self.roles.all():
              if isinstance(role.permissions, list):
                  perms.extend(role.permissions)
          return permission_code in perms
  ```

- [ ] **Tester chaque endpoint avec curl/Postman**
  ```bash
  # Login avec Guichetier
  curl -X POST http://localhost:8000/users/login/ \
    -H "Content-Type: application/json" \
    -d '{"email": "guichetier@transport.local", "password": "GuichGuich123"}'
  
  # Vérifier que roles est dans la réponse
  # {
  #   "user": {
  #     "id": 3,
  #     "email": "guichetier@transport.local",
  #     "roles": ["GUICHETIER"],
  #     ...
  #   },
  #   "access": "...",
  #   "refresh": "..."
  # }
  ```

---

## 📊 Plan d'Exécution Détaillé

### Jour 1 - Frontend (3-4 heures)

**Matin (1.5h):**
1. [ ] Créer des tests utilisateur avec chaque rôle
2. [ ] Ajouter RoleBasedRoute pour chaque page
3. [ ] Intégrer RoleBasedMenu dans ResponsiveAppBar

**Après-midi (1.5h):**
4. [ ] Cacher les boutons "Ajouter/Modifier/Supprimer" selon rôles
5. [ ] Tester manuellement chaque page
6. [ ] Build et commit

**Commit:** `✅ Frontend RBAC integration complete`

---

### Jour 2 - Backend (3-4 heures)

**Matin (2h):**
1. [ ] Ajouter helpers au User model
2. [ ] Protéger TripsViewSet
3. [ ] Protéger TicketsViewSet

**Après-midi (2h):**
4. [ ] Protéger les 5 autres ViewSets
5. [ ] Tester avec Postman
6. [ ] Commit

**Commit:** `✅ Backend RBAC integration complete`

---

### Jour 3 - Tests E2E (2-3 heures)

**Matin (1.5h):**
1. [ ] Créer 7 utilisateurs test (1 par rôle)
2. [ ] Tests d'accès sur chaque page
3. [ ] Tests d'API avec JWT tokens

**Après-midi (1h):**
4. [ ] Valider que les permissions fonctionnent
5. [ ] Documer les résultats

**Commit:** `✅ RBAC integration tests passed`

---

## 🎯 Critères de Validation

### Frontend
- [ ] RoleBasedRoute protège toutes les pages
- [ ] Menu affiche uniquement les items accessibles
- [ ] Boutons cachés selon les rôles
- [ ] AccessDenied page affichée correctement
- [ ] Build sans erreurs

### Backend
- [ ] Endpoints retournent 403 si unauthorized
- [ ] Querysets filtrés correctement par rôles
- [ ] Roles dans les API responses
- [ ] Audit trail enregistre les accès refusés
- [ ] Tests passent

### E2E
- [ ] ADMIN voit toutes les pages
- [ ] GUICHETIER ne voit que Tickets/Paiements
- [ ] CHAUFFEUR ne voit que ses trajets
- [ ] GESTIONNAIRE_COURRIER ne voit que Parcels
- [ ] Utilisateur non-authentifié redirigé vers login

---

## 📚 Ressources

**Documentation créée:**
- `RBAC_IMPLEMENTATION.md` - Overview complet
- `BACKEND_RBAC_GUIDE.md` - Guide détaillé backend
- `RBAC_COMPLETION_SUMMARY.md` - Statut actuel

**Code source créé:**
- `/frontend/src/components/RoleBasedRoute.tsx`
- `/frontend/src/components/AccessDenied.tsx`
- `/frontend/src/components/RoleBasedMenu.tsx`
- `/frontend/src/hooks/useRoleBasedAccess.ts`
- `/frontend/src/config/roleConfig.ts`
- `/backend/apps/common/permissions.py`
- `/backend/apps/common/decorators.py`

---

## 🧪 Commandes Utiles

### Backend - Django
```bash
# Initialiser les rôles (déjà fait)
python manage.py init_roles

# Shell Django
python manage.py shell

# Tester les permissions
from apps.users.models import User
from apps.common.models import Role
user = User.objects.get(email='guichetier@transport.local')
user.has_role('GUICHETIER')  # True
user.has_permission('tickets.view_ticket')  # True
```

### Frontend - React
```bash
# Build
yarn build

# Dev
yarn dev

# Test
yarn test
```

### Testing - Postman/cURL
```bash
# Login
curl -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "guichetier@transport.local", "password": "GuichGuich123"}'

# Utiliser le token
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/trips/
```

---

## ⚠️ Pièges à Éviter

1. **Frontend only checks** - ❌ JAMAIS faire confiance au frontend seul
2. **Oublier de filtrer les données** - Inclure les check dans les querysets
3. **Encoder les rôles en dur** - Utiliser la config roleConfig.ts
4. **Oublier l'audit trail** - Logger les accès refusés
5. **Pas de test du multi-rôles** - Un user peut avoir plusieurs rôles

---

## 📞 Support

Pour poser une question ou signaler un problème:
1. Vérifier la documentation
2. Vérifier le code des composants existants
3. Consulter le guide backend

---

**Prêt pour:** ✅ Intégration complète  
**Temps estimé:** 8-10 heures  
**Deadline recommandée:** J+2
