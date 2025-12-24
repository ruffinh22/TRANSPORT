#!/usr/bin/env python
"""
Script de test pour simuler les retours FeexPay
Usage: python test_feexpay_deposit.py
"""

import os
import sys
import json
import requests
from decimal import Decimal

# Configuration
DJANGO_SETTINGS_MODULE = 'rumo_rush.settings.development'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)

# Setup Django
import django
django.setup()

from apps.payments.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()

class FeexPayDepositTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def authenticate(self, username="admin", password="admin"):
        """S'authentifier pour obtenir un token"""
        print(f"🔐 Authentification...")
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/login/", {
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            if token:
                self.session.headers.update({
                    'Authorization': f'Bearer {token}'
                })
                print(f"✅ Authentifié avec succès")
                return True
        
        print(f"❌ Échec authentification: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    def create_test_transaction(self, amount=100):
        """Créer une transaction de test"""
        print(f"\n💰 Création d'une transaction de test ({amount} FCFA)...")
        
        # Données de dépôt
        deposit_data = {
            'amount': str(amount),
            'currency': 'FCFA',
            'payment_method_id': '178e4d3f-134b-4671-afd4-fac2e4aa4c2b',  # FeexPay
            'return_url': 'http://localhost:3000/deposits/success',
            'metadata': {
                'test': True,
                'source': 'feexpay_test_script'
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/payments/deposits/create/", 
            json=deposit_data
        )
        
        if response.status_code == 201:
            data = response.json()
            transaction = data.get('transaction', {})
            transaction_id = transaction.get('id')
            
            print(f"✅ Transaction créée:")
            print(f"  ID: {transaction_id}")
            print(f"  Montant: {transaction.get('amount')} {transaction.get('currency')}")
            print(f"  Status: {transaction.get('status')}")
            
            return transaction_id
        else:
            print(f"❌ Échec création transaction: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def confirm_feexpay_deposit(self, transaction_id, feexpay_data=None):
        """Confirmer un dépôt avec les données FeexPay"""
        print(f"\n🔔 Confirmation dépôt FeexPay...")
        
        # Données par défaut si non fournies
        if not feexpay_data:
            feexpay_data = {
                'transaction_id': transaction_id,
                'feexpay_reference': transaction_id,  # Utiliser l'ID comme référence
                'amount': 100,
                'status': 'completed'
            }
        
        print(f"📋 Données FeexPay:")
        print(f"  Transaction ID: {feexpay_data['transaction_id']}")
        print(f"  FeexPay Reference: {feexpay_data['feexpay_reference']}")
        print(f"  Amount: {feexpay_data['amount']}")
        print(f"  Status: {feexpay_data['status']}")
        
        response = self.session.post(
            f"{self.base_url}/api/v1/payments/deposits/confirm/",
            json=feexpay_data
        )
        
        print(f"\n📊 Réponse confirmation:")
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            if response.status_code == 200 and response_data.get('success'):
                print(f"✅ Dépôt confirmé avec succès!")
                return response_data
            else:
                print(f"❌ Échec confirmation dépôt")
                return None
                
        except json.JSONDecodeError:
            print(f"Response Text: {response.text}")
            return None
    
    def check_transaction_status(self, transaction_id):
        """Vérifier le statut final de la transaction"""
        print(f"\n🔍 Vérification statut transaction...")
        
        response = self.session.get(
            f"{self.base_url}/api/v1/payments/transactions/{transaction_id}/"
        )
        
        if response.status_code == 200:
            transaction = response.json()
            print(f"✅ Transaction trouvée:")
            print(f"  ID: {transaction.get('id')}")
            print(f"  Status: {transaction.get('status')}")
            print(f"  Amount: {transaction.get('amount')} {transaction.get('currency')}")
            print(f"  External Reference: {transaction.get('external_reference')}")
            print(f"  Completed At: {transaction.get('completed_at')}")
            print(f"  Metadata: {json.dumps(transaction.get('metadata', {}), indent=2)}")
            
            return transaction
        else:
            print(f"❌ Erreur vérification: {response.status_code}")
            return None
    
    def check_user_balance(self):
        """Vérifier le solde de l'utilisateur"""
        print(f"\n💰 Vérification solde utilisateur...")
        
        response = self.session.get(f"{self.base_url}/api/v1/profile/balance/")
        
        if response.status_code == 200:
            balance_data = response.json()
            print(f"✅ Solde actuel:")
            for currency, amount in balance_data.items():
                print(f"  {currency}: {amount}")
            return balance_data
        else:
            print(f"❌ Erreur récupération solde: {response.status_code}")
            return None
    
    def run_full_test(self, amount=100):
        """Exécuter un test complet de dépôt FeexPay"""
        print("="*80)
        print("🧪 TEST COMPLET DÉPÔT FEEXPAY")
        print("="*80)
        
        # 1. Authentification
        if not self.authenticate():
            return False
        
        # 2. Vérifier solde initial
        print(f"\n📊 SOLDE INITIAL:")
        initial_balance = self.check_user_balance()
        
        # 3. Créer transaction
        transaction_id = self.create_test_transaction(amount)
        if not transaction_id:
            return False
        
        # 4. Confirmer avec données FeexPay
        feexpay_data = {
            'transaction_id': transaction_id,
            'feexpay_reference': f"FEEXPAY_{transaction_id}",
            'amount': amount,
            'status': 'completed'
        }
        
        confirm_result = self.confirm_feexpay_deposit(transaction_id, feexpay_data)
        if not confirm_result:
            return False
        
        # 5. Vérifier statut final
        final_transaction = self.check_transaction_status(transaction_id)
        
        # 6. Vérifier solde final
        print(f"\n📊 SOLDE FINAL:")
        final_balance = self.check_user_balance()
        
        # 7. Résumé
        print(f"\n📋 RÉSUMÉ DU TEST:")
        print("-"*40)
        print(f"✅ Transaction créée: {transaction_id}")
        print(f"✅ FeexPay Reference: {feexpay_data['feexpay_reference']}")
        print(f"✅ Statut final: {final_transaction.get('status') if final_transaction else 'ERREUR'}")
        
        if initial_balance and final_balance:
            for currency in initial_balance:
                initial = Decimal(str(initial_balance.get(currency, 0)))
                final = Decimal(str(final_balance.get(currency, 0)))
                difference = final - initial
                print(f"💰 {currency}: {initial} → {final} (Δ: {difference})")
        
        print("="*80)
        
        return True

def main():
    tester = FeexPayDepositTester()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            amount = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            tester.run_full_test(amount)
            
        elif command == "create":
            if tester.authenticate():
                amount = int(sys.argv[2]) if len(sys.argv) > 2 else 100
                transaction_id = tester.create_test_transaction(amount)
                print(f"Transaction ID: {transaction_id}")
                
        elif command == "confirm":
            if len(sys.argv) < 3:
                print("Usage: python test_feexpay_deposit.py confirm <transaction_id> [amount]")
                return
                
            transaction_id = sys.argv[2]
            amount = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            
            if tester.authenticate():
                feexpay_data = {
                    'transaction_id': transaction_id,
                    'feexpay_reference': f"FEEXPAY_{transaction_id}",
                    'amount': amount,
                    'status': 'completed'
                }
                tester.confirm_feexpay_deposit(transaction_id, feexpay_data)
                
        elif command == "balance":
            if tester.authenticate():
                tester.check_user_balance()
                
        else:
            print_help()
    else:
        # Mode interactif
        tester.run_full_test()

def print_help():
    print("""
🧪 Test FeexPay Deposit - Commandes:

python test_feexpay_deposit.py                    # Test complet interactif
python test_feexpay_deposit.py test [amount]      # Test complet avec montant
python test_feexpay_deposit.py create [amount]    # Créer transaction seulement
python test_feexpay_deposit.py confirm <id> [amt] # Confirmer transaction
python test_feexpay_deposit.py balance            # Vérifier solde

Exemples:
python test_feexpay_deposit.py test 500          # Test avec 500 FCFA
python test_feexpay_deposit.py confirm abc-123 500  # Confirmer transaction abc-123
""")

if __name__ == "__main__":
    main()