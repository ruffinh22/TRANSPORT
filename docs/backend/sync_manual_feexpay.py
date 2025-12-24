#!/usr/bin/env python
"""
Script de synchronisation manuelle FeexPay
Utilise les données que vous copiez depuis le dashboard FeexPay
"""
import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
sys.path.append('/var/www/html/rhumo1/backend')
django.setup()

from django.contrib.auth import get_user_model
from apps.payments.models import Transaction, PaymentMethod
from decimal import Decimal

User = get_user_model()

class ManualFeexPaySync:
    def __init__(self):
        self.payment_method = PaymentMethod.objects.filter(name__icontains='FeexPay').first()
    
    def find_user_by_phone(self, phone_number):
        """Trouver un utilisateur par son numéro de téléphone"""
        # Nettoyer le numéro
        clean_phone = phone_number.replace('+229', '').replace('+', '').replace(' ', '')
        
        # Mapping manuel des numéros de téléphone connus
        phone_to_user = {
            '2290168737793': 'ana',  # Ana
            '2290196092246': 'ahounsounon',  # Ahounsounon
        }
        
        username = phone_to_user.get(clean_phone)
        if username:
            return User.objects.filter(username=username).first()
        
        # Si pas trouvé dans le mapping, chercher par numéro
        user = User.objects.filter(phone_number__icontains=clean_phone).first()
        if user:
            return user
        
        print(f"⚠️ Utilisateur non trouvé pour {phone_number}")
        return None
    
    def sync_manual_transaction(self, reference, amount, phone, transaction_type='deposit', status='completed'):
        """Synchroniser une transaction manuellement"""
        print(f"\n🔄 Sync: {reference}")
        print(f"   💰 {amount} FCFA - {phone} - {transaction_type}")
        
        # Vérifier si existe déjà
        existing = Transaction.objects.filter(external_reference=reference).first()
        if existing:
            print(f"   ⚠️ Transaction déjà synchronisée")
            return False
        
        # Trouver utilisateur
        user = self.find_user_by_phone(phone)
        if not user:
            return False
        
        print(f"   👤 Utilisateur: {user.username}")
        
        try:
            # Créer transaction
            transaction = Transaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                amount=Decimal(str(amount)),
                currency='FCFA',
                status=status,
                payment_method=self.payment_method,
                external_reference=reference,
                metadata={
                    'phone': phone,
                    'manual_sync': True,
                    'sync_date': datetime.now().isoformat()
                }
            )
            
            # Mettre à jour balance
            if transaction_type == 'deposit' and status == 'completed':
                old_balance = user.balance_fcfa
                user.balance_fcfa += Decimal(str(amount))
                user.save()
                
                print(f"   ✅ Balance: {old_balance} → {user.balance_fcfa} FCFA")
            
            return True
            
        except Exception as e:
            print(f"   💥 Erreur: {e}")
            return False
    
    def sync_ana_transactions(self):
        """Synchroniser spécifiquement les transactions d'Ana"""
        print("🔧 SYNCHRONISATION SPÉCIALE POUR ANA")
        print("=" * 40)
        
        # Transactions d'Ana du dashboard FeexPay
        ana_transactions = [
            {
                'reference': 'BEED6695-561C-4E46-8A7C-849B86EE5B94',
                'amount': 200,
                'phone': '2290168737793',
                'date': '18 novembre 2025 à 12:49'
            },
            {
                'reference': 'BFB7BD77-8F1B-4048-99EC-6C33B1DB94B3',
                'amount': 200,
                'phone': '2290168737793',
                'date': '18 novembre 2025 à 12:39'
            }
        ]
        
        synced_count = 0
        for tx in ana_transactions:
            if self.sync_manual_transaction(
                tx['reference'], 
                tx['amount'], 
                tx['phone']
            ):
                synced_count += 1
        
        print(f"\n🎉 {synced_count}/{len(ana_transactions)} transactions synchronisées pour Ana")
        
        # Vérifier le résultat
        ana = User.objects.filter(username='ana').first()
        if ana:
            print(f"💰 Balance finale d'Ana: {ana.balance_fcfa} FCFA")
    
    def sync_all_from_dashboard(self):
        """Synchroniser toutes les transactions du dashboard"""
        print("🚀 SYNCHRONISATION COMPLÈTE DEPUIS DASHBOARD")
        print("=" * 50)
        
        # Toutes les transactions réussies du dashboard
        dashboard_transactions = [
            # Ana
            {
                'reference': 'BEED6695-561C-4E46-8A7C-849B86EE5B94',
                'amount': 200,
                'phone': '2290168737793',
                'status': 'Succès'
            },
            {
                'reference': 'BFB7BD77-8F1B-4048-99EC-6C33B1DB94B3',
                'amount': 200,
                'phone': '2290168737793',
                'status': 'Succès'
            },
            # Ahounsounon
            {
                'reference': '09ffb7e5-0302-49d1-b197-3c0dee912b75',
                'amount': 200,
                'phone': '2290196092246',
                'status': 'Succès'
            },
            {
                'reference': '1d6efff5-6114-49b1-b43c-2e9f8e655e5b',
                'amount': 499,
                'phone': '2290196092246',
                'status': 'Succès'
            }
        ]
        
        synced_count = 0
        for tx in dashboard_transactions:
            if tx['status'] == 'Succès':
                if self.sync_manual_transaction(
                    tx['reference'], 
                    tx['amount'], 
                    tx['phone']
                ):
                    synced_count += 1
        
        print(f"\n🎉 SYNCHRONISATION TERMINÉE: {synced_count} transactions")
        
        # Résumé des balances
        print("\n💰 BALANCES FINALES:")
        for user in ['ana', 'ahounsounon']:
            user_obj = User.objects.filter(username=user).first()
            if user_obj:
                print(f"   👤 {user}: {user_obj.balance_fcfa} FCFA")

def main():
    """Choisir le type de synchronisation"""
    import sys
    
    sync = ManualFeexPaySync()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'ana':
        sync.sync_ana_transactions()
    else:
        sync.sync_all_from_dashboard()

if __name__ == "__main__":
    main()