# 📡 RUMO RUSH Backend API - Documentation Complète

**Version**: 1.0.0  
**Base URL**: `https://api.rumorush.com/api/v1/`  
**Development**: `http://localhost:8000/api/v1/`

---

## 📋 Table des Matières

1. [Authentication](#-authentication)
2. [Accounts (Utilisateurs)](#-accounts)
3. [Games (Jeux)](#-games)
4. [Payments (Paiements)](#-payments)
5. [Referrals (Parrainage)](#-referrals)
6. [Analytics (Analytiques)](#-analytics)
7. [Error Codes](#-error-codes)
8. [Rate Limiting](#-rate-limiting)

---

## 🔐 Authentication

### Login

```bash
POST /auth/login/
Content-Type: application/json

{
  "username": "user@email.com",  # email ou username
  "password": "secure_password"
}
```

**Response (200)**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "kyc_status": "approved"
  }
}
```

**cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john@example.com",
    "password": "password123"
  }'
```

### Register

```bash
POST /auth/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secure_password",
  "confirm_password": "secure_password",
  "country": "BJ",
  "phone": "+22967123456"
}
```

**Response (201)**:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Refresh Token

```bash
POST /auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Logout

```bash
POST /auth/logout/
Authorization: Bearer {access_token}
```

---

## 👥 Accounts

### Get Profile

```bash
GET /profile/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "country": "BJ",
  "profile_picture": "https://cdn.rumorush.com/avatars/user1.jpg",
  "kyc_status": "approved",
  "kyc_verified_at": "2025-11-10T15:30:00Z",
  "balance": {
    "fcfa": 50000,
    "eur": 150,
    "usd": 160
  },
  "statistics": {
    "total_games": 125,
    "wins": 87,
    "losses": 38,
    "win_rate": 69.6,
    "total_earnings": 275000,
    "rank": "Elite"
  },
  "created_at": "2025-10-01T10:00:00Z",
  "last_login": "2025-11-15T09:30:00Z"
}
```

### Update Profile

```bash
PUT /profile/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+22967123456",
  "bio": "Passionate gamer from Benin"
}
```

### Get Balance

```bash
GET /profile/balance/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "fcfa": 50000,
  "eur": 150,
  "usd": 160,
  "total_usd": 310,
  "last_updated": "2025-11-15T11:00:00Z"
}
```

### Sync Status (FeexPay)

```bash
GET /payments/sync/status/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "phone": "+22967123456",
    "balance_fcfa": 400.0
  },
  "sync_status": {
    "total_transactions": 2,
    "total_deposits": 2,
    "total_deposit_amount": 400.0,
    "last_sync": "2025-11-18T13:05:00Z",
    "period": "30 days"
  },
  "transactions": [
    {
      "id": "uuid-here",
      "type": "deposit",
      "amount": 200.0,
      "status": "completed",
      "feexpay_reference": "BEED6695-561C-4E46-8A7C-849B86EE5B94",
      "created_at": "2025-11-18T12:30:00Z"
    }
  ]
}
```

### Force Sync

```bash
POST /payments/sync/force/
Authorization: Bearer {access_token}
Content-Type: application/json

{}
```

### Balance Audit

```bash
GET /payments/sync/audit/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "phone": "+22967123456"
  },
  "audit": {
    "current_balance": 400.0,
    "calculated_balance": 400.0,
    "difference": 0.0,
    "total_deposits": 400.0,
    "total_withdrawals": 0.0,
    "is_synchronized": true,
    "audit_date": "2025-11-18T13:05:00Z"
  }
}
```

### Get Statistics

```bash
GET /profile/statistics/
Authorization: Bearer {access_token}
```

### Activity Log

```bash
GET /profile/activities/?limit=50&offset=0
Authorization: Bearer {access_token}
```

### KYC Upload

```bash
POST /kyc/upload/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

