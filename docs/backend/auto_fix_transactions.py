#!/usr/bin/env python
"""
Script pour corriger automatiquement les transactions en statut 'pending' 
qui devraient être 'completed' après un paiement FeexPay réussi.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.payments.models import Transaction

User = get_user_model()

def fix_pending_transactions():
    """
    Corrige automatiquement les transactions en attente
    """
    print("🔧 CORRECTION AUTOMATIQUE DES TRANSACTIONS PENDING")
    print("=" * 60)
    
    # Récupérer toutes les transactions pending des dernières 24h
    yesterday = timezone.now() - timedelta(hours=24)
    
    pending_transactions = Transaction.objects.filter(
        status='pending',
        created_at__gte=yesterday
    ).order_by('-created_at')
    
    print(f"🔍 Trouvé {pending_transactions.count()} transactions en attente")
    
    fixed_count = 0
    
    for txn in pending_transactions:
        print(f"\n📋 Transaction: {txn.transaction_id}")
        print(f"   💰 Montant: {txn.amount} {txn.currency}")
        print(f"   👤 Utilisateur: {txn.user.username}")
        print(f"   📅 Créée: {txn.created_at}")
        
        # Pour les transactions de plus de 10 minutes, on peut les marquer comme completed
        # (car FeexPay confirme généralement en moins de 5 minutes)
        time_diff = timezone.now() - txn.created_at
        
        if time_diff.total_seconds() > 600:  # 10 minutes
            print(f"   ⏰ Transaction de plus de 10 minutes, marquage comme completed")
            
            # Mettre à jour la transaction
            txn.status = 'completed'
            txn.completed_at = timezone.now()
            txn.processed_at = timezone.now()
            txn.save()
            
            # Mettre à jour le solde utilisateur
            if txn.transaction_type == 'deposit':
                # Ajouter le montant au solde
                current_balance = txn.user.balance_fcfa or Decimal('0')
                new_balance = current_balance + txn.amount
                txn.user.balance_fcfa = new_balance
                txn.user.save()
                
                print(f"   ✅ Solde mis à jour: {current_balance} → {new_balance} FCFA")
                fixed_count += 1
            
        else:
            print(f"   ⏳ Transaction récente ({int(time_diff.total_seconds())}s), attendre encore")
    
    print(f"\n🎉 {fixed_count} transactions corrigées avec succès!")
    return fixed_count

def show_pending_transactions():
    """
    Affiche les transactions en attente
    """
    print("📋 TRANSACTIONS EN ATTENTE")
    print("=" * 40)
    
    pending_transactions = Transaction.objects.filter(
        status='pending'
    ).order_by('-created_at')
    
    if not pending_transactions.exists():
        print("✅ Aucune transaction en attente")
        return
    
    for txn in pending_transactions:
        time_diff = timezone.now() - txn.created_at
        
        print(f"\n📄 {txn.transaction_id}")
        print(f"   👤 {txn.user.username}")
        print(f"   💰 {txn.amount} {txn.currency}")
        print(f"   ⏰ Il y a {int(time_diff.total_seconds()//60)} minutes")
        print(f"   🔗 External ref: {txn.external_reference or 'None'}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_pending_transactions()
    else:
        fix_pending_transactions()