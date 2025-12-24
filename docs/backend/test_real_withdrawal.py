#!/usr/bin/env python3
"""
Script pour tester les retraits FeexPay en mode production
Usage: python test_real_withdrawal.py
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/var/www/html/rhumo1/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.payments.models import FeexPayWithdrawal
from apps.payments.feexpay_payout import FeexPayPayout

def test_real_withdrawal():
    """Test d'un retrait réel FeexPay"""
    
    print("🚀 TEST RETRAIT FEEXPAY RÉEL")
    print("="*50)
    
    # Récupérer l'utilisateur
    User = get_user_model()
    user = User.objects.filter(email='ahounsounon@gmail.com').first()
    
    if not user:
        print("❌ Utilisateur non trouvé")
        return
    
    print(f"👤 Utilisateur: {user.username}")
    print(f"💰 Solde actuel: {user.balance_fcfa} FCFA")
    
    # Paramètres du retrait
    amount = Decimal('100')  # Montant petit pour test
    phone = "0196092246"
    network = "MTN"
    recipient = user.username
    
    if user.balance_fcfa < amount:
        print(f"❌ Solde insuffisant pour retrait de {amount} FCFA")
        return
    
    print(f"\n📱 Retrait de {amount} FCFA vers {phone} ({network})")
    
    # Calculer les frais
    fee_rate = Decimal('0.02')
    fee = max(amount * fee_rate, Decimal('100'))
    total = amount + fee
    
    print(f"💸 Frais: {fee} FCFA")
    print(f"🔢 Total déduit: {total} FCFA")
    
    confirmation = input("\n⚠️  ATTENTION: Ceci effectuera un VRAI retrait d'argent !\n   Confirmer ? (oui/non): ")
    
    if confirmation.lower() != 'oui':
        print("❌ Retrait annulé")
        return
    
    try:
        # Créer la demande de retrait
        withdrawal = FeexPayWithdrawal.objects.create(
            user=user,
            amount=amount,
            phone_number=phone,
            network=network,
            recipient_name=recipient,
            description=f"Test retrait réel - {user.username}",
            fee=fee,
            status='pending'
        )
        
        print(f"\n🆔 ID Retrait: {withdrawal.id}")
        
        # Déduire le solde
        user.balance_fcfa -= total
        user.save()
        
        print(f"💰 Solde déduit temporairement: {user.balance_fcfa} FCFA")
        
        # Initialiser FeexPay
        feexpay = FeexPayPayout()
        
        # Effectuer le VRAI transfert (FORCE PRODUCTION MODE)
        print("\n🚀 EXÉCUTION DU TRANSFERT FEEXPAY...")
        transfer_result = feexpay.send_money(
            amount=amount,
            phone_number=phone,
            network=network,
            recipient_name=recipient,
            description=f"Test retrait réel - {user.username}",
            custom_id=f"withdrawal_{withdrawal.id}",
            force_production=True  # Forcer le mode production
        )
        
        if transfer_result['success']:
            # Retrait réussi
            withdrawal.mark_as_completed(
                transfer_id=transfer_result.get('transfer_id'),
                response_data=transfer_result.get('data', {})
            )
            
            print(f"✅ RETRAIT RÉUSSI!")
            print(f"🆔 Transfer ID: {transfer_result.get('transfer_id')}")
            print(f"💰 Nouveau solde: {user.balance_fcfa} FCFA")
            print(f"📱 Vérifiez votre téléphone {phone}")
            
        else:
            # Retrait échoué - restaurer le solde
            withdrawal.mark_as_failed(
                error_message=transfer_result.get('message', 'Erreur inconnue'),
                response_data=transfer_result
            )
            
            user.balance_fcfa += total
            user.save()
            
            print(f"❌ RETRAIT ÉCHOUÉ!")
            print(f"🔍 Erreur: {transfer_result.get('message')}")
            print(f"💰 Solde restauré: {user.balance_fcfa} FCFA")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        
        # Restaurer le solde en cas d'erreur
        user.balance_fcfa += total
        user.save()
        print(f"💰 Solde restauré: {user.balance_fcfa} FCFA")

if __name__ == '__main__':
    test_real_withdrawal()