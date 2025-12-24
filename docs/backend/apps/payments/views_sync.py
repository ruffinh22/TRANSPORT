"""
Views pour la synchronisation des paiements FeexPay
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from django.db import models
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Transaction
from .transaction_monitor import TransactionMonitorService
from .feexpay_sync import feexpay_sync

User = get_user_model()
logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_status(request):
    """
    Endpoint pour vérifier le statut de synchronisation des transactions FeexPay
    """
    try:
        user = request.user
        
        # Récupérer les transactions des 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        transactions = Transaction.objects.filter(
            user=user,
            created_at__gte=thirty_days_ago,
            gateway='feexpay'
        ).order_by('-created_at')
        
        # Calculer les statistiques
        total_deposits = transactions.filter(type='deposit', status='completed').count()
        total_amount = sum(
            t.amount for t in transactions 
            if t.type == 'deposit' and t.status == 'completed'
        )
        
        # Solde actuel de l'utilisateur
        current_balance = user.balance_fcfa
        
        # Construire la réponse
        transaction_data = []
        for txn in transactions:
            transaction_data.append({
                'id': str(txn.id),
                'type': txn.type,
                'amount': float(txn.amount),
                'status': txn.status,
                'feexpay_reference': txn.feexpay_reference,
                'created_at': txn.created_at.isoformat(),
                'updated_at': txn.updated_at.isoformat() if txn.updated_at else None,
            })
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'balance_fcfa': float(current_balance) if current_balance else 0.0
            },
            'sync_status': {
                'total_transactions': transactions.count(),
                'total_deposits': total_deposits,
                'total_deposit_amount': float(total_amount),
                'last_sync': timezone.now().isoformat(),
                'period': '30 days'
            },
            'transactions': transaction_data
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du sync: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([])  # Aucune permission requise
def check_pending_transactions(request):
    """
    Endpoint public pour vérifier les transactions pending d'un utilisateur spécifique
    Utilise l'ID utilisateur passé en paramètre
    """
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'error': 'user_id requis'
            }, status=400)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=404)
        
        # Récupérer les transactions pending des dernières 2 heures
        two_hours_ago = timezone.now() - timedelta(hours=2)
        
        pending_transactions = Transaction.objects.filter(
            user=user,
            status='pending',
            transaction_type='deposit',
            created_at__gte=two_hours_ago
        ).order_by('-created_at')
        
        transactions_data = []
        for txn in pending_transactions:
            time_diff = timezone.now() - txn.created_at
            transactions_data.append({
                'id': str(txn.id),
                'transaction_id': txn.transaction_id,
                'amount': float(txn.amount),
                'currency': txn.currency,
                'created_at': txn.created_at.isoformat(),
                'minutes_elapsed': int(time_diff.total_seconds() // 60),
                'should_complete': time_diff.total_seconds() > 300  # Plus de 5 minutes
            })
        
        return Response({
            'success': True,
            'user_id': user_id,
            'username': user.username,
            'pending_transactions': transactions_data,
            'total_pending': len(transactions_data),
            'check_time': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des pending: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([])  # Aucune permission requise
def auto_complete_pending(request):
    """
    Endpoint pour auto-compléter les transactions pending anciennes
    Accepte soit user_id, soit username+password pour authentication
    """
    try:
        user = None
        
        # Vérifier si username et password sont fournis pour authentication
        username = request.data.get('username')
        password = request.data.get('password')
        user_id = request.data.get('user_id')
        
        if username and password:
            # Authentification par username/password
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if not user:
                return Response({
                    'success': False,
                    'error': 'Identifiants invalides'
                }, status=401)
        elif user_id:
            # Utilisation directe du user_id
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Utilisateur non trouvé'
                }, status=404)
        else:
            return Response({
                'success': False,
                'error': 'user_id ou username+password requis'
            }, status=400)
        
        # Récupérer les transactions pending de plus de 5 minutes
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        
        old_pending_transactions = Transaction.objects.filter(
            user=user,
            status='pending',
            transaction_type='deposit',
            created_at__lt=five_minutes_ago
        )
        
        completed_count = 0
        total_amount = 0
        
        with db_transaction.atomic():
            for txn in old_pending_transactions:
                # Marquer comme completed
                txn.status = 'completed'
                txn.completed_at = timezone.now()
                txn.processed_at = timezone.now()
                
                # Ajouter metadata d'auto-completion
                metadata = txn.metadata or {}
                metadata['auto_completed'] = True
                metadata['auto_completed_at'] = timezone.now().isoformat()
                txn.metadata = metadata
                txn.save()
                
                # Mettre à jour le solde utilisateur
                current_balance = user.balance_fcfa or models.DecimalField().to_python(0)
                new_balance = current_balance + txn.amount
                user.balance_fcfa = new_balance
                user.save()
                
                completed_count += 1
                total_amount += float(txn.amount)
                
                logger.info(f"✅ Auto-completed transaction {txn.transaction_id} pour {user.username}")
        
        return Response({
            'success': True,
            'user_id': user_id,
            'username': user.username,
            'completed_count': completed_count,
            'total_amount': total_amount,
            'new_balance': float(user.balance_fcfa or 0),
            'completed_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'auto-completion: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def force_sync(request):
    """
    Endpoint pour forcer la synchronisation des transactions FeexPay pour un utilisateur
    """
    try:
        user = request.user
        
        # Pour les tests, on peut synchroniser manuellement
        # En production, ceci devrait être limité aux admins
        
        # Récupérer les transactions récentes
        recent_transactions = Transaction.objects.filter(
            user=user,
            gateway='feexpay',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')
        
        sync_results = []
        for txn in recent_transactions:
            if txn.status == 'completed':
                sync_results.append({
                    'transaction_id': str(txn.id),
                    'amount': float(txn.amount),
                    'status': 'already_synced',
                    'message': 'Transaction déjà synchronisée'
                })
            else:
                # Pour les transactions non complétées, on peut essayer de les mettre à jour
                sync_results.append({
                    'transaction_id': str(txn.id),
                    'amount': float(txn.amount),
                    'status': 'needs_manual_check',
                    'message': 'Transaction nécessite une vérification manuelle'
                })
        
        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'sync_results': sync_results,
            'synced_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation forcée: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def balance_audit(request):
    """
    Endpoint pour auditer le solde d'un utilisateur
    """
    try:
        user = request.user
        
        # Calculer le solde basé sur les transactions
        deposits = Transaction.objects.filter(
            user=user,
            type='deposit',
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        withdrawals = Transaction.objects.filter(
            user=user,
            type='withdrawal',
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        # Solde calculé
        calculated_balance = deposits - withdrawals
        
        # Solde actuel en base
        current_balance = user.balance_fcfa or Decimal('0')
        
        # Différence
        difference = current_balance - calculated_balance
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'phone': user.phone
            },
            'audit': {
                'current_balance': float(current_balance),
                'calculated_balance': float(calculated_balance),
                'difference': float(difference),
                'total_deposits': float(deposits),
                'total_withdrawals': float(withdrawals),
                'is_synchronized': abs(difference) < 0.01,  # Tolérance de 1 centime
                'audit_date': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'audit du solde: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def auto_complete_transactions(request):
    """
    Endpoint pour auto-compléter les transactions pending anciennes de l'utilisateur connecté
    """
    try:
        user = request.user
        
        # Auto-compléter les transactions pending de plus de 10 minutes
        result = TransactionMonitorService.auto_complete_pending_transactions(
            user=user, 
            max_age_minutes=10
        )
        
        return JsonResponse({
            'success': result['success'],
            'completed_count': result['completed_count'],
            'updated_balances': result.get('updated_balances', {}),
            'user_id': user.id,
            'username': user.username,
            'processed_at': result.get('processed_at')
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'auto-completion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required  
def pending_transactions_status(request):
    """
    Endpoint pour vérifier le statut des transactions pending de l'utilisateur
    """
    try:
        user = request.user
        
        # Récupérer les transactions pending
        result = TransactionMonitorService.get_user_pending_transactions(user)
        
        # Auto-compléter si nécessaire les transactions anciennes
        auto_complete_result = TransactionMonitorService.auto_complete_pending_transactions(
            user=user,
            max_age_minutes=10
        )
        
        return JsonResponse({
            'success': True,
            'pending_transactions': result.get('transactions', []),
            'total_pending': result.get('total_pending', 0),
            'auto_completed': auto_complete_result.get('completed_count', 0),
            'user': {
                'id': user.id,
                'username': user.username,
                'balance_fcfa': float(user.balance_fcfa or 0)
            },
            'checked_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([])  # Pas d'auth requise pour sync automatique
def feexpay_sync_all(request):
    """
    Synchroniser toutes les transactions en attente avec l'API FeexPay.
    """
    try:
        stats = feexpay_sync.sync_pending_transactions()
        
        return JsonResponse({
            'success': True,
            'message': f'Synchronisation FeexPay terminée',
            'stats': stats,
            'sync_time': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation FeexPay: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([])  # Pas d'auth requise pour sync par référence
def feexpay_sync_by_reference(request):
    """
    Synchroniser une transaction spécifique par sa référence FeexPay.
    """
    try:
        feexpay_reference = request.data.get('reference')
        
        if not feexpay_reference:
            return JsonResponse({
                'success': False,
                'error': 'Référence FeexPay manquante'
            }, status=400)
        
        transaction = feexpay_sync.sync_transaction_by_reference(feexpay_reference)
        
        if transaction:
            return JsonResponse({
                'success': True,
                'message': f'Transaction synchronisée avec succès',
                'transaction': {
                    'id': str(transaction.id),
                    'status': transaction.status,
                    'amount': float(transaction.amount),
                    'external_reference': transaction.external_reference
                },
                'sync_time': timezone.now().isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Transaction non trouvée ou synchronisation échouée'
            }, status=404)
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation FeexPay par référence: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([])  # Pas d'auth requise
def feexpay_check_status(request, feexpay_reference):
    """
    Vérifier le statut d'une transaction directement via l'API FeexPay.
    """
    try:
        feexpay_data = feexpay_sync.get_transaction_status(feexpay_reference)
        
        if feexpay_data:
            # Essayer de trouver la transaction locale correspondante
            local_transaction = None
            try:
                local_transaction = Transaction.objects.get(external_reference=feexpay_reference)
            except Transaction.DoesNotExist:
                pass
            
            response_data = {
                'success': True,
                'feexpay_data': feexpay_data,
                'feexpay_reference': feexpay_reference,
                'check_time': timezone.now().isoformat()
            }
            
            if local_transaction:
                response_data['local_transaction'] = {
                    'id': str(local_transaction.id),
                    'status': local_transaction.status,
                    'amount': float(local_transaction.amount),
                    'user_email': local_transaction.user.email
                }
            
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Transaction non trouvée sur FeexPay'
            }, status=404)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification FeexPay: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)