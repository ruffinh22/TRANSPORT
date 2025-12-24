"""
Commande Django pour mettre à jour les références FeexPay manquantes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.payments.models import FeexPayWithdrawal
from apps.payments.feexpay_payout import FeexPayPayout


class Command(BaseCommand):
    help = 'Mettre à jour les références FeexPay manquantes et synchroniser les statuts'

    def handle(self, *args, **options):
        # Mapping des retraits avec leurs références FeexPay (du dashboard)
        REFERENCES_MAPPING = {
            '1f1718c5-a30b-49b9-ba39-e4739cc55fac': '74ce8827-0415-45f5-a974-0000b423f406',  # 450 FCFA
            '6254c363-56d0-41cd-9f55-ebb7bd685e00': '8874b3f5-3bd2-4e8a-8b16-03b2f3a994be',  # 550 FCFA
        }
        
        self.stdout.write("🔄 Mise à jour des références FeexPay...\n")
        
        feexpay = FeexPayPayout()
        updated = 0
        errors = 0
        
        for withdrawal_id, feexpay_reference in REFERENCES_MAPPING.items():
            try:
                withdrawal = FeexPayWithdrawal.objects.get(id=withdrawal_id)
                
                self.stdout.write(f"📝 Retrait ID: {withdrawal_id}")
                self.stdout.write(f"   Montant: {withdrawal.amount} FCFA")
                self.stdout.write(f"   Statut actuel: {withdrawal.status}")
                self.stdout.write(f"   Référence actuelle: {withdrawal.feexpay_transfer_id or 'AUCUNE'}")
                self.stdout.write(f"   Nouvelle référence: {feexpay_reference}")
                
                # Mettre à jour la référence
                withdrawal.feexpay_transfer_id = feexpay_reference
                withdrawal.save()
                self.stdout.write(self.style.SUCCESS("   ✅ Référence mise à jour"))
                
                # Vérifier le statut sur FeexPay
                result = feexpay.check_transfer_status(feexpay_reference)
                
                if result['success']:
                    status_value = result.get('status', '').lower()
                    self.stdout.write(f"   📊 Statut FeexPay: {status_value.upper()}")
                    
                    with transaction.atomic():
                        withdrawal.refresh_from_db()
                        
                        if status_value == 'successful':
                            withdrawal.mark_as_completed(
                                transfer_id=feexpay_reference,
                                response_data=result.get('data', {})
                            )
                            self.stdout.write(self.style.SUCCESS("   ✅ Retrait marqué comme COMPLETED"))
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
                            self.stdout.write(self.style.WARNING("   ❌ Retrait marqué comme FAILED (solde restauré)"))
                            updated += 1
                        else:
                            self.stdout.write("   ⏳ Retrait toujours PENDING")
                else:
                    self.stdout.write(self.style.WARNING(f"   ⚠️  Impossible de vérifier le statut: {result.get('message')}"))
                    errors += 1
                
                self.stdout.write("")
                
            except FeexPayWithdrawal.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Retrait {withdrawal_id} introuvable\n"))
                errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur pour {withdrawal_id}: {e}\n"))
                errors += 1
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✅ Mis à jour: {updated}"))
        self.stdout.write(self.style.ERROR(f"❌ Erreurs: {errors}"))
        self.stdout.write(f"📊 Total: {len(REFERENCES_MAPPING)}")
        self.stdout.write("="*60)