{
  "document_type": "ID_CARD",  # ID_CARD, PASSPORT, DRIVER_LICENSE
  "document_number": "12345678",
  "issue_date": "2020-01-15",
  "expiry_date": "2030-01-15",
  "file": <binary_file>
}
```

### KYC Status

```bash
GET /kyc/status/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "status": "approved",  # pending, approved, rejected
  "documents": [
    {
      "type": "ID_CARD",
      "status": "approved",
      "submitted_at": "2025-11-10T14:20:00Z",
      "verified_at": "2025-11-10T15:30:00Z"
    }
  ],
  "next_review_date": null
}
```

### Change Password

```bash
POST /auth/password/change/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_password": "old_password",
  "new_password": "new_secure_password",
  "confirm_password": "new_secure_password"
}
```

---

## 🎮 Games

### List Games

```bash
GET /games/?status=active&game_type=chess&limit=20&offset=0
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/games/?offset=20",
  "previous": null,
  "results": [
    {
      "id": "game_123",
      "game_type": "chess",
      "status": "active",
      "player1": {
        "id": 1,
        "username": "johndoe",
        "avatar": "https://cdn.rumorush.com/avatars/user1.jpg"
      },
      "player2": {
        "id": 2,
        "username": "janedoe",
        "avatar": "https://cdn.rumorush.com/avatars/user2.jpg"
      },
      "wager": 5000,
      "currency": "fcfa",
      "time_limit": 120,
      "move_count": 15,
      "created_at": "2025-11-15T10:00:00Z"
    }
  ]
}
```

### Create Game

```bash
POST /games/create/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "game_type": "chess",  # chess, checkers, ludo, cards
  "wager": 5000,
  "currency": "fcfa",
  "time_limit": 120,
  "is_private": false,
  "opponent_id": null  # null for matchmaking
}
```

**Response (201)**:
```json
{
  "id": "game_123",
  "game_type": "chess",
  "status": "waiting",
  "wager": 5000,
  "currency": "fcfa",
  "ws_url": "ws://localhost:8000/ws/game/game_123/",
  "created_at": "2025-11-15T10:30:00Z"
}
```

### Get Game Details

```bash
GET /games/{game_id}/
Authorization: Bearer {access_token}
```

### Join Game

```bash
POST /games/{game_id}/join/
Authorization: Bearer {access_token}
Content-Type: application/json

