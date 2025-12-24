#!/usr/bin/env python
"""
Script pour vérifier et créer des transactions de test
Usage: python check_transactions.py
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from apps.payments.models import Transaction, PaymentMethod
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

def list_recent_transactions(limit=10):
    """Lister les transactions récentes"""
    print(f"📋 Dernières {limit} transactions:")
    print("-" * 80)
    
    transactions = Transaction.objects.order_by('-created_at')[:limit]
    
    if not transactions.exists():
        print("❌ Aucune transaction trouvée")
        return []
    
    for tx in transactions:
        status_emoji = "✅" if tx.status == 'completed' else "⏳" if tx.status == 'pending' else "❌"
        print(f"{status_emoji} {tx.id}")
        print(f"   User: {tx.user.username} ({tx.user.email})")
        print(f"   Type: {tx.transaction_type} | Amount: {tx.amount} {tx.currency}")
        print(f"   Status: {tx.status} | Created: {tx.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   External Ref: {tx.external_reference}")
        print()
    
    return list(transactions)

def list_users():
    """Lister les utilisateurs"""
    print(f"👥 Utilisateurs disponibles:")
    print("-" * 50)
    
    users = User.objects.all()[:5]
    for user in users:
        print(f"🙍 {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Is Active: {user.is_active}")
        print()
    
    return list(users)

def list_payment_methods():
    """Lister les méthodes de paiement"""
    print(f"💳 Méthodes de paiement:")
    print("-" * 50)
    
    methods = PaymentMethod.objects.filter(is_active=True)
    for method in methods:
        print(f"💰 {method.id}")
        print(f"   Name: {method.name}")
        print(f"   Type: {method.method_type}")
        print(f"   Currencies: {method.supported_currencies}")
        print()
    
    return list(methods)

def create_test_transaction(user_id=None, amount=100):
    """Créer une transaction de test"""
    print(f"🧪 Création d'une transaction de test...")
    
    # Trouver un utilisateur
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            print(f"❌ Utilisateur {user_id} non trouvé")
            return None
    else:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print(f"❌ Aucun utilisateur actif trouvé")
            return None
    
    # Trouver une méthode de paiement
    payment_method = PaymentMethod.objects.filter(is_active=True, method_type='mobile_money').first()
    if not payment_method:
        payment_method = PaymentMethod.objects.filter(is_active=True).first()
    
    if not payment_method:
        print(f"❌ Aucune méthode de paiement trouvée")
        return None
    
    # Créer la transaction
    transaction = Transaction.objects.create(
        user=user,
        transaction_type='deposit',
        amount=Decimal(str(amount)),
        currency='FCFA',
        payment_method=payment_method,
        fees=Decimal('0.00'),
        net_amount=Decimal(str(amount)),
        status='pending',
        metadata={
            'test': True,
            'created_by': 'check_transactions_script',
            'timestamp': datetime.now().isoformat()
        },
        ip_address='127.0.0.1',
        user_agent='Test Script'
    )
    
    print(f"✅ Transaction créée:")
    print(f"   ID: {transaction.id}")
    print(f"   User: {user.username} ({user.email})")
    print(f"   Amount: {transaction.amount} {transaction.currency}")
    print(f"   Status: {transaction.status}")
    print(f"   Method: {payment_method.name}")
    
    return transaction

def create_feexpay_test_data(transaction_id):
    """Générer les données de test FeexPay"""
    feexpay_data = {
        'transaction_id': str(transaction_id),
        'feexpay_reference': str(transaction_id),  # Utiliser l'ID comme référence
        'amount': 100,
        'status': 'completed'
    }
    
    print(f"📋 Données FeexPay pour test:")
    print("-" * 40)
    print(f"transaction_id: {feexpay_data['transaction_id']}")
    print(f"feexpay_reference: {feexpay_data['feexpay_reference']}")
    print(f"amount: {feexpay_data['amount']}")
    print(f"status: {feexpay_data['status']}")
    print()
    
    # Format curl pour test
    import json
    curl_data = json.dumps(feexpay_data)
    
    print(f"🔧 Commande curl pour test:")
    print("-" * 40)
    print(f"curl -X POST http://localhost:8000/api/v1/payments/deposits/confirm/ \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -d '{curl_data}'")
    print()
    
    return feexpay_data

def check_specific_transaction(transaction_id):
    """Vérifier une transaction spécifique"""
    print(f"🔍 Vérification transaction: {transaction_id}")
    print("-" * 60)
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        print(f"✅ Transaction trouvée:")
        print(f"   ID: {transaction.id}")
        print(f"   User: {transaction.user.username} ({transaction.user.email})")
        print(f"   Type: {transaction.transaction_type}")
        print(f"   Amount: {transaction.amount} {transaction.currency}")
        print(f"   Status: {transaction.status}")
        print(f"   External Ref: {transaction.external_reference}")
        print(f"   Created: {transaction.created_at}")
        print(f"   Updated: {transaction.updated_at}")
        print(f"   Metadata: {transaction.metadata}")
        print()
        return transaction
        
    except Transaction.DoesNotExist:
        print(f"❌ Transaction {transaction_id} non trouvée")
        return None

def main():
    print("="*80)
    print("🔍 VÉRIFICATEUR DE TRANSACTIONS")
    print("="*80)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_recent_transactions(20)
            
        elif command == "users":
            list_users()
            
        elif command == "methods":
            list_payment_methods()
            
        elif command == "create":
            user_id = sys.argv[2] if len(sys.argv) > 2 else None
            amount = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            transaction = create_test_transaction(user_id, amount)
            if transaction:
                create_feexpay_test_data(transaction.id)
                
        elif command == "check":
            if len(sys.argv) < 3:
                print("Usage: python check_transactions.py check <transaction_id>")
                return
            transaction_id = sys.argv[2]
            check_specific_transaction(transaction_id)
            
        elif command == "feexpay":
            if len(sys.argv) < 3:
                print("Usage: python check_transactions.py feexpay <transaction_id>")
                return
            transaction_id = sys.argv[2]
            create_feexpay_test_data(transaction_id)
            
        else:
            print_help()
    else:
        # Mode interactif
        print("Mode automatique - Vérification complète\n")
        
        # 1. Lister les transactions récentes
        transactions = list_recent_transactions(5)
        
        # 2. Créer une nouvelle transaction de test si nécessaire
        if len(transactions) == 0:
            print("\n🧪 Création d'une transaction de test...")
            transaction = create_test_transaction()
            if transaction:
                create_feexpay_test_data(transaction.id)
        else:
            # Utiliser la première transaction en attente
            pending_tx = next((tx for tx in transactions if tx.status == 'pending'), None)
            if pending_tx:
                print(f"\n✅ Transaction en attente trouvée: {pending_tx.id}")
                create_feexpay_test_data(pending_tx.id)
            else:
                print(f"\n🧪 Création d'une nouvelle transaction de test...")
                transaction = create_test_transaction()
                if transaction:
                    create_feexpay_test_data(transaction.id)

def print_help():
    print("""
🔍 Vérificateur de Transactions - Commandes:

python check_transactions.py                    # Mode automatique
python check_transactions.py list               # Lister transactions récentes
python check_transactions.py users              # Lister utilisateurs
python check_transactions.py methods            # Lister méthodes paiement
python check_transactions.py create [user_id] [amount]  # Créer transaction test
python check_transactions.py check <id>         # Vérifier transaction
python check_transactions.py feexpay <id>       # Générer données FeexPay

Exemples:
python check_transactions.py create             # Transaction test automatique
python check_transactions.py check 63c7e60c-... # Vérifier transaction spécifique
python check_transactions.py feexpay 63c7e60c-... # Données pour cette transaction
""")

if __name__ == "__main__":
    main()