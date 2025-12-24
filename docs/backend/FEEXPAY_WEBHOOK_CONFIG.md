# 🔔 Configuration Webhook FeexPay - RUMO RUSH

## 📋 Informations de configuration :

**URL Webhook** : `http://154.66.133.50:8000/api/v1/payments/webhooks/feexpay/`
**Secret** : `rhXMItO8`
**Shop ID** : `67d68239474b2509dcde6d10`

## 🎯 Étapes de configuration :

### 1. Se connecter au Dashboard FeexPay
- URL : https://dashboard.feexpay.me/
- Login avec vos identifiants RUMO RUSH

### 2. Configuration Webhook
1. Aller dans **Paramètres** > **Webhooks**
2. Ajouter une nouvelle URL webhook :
   ```
   URL : http://154.66.133.50:8000/api/v1/payments/webhooks/feexpay/
   Secret : rhXMItO8
   Événements : payment.succeeded, payment.failed
   ```

### 3. Vérification
- Tester l'URL webhook depuis le dashboard
- Vérifier les logs dans l'application

## ⚠️ Note importante :
**IP locale (154.66.133.50)** pourrait ne pas être accessible depuis l'extérieur.
Pour une solution permanente, déployer sur :
- DigitalOcean, AWS, Heroku, etc.
- Obtenir une IP publique fixe

## 🧪 Test du webhook :
```bash
curl -X POST http://154.66.133.50:8000/api/v1/payments/webhooks/feexpay/ \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

## ✅ Une fois configuré :
- Les paiements FeexPay se synchroniseront automatiquement
- Plus besoin de correction manuelle
- Ana et autres utilisateurs auront leurs soldes mis à jour en temps réel