{}
```

### Make Move

```bash
POST /games/{game_id}/move/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "from": "e2",
  "to": "e4",
  "promotion": null  # for chess pawn promotion
}
```

### Surrender

```bash
POST /games/{game_id}/surrender/
Authorization: Bearer {access_token}
```

### Game History

```bash
GET /games/history/?limit=20&offset=0&filter=won
Authorization: Bearer {access_token}
```

### Leaderboard

```bash
GET /games/leaderboard/?period=month&limit=100
# period: week, month, all_time
```

**Response**:
```json
{
  "period": "month",
  "updated_at": "2025-11-15T11:00:00Z",
  "leaderboard": [
    {
      "rank": 1,
      "username": "ProPlayer",
      "country": "BJ",
      "wins": 45,
      "earnings": 450000,
      "win_rate": 90.0
    }
  ]
}
```

### Game Statistics

```bash
GET /games/statistics/
Authorization: Bearer {access_token}
```

---

## 💰 Payments

### Get Payment Methods

```bash
GET /methods/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "results": [
    {
      "id": "stripe_card",
      "name": "Card Payment",
      "icon": "💳",
      "min_amount": 1000,
      "max_amount": 5000000,
      "currency": "fcfa",
      "processing_time": "instant"
    },
    {
      "id": "mtn_mobile",
      "name": "MTN Mobile Money",
      "icon": "📱",
      "min_amount": 500,
      "max_amount": 1000000,
      "currency": "fcfa",
      "processing_time": "2-5 minutes"
    }
  ]
}
```

### Deposit

```bash
POST /deposit/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "amount": 10000,
  "currency": "fcfa",
  "payment_method": "mtn_mobile",
  "country": "BJ"
}
```

**Response (201)**:
```json
{
  "id": "txn_123",
  "status": "pending",
  "amount": 10000,
  "currency": "fcfa",
  "method": "mtn_mobile",
  "redirect_url": "https://pay.mtn.com/checkout/session123",
  "expires_at": "2025-11-15T11:30:00Z",
  "created_at": "2025-11-15T10:30:00Z"
}
```

### Withdraw

```bash
POST /withdraw/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "amount": 5000,
  "currency": "fcfa",
  "recipient_name": "John Doe",
  "recipient_phone": "+22967123456",
  "withdrawal_method": "mtn_mobile"
}
```

### Transaction History

```bash
GET /transactions/?type=all&limit=50&offset=0
# type: deposit, withdrawal, all
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "count": 125,
  "results": [
    {
      "id": "txn_123",
      "type": "deposit",
      "amount": 10000,
      "currency": "fcfa",
      "status": "completed",
      "method": "mtn_mobile",
      "created_at": "2025-11-15T10:30:00Z",
      "completed_at": "2025-11-15T10:35:00Z"
    }
  ]
}
```

### Withdrawal Status

```bash
GET /withdrawals/{withdrawal_id}/
Authorization: Bearer {access_token}
```

---

## 🎁 Referrals

### Get Referral Code

```bash
GET /code/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "code": "REF_JOHNDOE_ABC123",
  "url": "https://rumorush.com/join?ref=REF_JOHNDOE_ABC123",
  "created_at": "2025-10-01T10:00:00Z"
}
```

### Referral Statistics

```bash
GET /statistics/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "total_referrals": 15,
  "active_referrals": 12,
  "pending_commissions": 45000,
  "total_commissions": 275000,
  "commission_rate": 10,
  "referrals": [
    {
      "id": 5,
      "username": "referral_user",
      "status": "active",
      "games_played": 25,
      "earnings": 120000,
      "your_commission": 12000,
      "referred_at": "2025-11-01T10:00:00Z"
    }
  ]
}
```

### Referral Earnings

```bash
GET /earnings/
Authorization: Bearer {access_token}
```

### Premium Subscription

```bash
POST /premium/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "duration_months": 1  # or 3, 12
}
```

**Response (201)**:
```json
{
  "status": "active",
  "started_at": "2025-11-15T10:30:00Z",
  "expires_at": "2025-12-15T10:30:00Z",
  "cost": 10000,
  "currency": "fcfa",
  "benefits": [
    "Unlimited games",
    "No commission",
    "Priority support"
  ]
}
```

---

## 📊 Analytics

### Dashboard

```bash
GET /dashboard/
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "overview": {
    "total_games": 125,
    "wins": 87,
    "losses": 38,
    "total_earnings": 275000,
    "total_spent": 120000,
    "net_profit": 155000
  },
  "recent_games": [
    {
      "id": "game_123",
      "opponent": "janedoe",
      "game_type": "chess",
      "result": "win",
      "earnings": 5000,
      "played_at": "2025-11-15T10:00:00Z"
    }
  ],
  "trends": {
    "win_rate_7d": 65.0,
    "win_rate_30d": 69.6,
    "earnings_7d": 25000,
    "earnings_30d": 120000
  }
}
```

### User Analytics

```bash
GET /users/
Authorization: Bearer {access_token}
```

### Game Analytics

```bash
GET /games/?start_date=2025-11-01&end_date=2025-11-15
Authorization: Bearer {access_token}
```

---

## ⚠️ Error Codes

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| 400 | Bad Request | Invalid input | Vérifier le format des données |
| 401 | Unauthorized | Token expiré/invalide | Renouveler le token |
| 403 | Forbidden | Accès refusé | Vérifier les permissions |
| 404 | Not Found | Ressource inexistante | Vérifier l'ID |
| 409 | Conflict | État invalide | Vérifier l'état de la ressource |
| 422 | Unprocessable | Validation échouée | Vérifier les données |
| 429 | Too Many Requests | Rate limit dépassée | Attendre avant de réessayer |
| 500 | Server Error | Erreur serveur | Contacter le support |

**Exemple d'erreur**:
```json
{
  "detail": "Invalid credentials",
  "error_code": "INVALID_CREDENTIALS",
  "status": 401
}
```

---

## 🚦 Rate Limiting

**Par endpoint** (défaut) :
- **Guest** : 100 requêtes/heure
- **Authenticated** : 1000 requêtes/heure
- **VIP** : Illimité

**Headers de réponse** :
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1605516000
```

---

## 🔄 WebSockets

### Connexion Jeu

```javascript
const ws = new WebSocket(
  'ws://localhost:8000/ws/game/game_123/?token=<access_token>'
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Game update:', data);
};

// Envoyer un coup
ws.send(JSON.stringify({
  type: 'move',
  from: 'e2',
  to: 'e4'
}));
```

---

## 🛠️ Tools & SDKs

### JavaScript/TypeScript
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Python
```python
import requests

session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {access_token}'
})

response = session.get('http://localhost:8000/api/v1/profile/')
print(response.json())
```

---

## 📞 Support

- **Documentation** : https://docs.rumorush.com
- **Issues** : https://github.com/ruffinh22/rhumo_rush/issues
- **Email** : api@rumorush.com
- **Status** : https://status.rumorush.com

---

**Last Updated**: 15 November 2025  
**Version**: 1.0.0  
**Maintainer**: RUMO RUSH Dev Team
