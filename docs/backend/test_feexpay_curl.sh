#!/bin/bash

# Script de test simple pour FeexPay avec curl
echo "🧪 TEST FEEXPAY AVEC CURL"
echo "=========================="

# Variables
BASE_URL="http://localhost:8000"
TRANSACTION_ID="252b9473-e206-4931-aedd-90d7c4f99daa"
USERNAME="hounsounon07@gmail.com"
PASSWORD="password123"

echo "🔐 Étape 1: Connexion pour obtenir le token"
echo "----------------------------------------------"

# Tentative de connexion
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}")

echo "📡 Réponse login: $LOGIN_RESPONSE"

# Extraire le token (si JWT)
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access', data.get('token', data.get('access_token', '')));" 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "" ]; then
    echo "❌ Échec obtention token. Tentative sans authentification..."
    
    echo ""
    echo "🧪 Test sans authentification (pour voir l'erreur complète)"
    echo "--------------------------------------------------------"
    
    curl -X POST "${BASE_URL}/api/v1/payments/deposits/confirm/" \
      -H "Content-Type: application/json" \
      -d "{
        \"transaction_id\": \"${TRANSACTION_ID}\",
        \"feexpay_reference\": \"${TRANSACTION_ID}\",
        \"amount\": 100,
        \"status\": \"completed\"
      }" \
      -v
else
    echo "✅ Token obtenu: ${TOKEN:0:20}..."
    
    echo ""
    echo "📡 Étape 2: Test de confirmation FeexPay"
    echo "----------------------------------------"
    
    curl -X POST "${BASE_URL}/api/v1/payments/deposits/confirm/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${TOKEN}" \
      -d "{
        \"transaction_id\": \"${TRANSACTION_ID}\",
        \"feexpay_reference\": \"${TRANSACTION_ID}\",
        \"amount\": 100,
        \"status\": \"completed\"
      }" \
      -v
fi

echo ""
echo ""
echo "🔍 Vérification de la transaction dans la DB"
echo "============================================="

python3 -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from apps.payments.models import Transaction

try:
    tx = Transaction.objects.get(id='$TRANSACTION_ID')
    print(f'✅ Transaction trouvée:')
    print(f'  ID: {tx.id}')
    print(f'  User: {tx.user.username} ({tx.user.email})')
    print(f'  Status: {tx.status}')
    print(f'  Amount: {tx.amount} {tx.currency}')
    print(f'  External Ref: {tx.external_reference}')
except Exception as e:
    print(f'❌ Erreur: {e}')
"