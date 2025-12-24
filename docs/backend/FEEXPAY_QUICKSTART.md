# FEEXPAY_QUICKSTART.md

# 🚀 FeexPay Integration - Quick Start Guide

**Estimated Setup Time:** 15-20 minutes

---

## 1️⃣ Setup Environment Variables

```bash
# Copy the example file
cp .env.feexpay.example .env.feexpay

# Edit with your credentials
nano .env.feexpay
```

### Required Variables:
```bash
FEEXPAY_API_KEY=sk_live_your_key
FEEXPAY_SHOP_ID=shop_your_id
FEEXPAY_WEBHOOK_SECRET=whsec_your_secret
FEEXPAY_TEST_MODE=False
```

**Get these from:** [FeexPay Dashboard](https://dashboard.feexpay.io)

---

## 2️⃣ Configure Django Settings

```python
# rumo_rush/settings/production.py

# Load FeexPay config
FEEXPAY_API_KEY = os.environ.get('FEEXPAY_API_KEY')
FEEXPAY_SHOP_ID = os.environ.get('FEEXPAY_SHOP_ID')
FEEXPAY_WEBHOOK_SECRET = os.environ.get('FEEXPAY_WEBHOOK_SECRET')
FEEXPAY_TEST_MODE = os.environ.get('FEEXPAY_TEST_MODE', 'False') == 'True'

# Logging
LOGGING = {
    'loggers': {
        'feexpay': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

---

## 3️⃣ Apply Database Migrations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Verify
python manage.py migrate --plan | grep feexpay
```

---

## 4️⃣ Test the Integration

### Health Check

```bash
# Test API connectivity
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8000/api/v1/payments/feexpay/health/

# Expected response:
# {
#   "status": "healthy",
#   "api": "FeexPay",
#   "timestamp": "2024-01-15T10:00:00Z"
# }
```

### List Providers

```bash
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8000/api/v1/payments/feexpay/providers/

# Expected: List of 16 providers
```

### Initiate Test Payment

```bash
curl -X POST \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_code": "mtn",
    "amount": "50000",
    "currency": "XOF",
    "recipient_phone": "+221771234567",
    "description": "Test payment"
  }' \
  http://localhost:8000/api/v1/payments/feexpay/initiate/

# Expected response:
# {
#   "id": "tx-uuid",
#   "status": "processing",
#   "amount": "50000.00",
#   ...
# }
```

---

## 5️⃣ Configure Webhook

### In FeexPay Dashboard:

1. Go to **Settings** → **Webhooks**
2. Add new webhook URL:
   ```
   https://api.yourapp.com/api/v1/payments/feexpay/webhook/
   ```
3. Select events:
   - ✓ payment.success
   - ✓ payment.failed
   - ✓ payment.expired
   - ✓ payment.cancelled

4. Save and copy webhook secret to `FEEXPAY_WEBHOOK_SECRET`

### Test Webhook Locally:

```bash
# Generate signature
python manage.py shell
>>> import hmac, hashlib, json
>>> payload = '{"event":"payment.success","transaction_id":"tx_test","status":"successful","timestamp":"2024-01-15T10:00:00Z"}'
>>> secret = "your_webhook_secret"
>>> signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
>>> print(signature)

# Send test webhook
curl -X POST \
  -H "X-Webhook-Signature: <signature>" \
  -H "Content-Type: application/json" \
  -d '<payload>' \
  http://localhost:8000/api/v1/payments/feexpay/webhook/
```

---

## 6️⃣ Run Tests

```bash
# All FeexPay tests
pytest apps/payments/test_feexpay.py -v

# With coverage
pytest apps/payments/test_feexpay.py \
  --cov=apps.payments \
  --cov-report=html

# Specific test
pytest apps/payments/test_feexpay.py::TestFeexPayAPI::test_feexpay_initiate_payment_success -v
```

---

## 7️⃣ Django Admin Interface

### Access Admin:
```
http://localhost:8000/admin/payments/
```

### Available Options:
- **FeexPay Providers** - Manage 16 providers
  - Activate/deactivate
  - View statistics
  - Sync stats

- **FeexPay Transactions** - Track all payments
  - View status
  - Mark successful/failed
  - Retry failed payments

- **FeexPay Webhooks** - Debug webhooks
  - View received webhooks
  - Check validation status
  - Manual retry

---

## 8️⃣ Common Tasks

### Initialize Providers (One-Time)

```bash
# Using fixture (if available)
python manage.py loaddata feexpay_providers

# Or manually via admin or script
```

### Check Recent Transactions

```python
from apps.payments.models import FeexPayTransaction

# Get last 10 transactions
txs = FeexPayTransaction.objects.order_by('-created_at')[:10]

# By status
failed = FeexPayTransaction.objects.filter(status='failed')
successful = FeexPayTransaction.objects.filter(status='successful')

# By provider
mtn = FeexPayTransaction.objects.filter(provider__provider_code='mtn')
```

### Retry Failed Payments

```python
from apps.payments.models import FeexPayTransaction

# Retry all failed
for tx in FeexPayTransaction.objects.filter(status='failed', retry_count__lt=3):
    tx.retry()
```

### Monitor Success Rate

```python
from apps.payments.models import FeexPayTransaction

total = FeexPayTransaction.objects.count()
successful = FeexPayTransaction.objects.filter(status='successful').count()
success_rate = (successful / total * 100) if total > 0 else 0

print(f"Success Rate: {success_rate:.1f}% ({successful}/{total})")
```

---

## ✅ Verification Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Health check passing
- [ ] Providers list working
- [ ] Test payment can be initiated
- [ ] Webhook URL configured in FeexPay
- [ ] Webhook test passing
- [ ] All tests passing
- [ ] Admin interface accessible

---

## 🐛 Troubleshooting

### "Unauthorized - Invalid API key"
```bash
# Check .env
echo $FEEXPAY_API_KEY

# Verify key format
# Should start with: sk_live_ or sk_test_
```

### "Provider not found"
```bash
# List available providers
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/payments/feexpay/providers/

# Check provider exists
python manage.py shell
>>> from apps.payments.models import FeexPayProvider
>>> FeexPayProvider.objects.values_list('provider_code', flat=True)
```

### "Webhook signature invalid"
```bash
# Check webhook secret
echo $FEEXPAY_WEBHOOK_SECRET

# Verify HMAC calculation
python manage.py shell
>>> import hmac, hashlib
>>> secret = "your_secret"
>>> payload = "test_payload"
>>> hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
```

---

## 📚 Additional Resources

- [Full Documentation](./FEEXPAY_INTEGRATION.md)
- [API Endpoints](./FEEXPAY_INTEGRATION.md#endpoints-api)
- [Webhook Setup](./FEEXPAY_INTEGRATION.md#webhooks)
- [Error Codes](./FEEXPAY_INTEGRATION.md#gestion-des-erreurs)
- [FeexPay Docs](https://docs.feexpay.io)

---

## 🆘 Support

**Error?** Check:
1. [FEEXPAY_INTEGRATION.md - Troubleshooting](./FEEXPAY_INTEGRATION.md#troubleshooting)
2. Logs: `tail -f logs/feexpay.log`
3. Admin: Check webhook signature records
4. Tests: `pytest apps/payments/test_feexpay.py -v`

---

## ⏱️ Next Steps

1. **Test Phase:** Run full test suite
2. **Sandbox:** Test with FeexPay sandbox
3. **Staging:** Deploy to staging
4. **Production:** Deploy to production
5. **Monitor:** Watch success rates and errors

---

**Quick Reference:**

| Task | Command |
|------|---------|
| Health Check | `curl https://api/v1/payments/feexpay/health/` |
| List Providers | `curl https://api/v1/payments/feexpay/providers/` |
| Initiate Payment | `POST https://api/v1/payments/feexpay/initiate/` |
| Check Status | `GET https://api/v1/payments/feexpay/{id}/status/` |
| Run Tests | `pytest apps/payments/test_feexpay.py -v` |
| View Admin | `http://localhost:8000/admin/` |

---

**Estimated Time to Production:** 1-2 hours (including testing)

**Ready? Let's Go! 🚀**
