#!/bin/bash
# Script de vérification rapide FeexPay

echo "🔍 Vérification FeexPay - $(date)"
echo "=================================="

# Aller dans le répertoire backend
cd /var/www/html/rhumo1/backend

echo "📊 Dernières transactions FeexPay (5 dernières):"
python manage.py shell --settings=rumo_rush.settings.development << 'EOF'
from apps.payments.models import FeexPayTransaction
from django.utils import timezone

txs = FeexPayTransaction.objects.order_by('-created_at')[:5]
for tx in txs:
    status_emoji = "✅" if tx.status == 'completed' else "⏳" if tx.status == 'pending' else "❌"
    print(f"{status_emoji} {tx.external_reference} | {tx.amount}€ | {tx.status} | {tx.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
EOF

echo ""
echo "⏳ Transactions en attente:"
python manage.py shell --settings=rumo_rush.settings.development << 'EOF'
from apps.payments.models import FeexPayTransaction

pending = FeexPayTransaction.objects.filter(status='pending').count()
print(f"Nombre de transactions en attente: {pending}")
EOF

echo ""
echo "💰 Statistiques du jour:"
python manage.py shell --settings=rumo_rush.settings.development << 'EOF'
from apps.payments.models import FeexPayTransaction
from django.utils import timezone
from decimal import Decimal

today = timezone.now().date()
today_txs = FeexPayTransaction.objects.filter(created_at__date=today)

total = today_txs.count()
completed = today_txs.filter(status='completed').count()
total_amount = sum(tx.amount for tx in today_txs.filter(status='completed'))

print(f"Transactions aujourd'hui: {total}")
print(f"Transactions complétées: {completed}")
print(f"Montant total traité: {total_amount}€")
if total > 0:
    success_rate = (completed / total) * 100
    print(f"Taux de réussite: {success_rate:.1f}%")
EOF

echo ""
echo "🔄 Pour surveillance continue:"
echo "python monitor_feexpay.py monitor"