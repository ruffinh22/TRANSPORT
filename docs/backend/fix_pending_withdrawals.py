#!/usr/bin/env python3
"""
Script pour mettre à jour manuellement les références FeexPay manquantes
À exécuter avec: python manage.py shell < fix_pending_withdrawals.py
"""

# Ce script doit être exécuté dans le shell Django
from apps.payments.models import FeexPayWithdrawal
from apps.payments.feexpay_payout import FeexPayPayout
from django.db import transaction

# Mapping des retraits avec leurs références FeexPay (du dashboard)
REFERENCES_MAPPING = {
    '1f1718c5-a30b-49b9-ba39-e4739cc55fac': '74ce8827-0415-45f5-a974-0000b423f406',  # 450 FCFA
    '6254c363-56d0-41cd-9f55-ebb7bd685e00': '8874b3f5-3bd2-4e8a-8b16-03b2f3a994be',  # 550 FCFA
}

def update_withdrawal_references():
    """Mettre à jour les références et synchroniser les statuts"""
    
    print("🔄 Mise à jour des références FeexPay...\n")
    
    feexpay = FeexPayPayout()
    updated = 0
    errors = 0
    
    for withdrawal_id, feexpay_reference in REFERENCES_MAPPING.items():
        try:
            withdrawal = FeexPayWithdrawal.objects.get(id=withdrawal_id)
            
            print(f"📝 Retrait ID: {withdrawal_id}")
            print(f"   Montant: {withdrawal.amount} FCFA")
            print(f"   Statut actuel: {withdrawal.status}")
            print(f"   Référence actuelle: {withdrawal.feexpay_transfer_id or 'AUCUNE'}")
            print(f"   Nouvelle référence: {feexpay_reference}")
            
            # Mettre à jour la référence
            withdrawal.feexpay_transfer_id = feexpay_reference
            withdrawal.save()
            print(f"   ✅ Référence mise à jour")
            
            # Vérifier le statut sur FeexPay
            result = feexpay.check_transfer_status(feexpay_reference)
            
            if result['success']:
                status_value = result.get('status', '').lower()
                print(f"   📊 Statut FeexPay: {status_value.upper()}")
                
                with transaction.atomic():
                    withdrawal.refresh_from_db()
                    
                    if status_value == 'successful':
                        withdrawal.mark_as_completed(
                            transfer_id=feexpay_reference,
                            response_data=result.get('data', {})
                        )
                        print(f"   ✅ Retrait marqué comme COMPLETED")
                        updated += 1
                        
                    elif status_value == 'failed':
                        withdrawal.mark_as_failed(
                            error_message='Payout échoué',
                            response_data=result.get('data', {})
                        )
                        # Restaurer le solde
                        user = withdrawal.user
                        user.balance_fcfa += (withdrawal.amount + withdrawal.fee)
                        user.save()
                        print(f"   ❌ Retrait marqué comme FAILED (solde restauré)")
                        updated += 1
                    else:
                        print(f"   ⏳ Retrait toujours PENDING")
            else:
                print(f"   ⚠️  Impossible de vérifier le statut: {result.get('message')}")
                errors += 1
            
            print()
            
        except FeexPayWithdrawal.DoesNotExist:
            print(f"❌ Retrait {withdrawal_id} introuvable\n")
            errors += 1
        except Exception as e:
            print(f"❌ Erreur pour {withdrawal_id}: {e}\n")
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Mis à jour: {updated}")
    print(f"❌ Erreurs: {errors}")
    print(f"📊 Total: {len(REFERENCES_MAPPING)}")
    print(f"{'='*60}")

# Exécuter automatiquement
update_withdrawal_references()
