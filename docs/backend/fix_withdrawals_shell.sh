#!/bin/bash
# Script pour corriger les retraits via shell Django

cd /var/www/html/backend

cat << 'EOF' | python manage.py shell
from apps.payments.models import FeexPayWithdrawal
from apps.payments.feexpay_payout import FeexPayPayout
from django.db import transaction

# Mapping des retraits
REFS = {
    '1f1718c5-a30b-49b9-ba39-e4739cc55fac': '74ce8827-0415-45f5-a974-0000b423f406',
    '6254c363-56d0-41cd-9f55-ebb7bd685e00': '8874b3f5-3bd2-4e8a-8b16-03b2f3a994be',
}

print("🔄 Correction des retraits FeexPay...\n")

feexpay = FeexPayPayout()
updated = 0

for wid, ref in REFS.items():
    try:
        w = FeexPayWithdrawal.objects.get(id=wid)
        print(f"📝 {w.amount} FCFA - Status: {w.status}")
        
        # Mettre à jour référence
        w.feexpay_transfer_id = ref
        w.save()
        print(f"   Ref: {ref}")
        
        # Vérifier statut
        result = feexpay.check_transfer_status(ref)
        
        if result['success']:
            status = result.get('status', '').lower()
            print(f"   FeexPay: {status.upper()}")
            
            with transaction.atomic():
                w.refresh_from_db()
                
                if status == 'successful':
                    w.mark_as_completed(
                        transfer_id=ref,
                        response_data=result.get('data', {})
                    )
                    print(f"   ✅ COMPLETED")
                    updated += 1
                elif status == 'failed':
                    w.mark_as_failed(
                        error_message='Échoué',
                        response_data=result.get('data', {})
                    )
                    user = w.user
                    user.balance_fcfa += (w.amount + w.fee)
                    user.save()
                    print(f"   ❌ FAILED")
                    updated += 1
        else:
            print(f"   ⚠️  Erreur: {result.get('message')}")
        
        print()
    except Exception as e:
        print(f"❌ Erreur: {e}\n")

print(f"✅ Mis à jour: {updated}")
EOF

echo ""
echo "✅ Terminé !"
