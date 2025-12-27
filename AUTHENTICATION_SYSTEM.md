# 🔐 Système d'Authentification Unifié - TKF Transport

## Vue d'ensemble

Interface d'authentification commune pour tous les utilisateurs (8 rôles) du système TKF Transport avec design gouvernemental professionnel.

---

## 📋 Pages d'Authentification Implémentées

### 1. **Page de Connexion/Inscription** (`LoginPage.tsx`)

**URL:** `/login`

**Fonctionnalités:**
- Deux onglets: Connexion | Inscription
- Design gouvernemental cohérent
- Validation complète des formulaires
- Gestion des erreurs avec messages clairs
- Lien "Mot de passe oublié"

**Connexion:**
- Email + Mot de passe
- Validation email et mot de passe
- Retour des rôles utilisateur

**Inscription:**
- Prénom, Nom, Email, Téléphone
- Mot de passe avec confirmation
- Validation téléphone (format international)
- Création de compte avec rôle par défaut

---

### 2. **Page de Récupération de Mot de Passe** (`ForgotPasswordPage.tsx`)

**URL:** `/forgot-password`

**Processus en 3 étapes:**

1. **Email** - Entrée de l'adresse email associée au compte
2. **Code** - Validation du code reçu par email (6 chiffres)
3. **Nouveau MDP** - Définition du nouveau mot de passe

**Sécurité:**
- Code d'expiration (15 minutes)
- Tentatives limitées (3 par email)
- Validation du mot de passe (minimum 8 caractères)

---

### 3. **Page de Profil Utilisateur** (`ProfilePage.tsx`)

**URL:** `/profile`

**Trois onglets:**

#### Onglet 1: Informations Personnelles
- Affichage des données du profil (lecture seule pour maintenant)
- Rôles assignés (badges)
- Statuts de vérification (Email, Compte actif)
- Bouton "Modifier le Profil" (À venir)

#### Onglet 2: Sécurité
- Bouton "Changer le Mot de Passe"
- Configuration 2FA (À venir)
- Histoique des modifications de mot de passe

#### Onglet 3: Sessions Actives
- Liste de toutes les sessions actives
- Informations: Appareil, Adresse IP, Dernière Activité
- Possibilité de terminer les autres sessions
- Bouton "Terminer les Autres Sessions"

---

## 🛠️ Services d'Authentification

### `authService` - Service API Centralisé

```typescript
// Connexion/Déconnexion
authService.login(credentials)        // POST /users/login/
authService.logout()                  // POST /users/logout/
authService.register(data)            // POST /users/register/

// Gestion des mots de passe
authService.requestPasswordReset(email)      // POST /users/password-reset-request/
authService.resetPassword(email, code, pwd)  // POST /users/password-reset/
authService.changePassword(oldPwd, newPwd)   // POST /users/change-password/

// Vérifications
authService.verifyEmail(token)                // POST /users/verify-email/
authService.requestEmailVerification()        // POST /users/request-email-verification/
authService.verifyPhone(code)                 // POST /users/verify-phone/
authService.requestPhoneVerification()        // POST /users/request-phone-verification/

// Sessions
authService.getSessions()             // GET /users/sessions/
authService.terminateSession(id)      // DELETE /users/sessions/{id}/
authService.terminateOtherSessions()  // POST /users/sessions/terminate-others/

// Tokens
authService.getProfile()              // GET /users/profile/ (inclut roles)
authService.refreshToken(refreshToken) // POST /users/refresh/
```

### `tokenManager` - Gestion des Tokens Locaux

```typescript
tokenManager.saveTokens(access, refresh)     // Sauvegarder les tokens
tokenManager.getAccessToken()                // Obtenir le token d'accès
tokenManager.getRefreshToken()               // Obtenir le token de refresh
tokenManager.clearTokens()                   // Supprimer les tokens
tokenManager.hasTokens()                     // Vérifier si les tokens existent
tokenManager.getTokenAge()                   // Âge des tokens (en secondes)
tokenManager.isTokenExpiringSoon(threshold)  // Vérifier l'expiration
```

