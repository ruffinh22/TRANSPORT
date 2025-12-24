# apps/payments/feexpay_sync.py
# ==================================

import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
from django.conf import settings
from django.utils import timezone as django_timezone
from decimal import Decimal

from .models import Transaction

logger = logging.getLogger(__name__)


class FeexPayStatusSync:
    """Service de synchronisation des statuts FeexPay en temps réel."""
    
    def __init__(self):
        self.api_key = settings.FEEXPAY_API_KEY
        self.base_url = settings.FEEXPAY_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_transaction_status(self, feexpay_reference: str) -> Optional[Dict]:
        """
        Récupérer le statut d'une transaction depuis l'API FeexPay.
        
        Args:
            feexpay_reference: Référence de la transaction FeexPay
            
        Returns:
            Dict contenant les données de la transaction ou None si erreur
        """
        url = f"{self.base_url}/api/transactions/public/single/status/{feexpay_reference}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Statut FeexPay récupéré: {feexpay_reference} -> {data.get('status')}")
                return data
            elif response.status_code == 404:
                logger.warning(f"⚠️ Transaction FeexPay non trouvée: {feexpay_reference}")
                return None
            else:
                logger.error(f"❌ Erreur API FeexPay {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur de connexion FeexPay: {e}")
            return None
    
    def sync_transaction_status(self, transaction: Transaction) -> bool:
        """
        Synchroniser le statut d'une transaction avec FeexPay.
        
        Args:
            transaction: Instance de Transaction à synchroniser
            
        Returns:
            bool: True si la synchronisation a réussi, False sinon
        """
        if not transaction.external_reference:
            logger.warning(f"⚠️ Pas de référence externe pour transaction {transaction.id}")
            return False
        
        feexpay_data = self.get_transaction_status(transaction.external_reference)
        
        if not feexpay_data:
            return False
        
        return self._update_transaction_from_feexpay_data(transaction, feexpay_data)
    
    def _update_transaction_from_feexpay_data(self, transaction: Transaction, feexpay_data: Dict) -> bool:
        """
        Mettre à jour une transaction locale avec les données FeexPay.
        
        Args:
            transaction: Transaction à mettre à jour
            feexpay_data: Données reçues de l'API FeexPay
            
        Returns:
            bool: True si mise à jour effectuée, False sinon
        """
        try:
            feexpay_status = feexpay_data.get('status', '').upper()
            current_status = transaction.status
            
            # Mapping des statuts FeexPay vers nos statuts
            status_mapping = {
                'SUCCESSFUL': 'completed',
                'FAILED': 'failed',
                'PENDING': 'pending',
                'IN PENDING STATE': 'pending'
            }
            
            new_status = status_mapping.get(feexpay_status, transaction.status)
            
            # Vérifier si une mise à jour est nécessaire
            needs_update = False
            updates = {}
            
            if new_status != current_status:
                updates['status'] = new_status
                needs_update = True
                logger.info(f"📊 Changement de statut: {current_status} -> {new_status}")
            
            # Mettre à jour les métadonnées avec les infos FeexPay
            metadata = transaction.metadata or {}
            feexpay_metadata = {
                'feexpay_sync_date': django_timezone.now().isoformat(),
                'feexpay_status': feexpay_status,
                'feexpay_responsecode': feexpay_data.get('responsecode', ''),
                'feexpay_responsemsg': feexpay_data.get('responsemsg', ''),
                'feexpay_reason': feexpay_data.get('reason', ''),
                'feexpay_phone': feexpay_data.get('phoneNumber', ''),
                'feexpay_date': feexpay_data.get('date', ''),
                'feexpay_type': feexpay_data.get('type', ''),
            }
            
            # Vérifier si les métadonnées ont changé
            if metadata.get('feexpay_sync') != feexpay_metadata:
                metadata['feexpay_sync'] = feexpay_metadata
                updates['metadata'] = metadata
                needs_update = True
            
            if needs_update:
                updates['updated_at'] = django_timezone.now()
                
                # Effectuer la mise à jour
                for field, value in updates.items():
                    setattr(transaction, field, value)
                
                transaction.save()
                
                logger.info(f"✅ Transaction {transaction.id} mise à jour depuis FeexPay")
                
                # Si la transaction est maintenant complétée, traiter le succès
                if new_status == 'completed' and current_status != 'completed':
                    self._handle_successful_transaction(transaction)
                
                return True
            else:
                logger.debug(f"ℹ️ Aucune mise à jour nécessaire pour transaction {transaction.id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour de transaction {transaction.id}: {e}")
            return False
    
    def _handle_successful_transaction(self, transaction: Transaction):
        """Traiter une transaction qui vient d'être confirmée comme réussie."""
        try:
            # Créditer le solde de l'utilisateur
            from apps.accounts.models import UserBalance
            
            user_balance, created = UserBalance.objects.get_or_create(
                user=transaction.user,
                defaults={'balance': Decimal('0')}
            )
            
            old_balance = user_balance.balance
            user_balance.balance += transaction.net_amount
            user_balance.save()
            
            logger.info(f"💰 Solde mis à jour: {old_balance} -> {user_balance.balance} (+{transaction.net_amount})")
            
            # Logging de l'activité
            from apps.core.utils import log_user_activity
            log_user_activity(
                user=transaction.user,
                activity_type='deposit_completed',
                description=f'Dépôt FeexPay complété: {transaction.amount} {transaction.currency}',
                metadata={
                    'transaction_id': str(transaction.id),
                    'feexpay_reference': transaction.external_reference,
                    'amount': str(transaction.amount),
                    'net_amount': str(transaction.net_amount),
                    'old_balance': str(old_balance),
                    'new_balance': str(user_balance.balance),
                    'sync_method': 'feexpay_api'
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la transaction réussie {transaction.id}: {e}")
    
    def sync_pending_transactions(self) -> Dict[str, int]:
        """
        Synchroniser toutes les transactions en attente avec FeexPay.
        
        Returns:
            Dict avec les statistiques de synchronisation
        """
        pending_transactions = Transaction.objects.filter(
            status='pending',
            transaction_type='deposit',
            external_reference__isnull=False
        ).exclude(external_reference='')
        
        stats = {
            'total': pending_transactions.count(),
            'updated': 0,
            'completed': 0,
            'failed': 0,
            'errors': 0
        }
        
        logger.info(f"🔄 Synchronisation de {stats['total']} transactions en attente")
        
        for transaction in pending_transactions:
            try:
                if self.sync_transaction_status(transaction):
                    stats['updated'] += 1
                    
                    # Recharger la transaction pour avoir le statut à jour
                    transaction.refresh_from_db()
                    
                    if transaction.status == 'completed':
                        stats['completed'] += 1
                    elif transaction.status == 'failed':
                        stats['failed'] += 1
                        
            except Exception as e:
                logger.error(f"❌ Erreur sync transaction {transaction.id}: {e}")
                stats['errors'] += 1
        
        logger.info(f"✅ Synchronisation terminée: {stats}")
        return stats
    
    def sync_transaction_by_reference(self, feexpay_reference: str) -> Optional[Transaction]:
        """
        Synchroniser une transaction spécifique par sa référence FeexPay.
        
        Args:
            feexpay_reference: Référence FeexPay de la transaction
            
        Returns:
            Transaction mise à jour ou None si non trouvée
        """
        try:
            transaction = Transaction.objects.get(external_reference=feexpay_reference)
            
            if self.sync_transaction_status(transaction):
                transaction.refresh_from_db()
                return transaction
            
            return None
            
        except Transaction.DoesNotExist:
            logger.warning(f"⚠️ Transaction avec référence {feexpay_reference} non trouvée en base")
            return None


# Instance globale du service
feexpay_sync = FeexPayStatusSync()