"""
Vue pour traiter les retraits via FeexPay
Traite les demandes de retrait et effectue les transferts réels
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation
import json
import logging

from .models import WithdrawalRequest, FeexPayWithdrawal
from .feexpay_payout import FeexPayPayout

User = get_user_model()
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_withdrawal(request):
    """
    Traiter une demande de retrait et effectuer le transfert FeexPay
    
    POST /api/v1/payments/withdrawals/process/
    
    Données attendues:
    {
        "amount": 1000,
        "phone_number": "22967123456", 
        "network": "MTN",
        "recipient_name": "Jean Dupont"
    }
    """
    try:
        # Récupérer les données de la requête
        data = request.data
        user = request.user
        
        amount = Decimal(str(data.get('amount', 0)))
        phone_number = data.get('phone_number', '').strip()
        network = data.get('network', '').strip().upper()
        recipient_name = data.get('recipient_name', '').strip()
        description = data.get('description', f'Retrait RUMO RUSH - {user.username}')
        
        logger.info(f"💸 Demande retrait - User: {user.username}, Montant: {amount} FCFA, Tél: {phone_number}, Réseau: {network}")
        
        # Validation des données
        if amount <= 0:
            return Response({
                'error': 'Montant invalide',
                'message': 'Le montant doit être supérieur à 0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Montant minimum selon documentation FeexPay Payout: 50 FCFA
        min_amount = getattr(settings, 'FEEXPAY_MIN_PAYOUT', 50)
        if amount < min_amount:
            return Response({
                'error': 'Montant trop faible', 
                'message': f'Le montant minimum de retrait est de {min_amount} FCFA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Montant maximum selon documentation FeexPay Payout: 100,000 FCFA
        max_amount = getattr(settings, 'FEEXPAY_MAX_PAYOUT', 100000)
        if amount > max_amount:
            return Response({
                'error': 'Montant trop élevé',
                'message': f'Le montant maximum de retrait est de {max_amount:,} FCFA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not phone_number or len(phone_number) < 8:
            return Response({
                'error': 'Numéro invalide',
                'message': 'Veuillez saisir un numéro de téléphone valide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if network not in ['MTN', 'ORANGE', 'MOOV', 'WAVE', 'CELTIIS', 'TOGOCOM', 'FREE']:
            return Response({
                'error': 'Réseau invalide',
                'message': 'Veuillez sélectionner un réseau supporté'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not recipient_name:
            return Response({
                'error': 'Nom manquant',
                'message': 'Veuillez saisir le nom du bénéficiaire'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier le solde utilisateur
        if user.balance_fcfa < amount:
            return Response({
                'error': 'Solde insuffisant',
                'message': f'Votre solde ({user.balance_fcfa} FCFA) est insuffisant pour ce retrait'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Frais de retrait (2% minimum 100 FCFA)
        fee_rate = Decimal('0.02')  # 2%
        fee = max(amount * fee_rate, Decimal('100'))  # Minimum 100 FCFA
        total_deduction = amount + fee
        
        if user.balance_fcfa < total_deduction:
            return Response({
                'error': 'Solde insuffisant pour les frais',
                'message': f'Montant + frais ({total_deduction} FCFA) supérieur à votre solde'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Transaction atomique pour éviter les problèmes de concurrence
        with transaction.atomic():
            # Créer la demande de retrait
            withdrawal = FeexPayWithdrawal.objects.create(
                user=user,
                amount=amount,
                phone_number=phone_number,
                network=network,
                recipient_name=recipient_name,
                description=description,
                fee=fee,
                status='pending'
            )
            
            # En mode production seulement, déduire le montant
            if not settings.DEBUG:
                user.balance_fcfa -= total_deduction
                user.save()
                logger.info(f"💰 Solde déduit (PRODUCTION) - User: {user.username}, Nouveau solde: {user.balance_fcfa} FCFA")
            else:
                logger.info(f"🧪 Mode DEBUG - Solde non déduit (simulation)")
        
        # Initialiser FeexPay Payout
        feexpay = FeexPayPayout()
        
        # Effectuer le transfert
        if settings.DEBUG:
            # Mode développement - simulation
            logger.info("🧪 Mode DEBUG - Simulation du retrait")
            transfer_result = feexpay.simulate_payout(
                amount=amount,
                phone_number=phone_number,
                network=network,
                recipient_name=recipient_name,
                description=description,
                custom_id=f"withdrawal_{withdrawal.id}"
            )
        else:
            # Mode production - transfert réel
            logger.info("🚀 Mode PRODUCTION - Transfert réel FeexPay")
            transfer_result = feexpay.send_money(
                amount=amount,
                phone_number=phone_number,
                network=network,
                recipient_name=recipient_name,
                description=description,
                custom_id=f"withdrawal_{withdrawal.id}"
            )
        
        # Traiter le résultat du transfert
        with transaction.atomic():
            withdrawal.refresh_from_db()
            user.refresh_from_db()
            
            if transfer_result['success']:
                # Récupérer le statut du payout (SUCCESSFUL/FAILED/PENDING)
                payout_status = transfer_result.get('status', 'pending').lower()
                
                # Marquer comme complété seulement si SUCCESSFUL
                if payout_status == 'successful':
                    withdrawal.mark_as_completed(
                        transfer_id=transfer_result.get('transfer_id'),
                        response_data=transfer_result.get('data', {})
                    )
                    logger.info(f"✅ Retrait SUCCESSFUL - ID: {withdrawal.id}, Ref: {transfer_result.get('transfer_id')}")
                    
                elif payout_status == 'pending':
                    # Mettre à jour avec la référence mais garder status pending
                    withdrawal.feexpay_transfer_id = transfer_result.get('transfer_id')
                    withdrawal.status = 'pending'
                    withdrawal.feexpay_response = transfer_result.get('data', {})
                    withdrawal.save()
                    logger.info(f"⏳ Retrait PENDING - ID: {withdrawal.id}, Ref: {transfer_result.get('transfer_id')}")
                    
                    # Programmer une vérification du statut après 5 minutes
                    try:
                        from .tasks import check_pending_payout_status
                        check_pending_payout_status.apply_async(
                            args=[withdrawal.id],
                            countdown=300  # 5 minutes (300 secondes)
                        )
                        logger.info(f"⏰ Vérification programmée dans 5min pour withdrawal {withdrawal.id}")
                    except Exception as task_error:
                        logger.error(f"❌ Erreur programmation task: {task_error}")
                    
                elif payout_status == 'failed':
                    withdrawal.mark_as_failed(
                        error_message='Payout échoué',
                        response_data=transfer_result.get('data', {})
                    )
                    # Restaurer le solde si déjà déduit
                    if not settings.DEBUG:
                        user.balance_fcfa += total_deduction
                        user.save()
                    logger.error(f"❌ Retrait FAILED - ID: {withdrawal.id}")
                
                # En mode production, le montant reste déduit. En mode debug, on simule juste
                if settings.DEBUG:
                    current_balance = user.balance_fcfa
                else:
                    user.refresh_from_db()
                    current_balance = user.balance_fcfa
                
                return Response({
                    'success': True,
                    'status': payout_status,  # SUCCESSFUL/PENDING/FAILED
                    'message': f'Retrait de {amount} FCFA {"effectué" if payout_status == "successful" else "en cours"} vers {phone_number} ({network})',
                    'withdrawal_id': withdrawal.id,
                    'reference': transfer_result.get('transfer_id'),  # Référence FeexPay
                    'fee': str(fee),
                    'new_balance': str(current_balance),
                    'simulation': transfer_result.get('data', {}).get('simulation', settings.DEBUG)
                }, status=status.HTTP_200_OK)
            
            else:
                # Transfert échoué
                withdrawal.mark_as_failed(
                    error_message=transfer_result.get('message', 'Erreur inconnue'),
                    response_data=transfer_result
                )
                
                # Restaurer le solde seulement si déjà déduit (mode production)
                if not settings.DEBUG:
                    user.balance_fcfa += total_deduction
                    user.save()
                
                logger.error(f"❌ Retrait échoué - ID: {withdrawal.id}, Erreur: {transfer_result.get('message')}")
                
                return Response({
                    'error': 'Transfert échoué',
                    'message': transfer_result.get('message', 'Erreur lors du transfert'),
                    'details': transfer_result.get('error'),
                    'withdrawal_id': withdrawal.id
                }, status=status.HTTP_400_BAD_REQUEST)
    
    except InvalidOperation:
        return Response({
            'error': 'Montant invalide',
            'message': 'Format de montant incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"❌ Erreur retrait: {e}")
        return Response({
            'error': 'Erreur interne',
            'message': 'Une erreur est survenue lors du traitement'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def withdrawal_networks(request):
    """
    Retourner la liste des réseaux Mobile Money supportés
    
    GET /api/v1/payments/withdrawals/networks/
    """
    feexpay = FeexPayPayout()
    networks = feexpay.get_supported_networks()
    
    return Response({
        'networks': networks
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def withdrawal_history(request):
    """
    Historique des retraits de l'utilisateur
    
    GET /api/v1/payments/withdrawals/history/
    """
    try:
        withdrawals = FeexPayWithdrawal.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]  # 20 derniers retraits
        
        withdrawal_data = []
        for w in withdrawals:
            withdrawal_data.append({
                'id': w.id,
                'amount': str(w.amount),
                'fee': str(w.fee),
                'phone_number': w.phone_number,
                'network': w.network,
                'recipient_name': w.recipient_name,
                'status': w.status,
                'created_at': w.created_at.isoformat(),
                'feexpay_transfer_id': w.feexpay_transfer_id,
                'error_message': w.error_message
            })
        
        return Response({
            'withdrawals': withdrawal_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"❌ Erreur historique retraits: {e}")
        return Response({
            'error': 'Erreur lors du chargement'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def withdrawal_fees(request):
    """
    Calculer les frais de retrait pour un montant donné
    
    GET /api/v1/payments/withdrawals/fees/?amount=1000
    """
    try:
        amount_str = request.GET.get('amount', '0')
        amount = Decimal(str(amount_str))
        
        if amount <= 0:
            return Response({
                'error': 'Montant invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcul des frais (2% minimum 100 FCFA)
        fee_rate = Decimal('0.02')
        fee = max(amount * fee_rate, Decimal('100'))
        total = amount + fee
        
        return Response({
            'amount': str(amount),
            'fee': str(fee),
            'fee_rate': '2%',
            'total': str(total),
            'minimum_fee': '100'
        }, status=status.HTTP_200_OK)
    
    except InvalidOperation:
        return Response({
            'error': 'Format de montant invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"❌ Erreur calcul frais: {e}")
        return Response({
            'error': 'Erreur calcul'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)