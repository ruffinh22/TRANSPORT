# Intégration FeexPay Payout API - RUMO RUSH

## Vue d'ensemble

Intégration complète de l'API Payout de FeexPay pour permettre les retraits réels vers Mobile Money (MTN, Moov, Orange, Wave, etc.).

## Documentation FeexPay

**Endpoint principal:** `POST https://api.feexpay.me/api/payouts/public/transfer/global`
**Vérification status:** `GET https://api.feexpay.me/api/payouts/status/public/{reference}`

## Configuration

### 1. Variables d'environnement

Ajouter dans `.env.feexpay` ou `.env` :

```env
FEEXPAY_API_KEY=fp_live_votre_clé_api
FEEXPAY_SHOP_ID=votre_shop_id
```

**Où trouver ces valeurs ?**
- Connectez-vous sur https://feexpay.me
- Menu **Développeur**
- Copiez l'**API Key** et le **Shop ID**

### 2. Settings Django

Les configurations suivantes ont été ajoutées dans `backend/rumo_rush/settings/base.py` :

```python
# URLs API FeexPay
FEEXPAY_BASE_URL = 'https://api.feexpay.me'
FEEXPAY_PAYOUT_URL = 'https://api.feexpay.me/api/payouts/public/transfer/global'
FEEXPAY_PAYOUT_STATUS_URL = 'https://api.feexpay.me/api/payouts/status/public'

# Limites selon documentation FeexPay
FEEXPAY_MIN_PAYOUT = 50  # 50 FCFA minimum
FEEXPAY_MAX_PAYOUT = 100000  # 100,000 FCFA maximum
```

## Architecture Backend

### 1. Service Payout (`feexpay_payout.py`)

**Classe:** `FeexPayPayout`

**Méthodes principales:**

- `send_money()` : Envoyer de l'argent vers Mobile Money
- `check_transfer_status()` : Vérifier le statut d'un payout
- `get_supported_networks()` : Liste des réseaux supportés

**Format de requête Payout:**

```python
{
    "phoneNumber": "2290166000000",  # 10 chiffres avec préfixe 01
    "amount": 100,                    # Entier, minimum 50
    "shop": "shop_id",                # Depuis menu Développeur
    "network": "MTN",                 # MTN, MOOV, ORANGE, etc.
    "motif": "Retrait RUMO RUSH"      # Sans caractères spéciaux
}
```

**Réponse FeexPay:**

```python
{
    "phoneNumber": "2290166000000",
    "amount": 100,
    "reference": "Fdbgfd122546",     # Référence unique
    "status": "SUCCESSFUL"            # SUCCESSFUL/FAILED/PENDING
}
```

### 2. Endpoint Django (`views_withdrawal.py`)

**Route:** `POST /api/v1/payments/withdrawals/process/`

**Données requises:**

```json
{
    "amount": 1000,
    "phone_number": "22967123456",
    "network": "MTN",
    "recipient_name": "Jean Dupont"
}
```

**Réponse:**

```json
{
    "success": true,
    "status": "successful",
    "message": "Retrait de 1000 FCFA effectué vers 22967123456 (MTN)",
    "withdrawal_id": 42,
    "reference": "Fdbgfd122546",
    "fee": "100",
    "new_balance": "9000",
    "simulation": false
}
```

### 3. Gestion des statuts

**3 statuts possibles selon FeexPay:**

1. **SUCCESSFUL** : Payout réussi immédiatement
   - Withdrawal marqué comme `completed`
   - Solde utilisateur déjà déduit

2. **PENDING** : Payout en cours de traitement
   - Withdrawal reste en `pending`
   - Tâche Celery programmée pour vérifier après 5 minutes
   - Vérification automatique via `GET /api/payouts/status/public/{reference}`

3. **FAILED** : Payout échoué
   - Withdrawal marqué comme `failed`
   - Solde utilisateur restauré

### 4. Tâches Celery (`tasks.py`)

**Tâche automatique:** `check_pending_payout_status`

```python
# Vérifier un payout pending après 5 minutes
check_pending_payout_status.apply_async(
    args=[withdrawal_id],
    countdown=300  # 5 minutes
)
```

**Tâche périodique:** `check_all_pending_payouts`
- À exécuter via Celery Beat toutes les 10 minutes
- Vérifie tous les payouts pending depuis plus de 5 minutes

## Architecture Frontend

### Composant: `WithdrawalComponent.tsx`

**Modifications principales:**

1. **Montant minimum:** 50 FCFA (au lieu de 500)
2. **Gestion des 3 statuts:** SUCCESSFUL/PENDING/FAILED
3. **Affichage référence FeexPay** dans les messages et l'historique
4. **Messages colorés:**
   - ✅ Vert : SUCCESSFUL
   - ⏳ Jaune : PENDING
   - ❌ Rouge : FAILED

**Interface:**

```typescript
interface WithdrawalHistory {
  status: 'pending' | 'completed' | 'failed' | 'cancelled' | 'successful';
  reference?: string;  // Référence FeexPay
  // ...
}
```

## Workflow Complet

### 1. Utilisateur demande un retrait

```
Frontend → POST /api/v1/payments/withdrawals/process/
{
  amount: 1000,
  phone_number: "22967123456",
  network: "MTN",
  recipient_name: "Jean Dupont"
}
```

### 2. Backend traite la demande

