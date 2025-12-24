"""
Service de monitoring automatique des transactions FeexPay
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from .models import Transaction

User = get_user_model()
logger = logging.getLogger(__name__)

class TransactionMonitorService:
    """
    Service pour le monitoring automatique des transactions
    """
    
    @staticmethod
    def auto_complete_pending_transactions(user=None, max_age_minutes=60):
        """
        Complète automatiquement les transactions pending anciennes
        
        Args:
            user: Utilisateur spécifique (optionnel)
            max_age_minutes: Âge maximum des transactions à traiter (défaut: 60 minutes)
        
        Returns:
            dict: Résultats de l'opération
        """
        try:
            cutoff_time = timezone.now() - timedelta(minutes=max_age_minutes)
            
            # Filtrer les transactions pending anciennes
            query = Transaction.objects.filter(
                status='pending',
                transaction_type='deposit',
                created_at__lt=cutoff_time
            )
            
            if user:
                query = query.filter(user=user)
            
            pending_transactions = query.order_by('-created_at')
            
            completed_count = 0
            updated_balances = {}
            
            for txn in pending_transactions:
                try:
                    with db_transaction.atomic():
                        # Marquer la transaction comme complétée
                        txn.status = 'completed'
                        txn.completed_at = timezone.now()
                        txn.processed_at = timezone.now()
                        
                        # Ajouter métadonnée d'auto-completion
                        metadata = txn.metadata or {}
                        metadata.update({
                            'auto_completed': True,
                            'auto_completed_at': timezone.now().isoformat(),
                            'auto_completion_reason': f'Transaction pending depuis plus de {max_age_minutes} minutes'
                        })
                        txn.metadata = metadata
                        txn.save()
                        
                        # Mettre à jour le solde utilisateur
                        user_obj = txn.user
                        old_balance = user_obj.balance_fcfa or Decimal('0')
                        new_balance = old_balance + txn.amount
                        user_obj.balance_fcfa = new_balance
                        user_obj.save()
                        
                        updated_balances[user_obj.username] = {
                            'old_balance': float(old_balance),
                            'new_balance': float(new_balance),
                            'amount_added': float(txn.amount)
                        }
                        
                        completed_count += 1
                        
                        logger.info(
                            f"✅ Auto-complété transaction {txn.transaction_id} "
                            f"pour {user_obj.username}: +{txn.amount} FCFA"
                        )
                        
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'auto-completion de {txn.transaction_id}: {e}")
                    continue
            
            return {
                'success': True,
                'completed_count': completed_count,
                'updated_balances': updated_balances,
                'processed_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'auto-completion des transactions: {e}")
            return {
                'success': False,
                'error': str(e),
                'completed_count': 0
            }
    
    @staticmethod
    def get_user_pending_transactions(user):
        """
        Récupère les transactions pending d'un utilisateur
        """
        try:
            pending_transactions = Transaction.objects.filter(
                user=user,
                status='pending',
                transaction_type='deposit'
            ).order_by('-created_at')
            
            transactions_data = []
            for txn in pending_transactions:
                age = timezone.now() - txn.created_at
                transactions_data.append({
                    'id': str(txn.id),
                    'transaction_id': txn.transaction_id,
                    'amount': float(txn.amount),
                    'currency': txn.currency,
                    'status': txn.status,
                    'created_at': txn.created_at.isoformat(),
                    'age_minutes': int(age.total_seconds() // 60),
                    'external_reference': txn.external_reference,
                })
            
            return {
                'success': True,
                'transactions': transactions_data,
                'total_pending': len(transactions_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des transactions pending: {e}")
            return {
                'success': False,
                'error': str(e),
                'transactions': []
            }