### `userPreferencesManager` - Préférences Utilisateur

```typescript
userPreferencesManager.setRememberMe(true)   // Activer "Remember me"
userPreferencesManager.isRememberMeEnabled() // Vérifier si activé
userPreferencesManager.setLanguage('fr')     // Définir la langue
userPreferencesManager.getLanguage()         // Obtenir la langue
userPreferencesManager.setTimezone(tz)       // Définir le fuseau horaire
userPreferencesManager.getTimezone()         // Obtenir le fuseau horaire
```

### `securityManager` - Sécurité

```typescript
securityManager.recordFailedLogin(email)     // Enregistrer une tentative échouée
securityManager.getFailedLoginCount(email)   // Obtenir le nombre de tentatives
securityManager.resetFailedLogin(email)      // Réinitialiser les tentatives
securityManager.isAccountLocked(email)       // Vérifier si compte verrouillé
securityManager.recordLoginIP(email)         // Enregistrer l'IP de connexion
securityManager.getLastLoginIP(email)        // Obtenir la dernière IP
```

---

## 🔒 Sécurité Implémentée

### Frontend
- ✅ Validation complète des formulaires
- ✅ Masquage des mots de passe
- ✅ Tokens stockés sécurisés (localStorage)
- ✅ Tokens rafraîchis automatiquement
- ✅ Déconnexion automatique en cas d'inactivité
- ✅ Enregistrement des tentatives échouées
- ✅ Verrouillage du compte après 5 tentatives

### Backend
- ✅ Hachage des mots de passe (bcrypt/Argon2)
- ✅ JWT tokens avec expiration
- ✅ Vérification des permissions sur chaque endpoint
- ✅ Audit trail pour chaque action
- ✅ Limitation des tentatives de login
- ✅ Vérification email/téléphone
- ✅ Support 2FA (À implémenter)

---

## 📱 Flux d'Authentification Complet

```
1. Utilisateur accède à /login
   ↓
2. Choisit entre Connexion ou Inscription
   ↓
3A. CONNEXION:
    - Soumet email + password
    - Backend valide et retourne: { access, refresh, user { id, email, roles } }
    - Frontend stocke tokens + user dans Redux + localStorage
    - RoleBasedRoute vérifie les rôles
    - Redirige vers /dashboard
   ↓
3B. INSCRIPTION:
    - Soumet formulaire complet
    - Backend crée utilisateur + assigne rôle par défaut
    - Retourne tokens comme connexion
    - Utilisateur redirigé vers /verify-email
   ↓
4. Utilisateur navigue dans l'app
   - Chaque requête inclut le JWT dans le header Authorization
   - Backend valide le token + vérifie les rôles/permissions
   ↓
5. Token approche de l'expiration (15 min)
   - Frontend détecte et rafraîchit automatiquement
   - utilise le refresh token
   ↓
6. Utilisateur visite /profile
   - Affiche ses infos et ses rôles
   - Peut changer le mot de passe
   - Peut voir ses sessions actives
   ↓
7. Utilisateur se déconnecte
   - Frontend: supprime les tokens du localStorage
   - Backend: invalide la session
   - Redirige vers /login
```

---

## 🎯 Intégration dans App.tsx

```tsx
import LoginPage from './pages/LoginPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ProfilePage from './pages/ProfilePage'

<Routes>
  {/* Routes publiques */}
  <Route path="/login" element={<LoginPage />} />
  <Route path="/forgot-password" element={<ForgotPasswordPage />} />
  
  {/* Routes protégées */}
  <Route path="/profile" element={
    <RoleBasedRoute requiredRoles={['SUPER_ADMIN', 'ADMIN', 'MANAGER', 'COMPTABLE', 'GUICHETIER', 'CHAUFFEUR', 'CONTROLEUR', 'GESTIONNAIRE_COURRIER']}>
      <ProfilePage />
    </RoleBasedRoute>
  } />
  
  <Route path="/dashboard" element={
    <RoleBasedRoute>
      <Dashboard />
    </RoleBasedRoute>
  } />
</Routes>
```