```python
# 1. Validation des données
- Montant entre 50 et 100,000 FCFA
- Solde utilisateur suffisant (montant + frais 2%)
- Numéro et réseau valides

# 2. Déduction du solde (en production)
user.balance_fcfa -= (amount + fee)

# 3. Création du retrait en BDD
withdrawal = FeexPayWithdrawal.objects.create(...)

# 4. Appel API FeexPay Payout
response = feexpay.send_money(...)
```

### 3. Traitement selon statut

**Cas A: SUCCESSFUL**
```python
withdrawal.mark_as_completed(transfer_id=reference)
# Solde déjà déduit, transaction terminée
```

**Cas B: PENDING**
```python
withdrawal.status = 'pending'
withdrawal.feexpay_transfer_id = reference
withdrawal.save()

# Programmer vérification après 5 minutes
check_pending_payout_status.apply_async(
    args=[withdrawal.id],
    countdown=300
)
```

**Cas C: FAILED**
```python
withdrawal.mark_as_failed(error_message)
# Restaurer le solde
user.balance_fcfa += (amount + fee)
```

### 4. Vérification différée (PENDING)

```python
# Après 5 minutes, Celery exécute
def check_pending_payout_status(withdrawal_id):
    # GET /api/payouts/status/public/{reference}
    status = feexpay.check_transfer_status(reference)
    
    if status == 'successful':
        withdrawal.mark_as_completed()
    elif status == 'failed':
        withdrawal.mark_as_failed()
        user.balance_fcfa += total  # Restaurer
    elif status == 'pending':
        # Re-vérifier dans 5 min
        check_pending_payout_status.apply_async(...)
```

## Mode Test / Production

### Mode Développement (DEBUG=True)

```python
# Simulation sans appel réel API
if settings.DEBUG:
    return simulate_payout(...)  # Génère fausse référence
```

### Mode Production (DEBUG=False)

```python
# Appel réel API FeexPay
response = requests.post(
    'https://api.feexpay.me/api/payouts/public/transfer/global',
    headers={'Authorization': f'Bearer {api_key}'},
    json=payout_data
)
```

## Réseaux Supportés

Selon documentation FeexPay:

- **MTN** : MTN Mobile Money (multi-pays)
- **MOOV** : Moov Money (multi-pays)
- **ORANGE** : Orange Money (CI, SN, etc.)
- **WAVE** : Wave (CI, SN)
- **CELTIIS** : Celtiis BJ (Bénin)
- **TOGOCOM** : Togocom (Togo)
- **FREE** : Free Money (Sénégal)

## Frais de Retrait

**Calcul:** 2% du montant, minimum 100 FCFA

```python
fee_rate = Decimal('0.02')  # 2%
fee = max(amount * fee_rate, Decimal('100'))
total_deduction = amount + fee
```

**Exemple:**
- Retrait: 1000 FCFA
- Frais: 100 FCFA (2% = 20, mais min 100)
- Total déduit: 1100 FCFA

## Sécurité

1. **API Key** stockée dans variables d'environnement
2. **Header Authorization** avec Bearer token
3. **Validation stricte** des montants et formats
4. **Transaction atomique** pour éviter problèmes de concurrence
5. **Logging détaillé** de toutes les opérations

## Logs

```python
logger.info(f"💸 Appel API FeexPay Payout: {payout_data}")
logger.info(f"📤 Réponse FeexPay: {response.status_code}")
logger.info(f"✅ Retrait SUCCESSFUL - Ref: {reference}")
logger.info(f"⏳ Retrait PENDING - Vérification dans 5min")
logger.error(f"❌ Retrait FAILED - Erreur: {error}")
```

## Configuration Celery Beat

Ajouter dans `settings.py` pour vérifications périodiques:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-pending-payouts': {
        'task': 'payments.check_all_pending_payouts',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
}
```

## Tests

### Test en mode DEBUG

1. Lancer le serveur Django
2. Faire un retrait depuis le frontend
3. Vérifier les logs: `🧪 Mode DEBUG - Simulation du retrait`
4. Référence générée: UUID fake

### Test en mode PRODUCTION

1. Configurer `DEBUG=False` et variables FeexPay
2. Faire un petit retrait (ex: 100 FCFA)
3. Vérifier:
   - Appel réel API dans logs
   - Référence FeexPay retournée
   - Statut correct (SUCCESSFUL/PENDING/FAILED)
   - Solde déduit correctement
4. Si PENDING: attendre 5 min et vérifier mise à jour auto

## Dépannage

### Erreur "Erreur HTTP 401"
- Vérifier `FEEXPAY_API_KEY` correcte
- Format: `Bearer fp_live_xxxxx`

### Erreur "Erreur HTTP 400"
- Vérifier format numéro téléphone (10 chiffres avec 01)
- Vérifier montant entre 50 et 100,000
- Vérifier `FEEXPAY_SHOP_ID` correct

### Payout reste PENDING longtemps
- Normal pour certains réseaux (Orange CI, Moov CI)
- Celery task vérifie automatiquement après 5 min
- Vérifier logs Celery

### Solde non restauré après échec
- Vérifier transaction Django (atomicité)
- Vérifier logs `mark_as_failed`
- Restauration automatique dans le code

## Ressources

- **Documentation FeexPay:** https://feexpay.me/docs
- **Dashboard FeexPay:** https://feexpay.me/dashboard
- **Support FeexPay:** contact@feexpay.me
