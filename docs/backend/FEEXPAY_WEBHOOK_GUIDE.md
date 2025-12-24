# 🔔 Guide Webhook FeexPay

## Configuration des Webhooks

Les webhooks permettent à FeexPay de notifier votre serveur en temps réel lorsqu'un paiement est complété, échoue ou est remboursé.

### 1. URL Webhook dans le Dashboard FeexPay

1. Connectez-vous au dashboard FeexPay
2. Allez dans **Settings** → **Webhooks**
3. Ajoutez l'URL webhook:
   - **Production**: `https://www.rumorush.com/api/v1/payments/feexpay/webhook/`
   - **Staging**: `https://staging.rumorush.com/api/v1/payments/feexpay/webhook/`
   - **Développement local** (voir section ngrok): `https://your-ngrok-url.ngrok.io/api/v1/payments/feexpay/webhook/`

4. Copiez le **Webhook Secret** fourni par FeexPay
5. Mettez le secret dans votre fichier `.env.feexpay`:
   ```dotenv
   FEEXPAY_WEBHOOK_SECRET=rhXMItO8
   ```

### 2. Événements Webhook

FeexPay envoie les événements suivants:

```json
{
  "event_type": "payment.completed|payment.failed|payment.pending|refund.issued",
  "transaction_id": "txn_abc123xyz",
  "reference": "ORDER_12345",
  "amount": 50000,
  "currency": "FCFA",
  "provider": "mtn_ci",
  "status": "completed|failed|pending",
  "timestamp": "2025-11-15T12:30:45Z",
  "metadata": {
    "user_id": 123,
    "game_id": 456
  }
}
```

### 3. Vérification de la Signature Webhook

Le client FeexPay valide automatiquement la signature:

```python
from apps.payments.feexpay_client import FeexPayClient

client = FeexPayClient()

# Vérifier la signature (appelé automatiquement dans les vues)
is_valid = client.verify_webhook_signature(
    payload_str,
    signature_header
)
```

### 4. Traitement du Webhook

La vue Django gère automatiquement:
- ✅ Vérification de la signature
- ✅ Validation du payload JSON
- ✅ Mise à jour du statut de la transaction
- ✅ Notification de l'utilisateur
- ✅ Logging des erreurs

```python
POST /api/v1/payments/feexpay/webhook/
Content-Type: application/json
X-FeexPay-Signature: hmac_sha256_signature

{
  "event_type": "payment.completed",
  "transaction_id": "txn_123",
  ...
}

# Réponse
200 OK
{
  "status": "ok"
}
```

---

## 🔗 Tester les Webhooks Localement avec ngrok

### Installation de ngrok

```bash
# Sur macOS
brew install ngrok

# Sur Linux
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip
unzip ngrok-v3-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin/
```

### Utilisation

1. **Démarrez votre serveur Django**:
   ```bash
   cd /home/lidruf/rhumo_rush/backend
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Exposez le port local avec ngrok**:
   ```bash
   ngrok http 8000
   ```

   Vous obtiendrez une URL comme:
   ```
   Forwarding: https://abc123xyz.ngrok.io -> http://localhost:8000
   ```

3. **Configurez l'URL webhook dans le dashboard FeexPay**:
   ```
   https://abc123xyz.ngrok.io/api/v1/payments/feexpay/webhook/
   ```

4. **Testez avec curl**:
   ```bash
   curl -X POST https://abc123xyz.ngrok.io/api/v1/payments/feexpay/webhook/ \
     -H "Content-Type: application/json" \
     -H "X-FeexPay-Signature: your_signature_here" \
     -d '{
       "event_type": "payment.completed",
       "transaction_id": "txn_test_123",
       "reference": "ORDER_12345",
       "amount": 50000,
       "currency": "FCFA",
       "provider": "mtn_ci",
       "status": "completed"
     }'
   ```

5. **Vérifiez les logs**:
   ```bash
   tail -f /home/lidruf/rhumo_rush/backend/logs/django.log
   ```

### Générer une Signature Valide

```python
import hmac
import hashlib
import json

payload = {
    "event_type": "payment.completed",
    "transaction_id": "txn_test_123",
}

secret = "rhXMItO8"
payload_str = json.dumps(payload, separators=(',', ':'))

signature = hmac.new(
    secret.encode(),
    payload_str.encode(),
    hashlib.sha256
).hexdigest()

print(f"X-FeexPay-Signature: {signature}")
```

---

## 🚨 Monitoring des Webhooks

### Logs FeexPay

Les logs sont stockés dans:
```
/home/lidruf/rhumo_rush/backend/logs/django.log
/home/lidruf/rhumo_rush/backend/logs/django.json.log (format JSON)
```

### Exemple de Log

```json
{
  "timestamp": "2025-11-15T12:30:45Z",
  "level": "INFO",
  "logger": "apps.payments",
  "message": "Webhook reçu",
  "event_type": "payment.completed",
  "transaction_id": "txn_abc123",
  "status": "success"
}
```

### Vérifier l'État des Webhooks

```bash
# Compter les webhooks reçus
grep -c "Webhook reçu" /home/lidruf/rhumo_rush/backend/logs/django.log

# Afficher les webhooks reçus aujourd'hui
grep "Webhook reçu" /home/lidruf/rhumo_rush/backend/logs/django.log | \
  grep "$(date +%Y-%m-%d)"

# Afficher les erreurs de webhook
grep "ERROR.*webhook" /home/lidruf/rhumo_rush/backend/logs/django.log
```

---

## 📋 Checklist Webhook

- [ ] Dashboard FeexPay configuré avec URL webhook
- [ ] Secret webhook placé dans `.env.feexpay`
- [ ] ngrok installé et testé localement
- [ ] Endpoint `/api/v1/payments/feexpay/webhook/` accessible
- [ ] Signature webhook validée
- [ ] Logs webhook vérifiés
- [ ] Transactions DB mises à jour au réception du webhook
- [ ] Utilisateurs notifiés après paiement
- [ ] Erreurs webhook loggées et alertées
- [ ] URL webhook en production déployée

---

## 🔐 Sécurité des Webhooks

✅ **Signature HMAC-SHA256** validée pour chaque webhook
✅ **CSRF exempt** pour l'endpoint webhook (nécessaire pour les webhooks externes)
✅ **HTTPS obligatoire** en production
✅ **IP whitelist** recommandée (configurable dans le dashboard FeexPay)
✅ **Rate limiting** appliqué aux endpoints normaux

---

## 🐛 Troubleshooting

| Problème | Solution |
|----------|----------|
| Signature invalide | Vérifiez que `FEEXPAY_WEBHOOK_SECRET` est correct |
| 404 Not Found | Vérifiez que l'URL webhook est correcte dans le dashboard |
| 500 Server Error | Vérifiez les logs: `tail -f logs/django.error.log` |
| ngrok expire | Les URLs ngrok expirent après 2h, relancez ngrok |
| Webhook non reçu | Assurez-vous que le serveur Django écoute sur `0.0.0.0:8000` |

