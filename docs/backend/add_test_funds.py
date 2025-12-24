#!/usr/bin/env python
"""
Script pour ajouter des fonds de test à un utilisateur
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
sys.path.insert(0, '/home/lidruf/rumo_rush/backend')
django.setup()

from django.contrib.auth import get_user_model
from apps.payments.models import Wallet, Transaction

User = get_user_model()

def add_funds_to_user(username, amount, currency='FCFA'):
    """Ajouter des fonds à un utilisateur"""
    try:
        user = User.objects.get(username=username)
        print(f"✅ Utilisateur trouvé: {user.username}")
        
        # Obtenir ou créer le portefeuille
        wallet, created = Wallet.objects.get_or_create(
            user=user,
            currency=currency,
            defaults={
                'available_balance': Decimal('0.00'),
                'locked_balance': Decimal('0.00'),
            }
        )
        
        old_balance = wallet.available_balance
        wallet.available_balance += Decimal(str(amount))
        wallet.total_deposited += Decimal(str(amount))
        wallet.save()
        
        # Créer une transaction de test
        Transaction.objects.create(
            user=user,
            type='deposit',
            currency=currency,
            amount=Decimal(str(amount)),
            status='completed',
            description=f'Crédit de test: {amount} {currency}',
            wallet=wallet
        )
        
        print(f"💰 Fonds ajoutés avec succès!")
        print(f"   Ancien solde: {old_balance} {currency}")
        print(f"   Nouveau solde: {wallet.available_balance} {currency}")
        print(f"   Montant ajouté: {amount} {currency}")
        
        return True
        
    except User.DoesNotExist:
        print(f"❌ Utilisateur '{username}' non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Ajouter 10000 FCFA à l'utilisateur de test
    username = 'testuser'
    amount = 10000
    currency = 'FCFA'
    
    print(f"\n🎯 Ajout de {amount} {currency} à {username}...\n")
    
    if add_funds_to_user(username, amount, currency):
        print(f"\n✅ Opération réussie!\n")
        sys.exit(0)
    else:
        print(f"\n❌ Opération échouée\n")
        sys.exit(1)
