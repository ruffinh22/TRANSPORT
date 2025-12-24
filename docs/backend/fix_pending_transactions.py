"""
Script pour corriger automatiquement les transactions en statut "pending" 
qui sont réellement complétées dans FeexPay
"""

import os
import sys
import django

# Configuration Django
sys.path.append('/var/www/html/rhumo1/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from decimal import Decimal
from django.utils import timezone
from apps.payments.models import Transaction
from apps.accounts.models import User
from django.db import transaction as db_transaction

def fix_pending_transactions():
    """
    Corrige les transactions en statut pending qui correspondent à des paiements réels
    """
    print("🔧 CORRECTION DES TRANSACTIONS PENDING")
    print("=" * 50)
    
    # Récupérer toutes les transactions pending
    pending_transactions = Transaction.objects.filter(
        status='pending',
        transaction_type='deposit'
    ).order_by('-created_at')
    
    print(f"🔍 {pending_transactions.count()} transactions pending trouvées")
    
    fixed_count = 0
    
    for txn in pending_transactions:
        print(f"\n📋 Transaction: {txn.transaction_id}")
        print(f"   💰 Montant: {txn.amount} {txn.currency}")
        print(f"   👤 Utilisateur: {txn.user.username}")
        print(f"   📅 Créée: {txn.created_at}")
        
        # Demander confirmation pour chaque transaction
        response = input("   ❓ Marquer comme completed et mettre à jour le solde ? (y/n/q): ").lower()
        
        if response == 'q':
            print("   ⛔ Arrêt du script")
            break
        elif response == 'y':
            with db_transaction.atomic():
                try:
                    # Mettre à jour la transaction
                    txn.status = 'completed'
                    txn.processed_at = timezone.now()
                    txn.completed_at = timezone.now()
                    txn.save()
                    
                    # Mettre à jour le solde utilisateur
                    old_balance = txn.user.balance_fcfa or Decimal('0')
                    new_balance = old_balance + txn.net_amount
                    
                    txn.user.balance_fcfa = new_balance
                    txn.user.save()
                    
                    print(f"   ✅ Transaction mise à jour: pending → completed")
                    print(f"   💳 Solde mis à jour: {old_balance} → {new_balance} FCFA")
                    
                    fixed_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Erreur: {str(e)}")
        else:
            print("   ⏭️ Transaction ignorée")
    
    print(f"\n🎉 {fixed_count} transactions corrigées avec succès!")

def list_pending_transactions():
    """
    Liste toutes les transactions pending sans les modifier
    """
    print("📋 LISTE DES TRANSACTIONS PENDING")
    print("=" * 50)
    
    pending_transactions = Transaction.objects.filter(
        status='pending',
        transaction_type='deposit'
    ).order_by('-created_at')
    
    if not pending_transactions:
        print("✅ Aucune transaction pending trouvée")
        return
    
    print(f"🔍 {pending_transactions.count()} transactions pending trouvées:\n")
    
    for i, txn in enumerate(pending_transactions, 1):
        print(f"{i:2d}. {txn.transaction_id}")
        print(f"     💰 {txn.amount} {txn.currency}")
        print(f"     👤 {txn.user.username} (ID: {txn.user.id})")
        print(f"     📅 {txn.created_at}")
        print()

def fix_specific_transaction(transaction_id):
    """
    Corrige une transaction spécifique par son ID
    """
    try:
        txn = Transaction.objects.get(transaction_id=transaction_id)
        
        print(f"🔍 Transaction trouvée: {txn.transaction_id}")
        print(f"   💰 Montant: {txn.amount} {txn.currency}")
        print(f"   👤 Utilisateur: {txn.user.username}")
        print(f"   📊 Statut actuel: {txn.status}")
        
        if txn.status != 'pending':
            print(f"   ⚠️ Transaction déjà en statut {txn.status}")
            return
        
        with db_transaction.atomic():
            # Mettre à jour la transaction
            txn.status = 'completed'
            txn.processed_at = timezone.now()
            txn.completed_at = timezone.now()
            txn.save()
            
            # Mettre à jour le solde utilisateur
            old_balance = txn.user.balance_fcfa or Decimal('0')
            new_balance = old_balance + txn.net_amount
            
            txn.user.balance_fcfa = new_balance
            txn.user.save()
            
            print(f"   ✅ Transaction mise à jour: pending → completed")
            print(f"   💳 Solde mis à jour: {old_balance} → {new_balance} FCFA")
            
    except Transaction.DoesNotExist:
        print(f"❌ Transaction {transaction_id} non trouvée")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Outil de correction des transactions pending")
    parser.add_argument('--list', action='store_true', help='Lister les transactions pending')
    parser.add_argument('--fix', action='store_true', help='Corriger les transactions pending (interactif)')
    parser.add_argument('--transaction', help='Corriger une transaction spécifique par son ID')
    
    args = parser.parse_args()
    
    if args.list:
        list_pending_transactions()
    elif args.fix:
        fix_pending_transactions()
    elif args.transaction:
        fix_specific_transaction(args.transaction)
    else:
        print("Usage:")
        print("  python fix_pending_transactions.py --list                    # Lister les transactions")
        print("  python fix_pending_transactions.py --fix                     # Corriger interactivement")
        print("  python fix_pending_transactions.py --transaction TXN_ID      # Corriger une transaction spécifique")