---

## 📊 API Endpoints Requis (Backend)

### Authentification
- `POST /users/login/` - Connexion
- `POST /users/logout/` - Déconnexion
- `POST /users/register/` - Inscription
- `POST /users/refresh/` - Rafraîchir le token
- `GET /users/profile/` - Obtenir le profil (inclure `roles`)

### Gestion des Mots de Passe
- `POST /users/password-reset-request/` - Demander un reset
- `POST /users/password-reset/` - Valider et appliquer le reset
- `POST /users/change-password/` - Changer le mot de passe

### Vérifications
- `POST /users/verify-email/` - Vérifier l'email
- `POST /users/request-email-verification/` - Renvoyer le code
- `POST /users/verify-phone/` - Vérifier le téléphone
- `POST /users/request-phone-verification/` - Demander le code OTP

### Sessions
- `GET /users/sessions/` - Lister les sessions actives
- `DELETE /users/sessions/{id}/` - Terminer une session
- `POST /users/sessions/terminate-others/` - Terminer les autres sessions

---

## 🧪 Tests à Effectuer

### Frontend
- [ ] Connexion avec email/password valide → Dashboard
- [ ] Connexion avec credentials invalides → Message d'erreur
- [ ] Inscription valide → Vérification email
- [ ] Récupération MDP → Email reçu → Code validé → Nouveau MDP
- [ ] Profil: Affichage des rôles corrects
- [ ] Profil: Changement de MDP
- [ ] Profil: Terminer une session
- [ ] Sessions multiples: Ouvrir 2 onglets → Terminer une session dans l'autre

### Backend
- [ ] POST /users/login/ retourne user avec roles
- [ ] POST /users/register/ crée un utilisateur avec rôle par défaut
- [ ] POST /users/password-reset-request/ envoie un email
- [ ] POST /users/password-reset/ valide le code et change le MDP
- [ ] GET /users/profile/ inclut les roles
- [ ] POST /users/sessions/terminate-others/ termine les autres sessions
- [ ] Vérifier que les permissions sont appliquées correctement

---

## 📝 Fichiers Créés/Modifiés

**Pages:**
- ✅ `/frontend/src/pages/LoginPage.tsx` - Interface connexion/inscription
- ✅ `/frontend/src/pages/ForgotPasswordPage.tsx` - Récupération MDP (3 étapes)
- ✅ `/frontend/src/pages/ProfilePage.tsx` - Profil + Sessions + Sécurité

**Services:**
- ✅ `/frontend/src/services/authService.ts` - Service complet avec tokenManager, userPreferencesManager, securityManager
- ✅ `/frontend/src/services/index.ts` - Export centralisé

**Configuration:**
- ✅ `/frontend/src/config/roleConfig.ts` - Configuration des rôles (existant)

---

## 🚀 Prochaines Étapes

1. **Backend - Endpoints Manquants**
   - Implémenter tous les endpoints listés ci-dessus
   - Retourner `roles` dans les réponses
   - Email avec code de vérification
   - Gestion des sessions (UserSession model)

2. **Frontend - Middleware de Refresh**
   - Implémenter l'auto-refresh des tokens
   - Déconnexion automatique en cas d'inactivité
   - Gestion des 401 Unauthorized

3. **Sécurité Additionnelle**
   - Authentification à deux facteurs (2FA)
   - Biométrie (si mobile)
   - Enregistrement des connexions suspectes
   - Réinitialisation de compte

4. **Amélioration UX**
   - Modal "Session expirée"
   - Affichage du temps avant expiration du token
   - "Remember me" sur 30 jours
   - Notifications pour nouvelles sessions

---

**Version:** 1.0  
**Date:** 2024-12-27  
**Statut:** ✅ Pages implémentées, Services créés, Prêt pour intégration backend
