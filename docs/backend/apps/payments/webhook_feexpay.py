"""
Webhook FeexPay pour synchroniser les paiements avec RUMO RUSH
"""
import json
import logging
import time
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from decimal import Decimal
import hashlib
import hmac
from django.conf import settings
import os

logger = logging.getLogger(__name__)

# Configuration webhook FeexPay
FEEXPAY_WEBHOOK_SECRET = os.getenv('FEEXPAY_WEBHOOK_SECRET', 'rhXMItO8')

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class FeexPayWebhookView(View):
    """
    Webhook FeexPay pour recevoir les notifications de paiement
    
    Payload exemple :
    {
      "reference": "9006cca3-3216-48f7-9087-ba0b4a509f18",
      "order_id": "9006cca3-3216-48f7-9087-ba0b4a509f18", 
      "status": "SUCCESSFUL",
      "amount": 500,
      "callback_info": "",
      "last_name": "",
      "first_name": "ABDIAS ADINSI",
      "email": "lagraceparle98@gmail.com",
      "type": "Paiement",
      "phoneNumber": 2290153037832,
      "date": "2025-11-17T09:31:21.512Z",
      "reseau": "MTN",
      "ref_link": "",
      "description": "Achat de produit",
      "reason": ""
    }
    """
    
    def post(self, request):
        try:
            # Lire le payload
            payload = json.loads(request.body.decode('utf-8'))
            
            logger.info(f"🔔 Webhook FeexPay reçu: {json.dumps(payload, indent=2)}")
            
            # Vérifier la signature (si implémentée côté FeexPay)
            # if not self.verify_signature(request, payload):
            #     logger.warning("⚠️ Signature webhook invalide")
            #     return HttpResponseBadRequest("Signature invalide")
            
            # Extraire les données importantes
            reference = payload.get('reference')
            status = payload.get('status') 
            amount = payload.get('amount')
            phone_number = payload.get('phoneNumber')
            reseau = payload.get('reseau')
            custom_id = payload.get('order_id')  # Notre ID custom si défini
            
            if not reference or not status or not amount:
                logger.error("❌ Données webhook manquantes")
                return HttpResponseBadRequest("Données manquantes")
            
            # Traiter selon le statut
            if status == 'SUCCESSFUL':
                success = self.handle_successful_payment(
                    reference=reference,
                    amount=amount,
                    phone_number=phone_number,
                    reseau=reseau,
                    custom_id=custom_id,
                    payload=payload
                )
                
                if success:
                    logger.info(f"✅ Paiement traité avec succès: {reference}")
                    return JsonResponse({"status": "success", "message": "Paiement traité"})
                else:
                    logger.error(f"❌ Erreur traitement paiement: {reference}")
                    return JsonResponse({"status": "error", "message": "Erreur traitement"}, status=500)
                    
            elif status == 'FAILED':
                self.handle_failed_payment(reference, payload)
                return JsonResponse({"status": "success", "message": "Échec traité"})
                
            else:
                logger.info(f"📋 Statut webhook ignoré: {status}")
                return JsonResponse({"status": "ignored", "message": f"Statut {status} ignoré"})
                
        except json.JSONDecodeError:
            logger.error("❌ JSON webhook invalide")
            return HttpResponseBadRequest("JSON invalide")
            
        except Exception as e:
            logger.error(f"❌ Erreur webhook FeexPay: {e}")
            return JsonResponse({"status": "error", "message": "Erreur serveur"}, status=500)
    
    def handle_successful_payment(self, reference, amount, phone_number, reseau, custom_id, payload):
        """
        Traiter un paiement réussi - avec mise à jour des transactions pending
        """
        try:
            from django.contrib.auth import get_user_model
            from apps.payments.models import Transaction
            from django.db import transaction as db_transaction
            
            User = get_user_model()
            
            # 1. D'abord chercher une transaction pending qui pourrait correspondre
            pending_transaction = None
            
            # Chercher par reference externe directe
            pending_transaction = Transaction.objects.filter(
                external_reference=reference,
                status='pending'
            ).first()
            
            # Si pas trouvé par référence, chercher par montant et statut pending récent (dernières 2h)
            if not pending_transaction:
                from datetime import datetime, timedelta
                two_hours_ago = datetime.now().replace(tzinfo=timezone.now().tzinfo) - timedelta(hours=2)
                
                pending_transaction = Transaction.objects.filter(
                    amount=Decimal(str(amount)),
                    currency='FCFA',
                    type='deposit',
                    status='pending',
                    created_at__gte=two_hours_ago
                ).first()
                
                if pending_transaction:
                    logger.info(f"🔄 Transaction pending trouvée par montant: {pending_transaction.transaction_id}")
            
            # 2. Si transaction pending trouvée, la mettre à jour
            if pending_transaction:
                with db_transaction.atomic():
                    # Mettre à jour la transaction
                    pending_transaction.status = 'completed'
                    pending_transaction.external_reference = reference
                    pending_transaction.processed_at = timezone.now()
                    pending_transaction.completed_at = timezone.now()
                    
                    # Mettre à jour les métadonnées avec les infos FeexPay
                    current_metadata = pending_transaction.metadata or {}
                    current_metadata.update({
                        'feexpay_payload': payload,
                        'phone_number': phone_number,
                        'reseau': reseau,
                        'webhook_updated': True,
                        'updated_at': timezone.now().isoformat()
                    })
                    pending_transaction.metadata = current_metadata
                    pending_transaction.save()
                    
                    # Mettre à jour le solde utilisateur
                    user = pending_transaction.user
                    old_balance = user.balance_fcfa or Decimal('0')
                    new_balance = old_balance + Decimal(str(amount))
                    user.balance_fcfa = new_balance
                    user.save()
                    
                    logger.info(
                        f"✅ Transaction pending mise à jour: {pending_transaction.transaction_id}"
                    )
                    logger.info(
                        f"💰 Solde mis à jour pour {user.username}: "
                        f"{old_balance} + {amount} = {new_balance} FCFA"
                    )
                    
                    return True
            
            # 3. Si pas de transaction pending, suivre l'ancien processus
            # Chercher l'utilisateur par numéro de téléphone
            user = None
            if phone_number:
                # Essayer de trouver l'utilisateur par numéro
                try:
                    # Si vous avez un champ phone dans User
                    user = User.objects.filter(phone=str(phone_number)).first()
                except:
                    pass
                    
                # Ou par email si fourni dans le payload
                email = payload.get('email')
                if not user and email:
                    try:
                        user = User.objects.filter(email=email).first()
                    except:
                        pass
            
            # Si custom_id contient l'ID utilisateur (format: rumo-rush-{timestamp}-{user_id})
            if not user and custom_id:
                try:
                    parts = custom_id.split('-')
                    if len(parts) >= 4 and parts[0] == 'rumo' and parts[1] == 'rush':
                        # Essayer d'extraire l'ID utilisateur si présent
                        pass
                except:
                    pass
            
            # Si pas d'utilisateur trouvé, créer une transaction en attente
            if not user:
                logger.warning(f"⚠️ Utilisateur non trouvé pour le paiement {reference} (phone: {phone_number})")
                
                # Créer une transaction orpheline pour investigation manuelle
                from apps.payments.models import PaymentMethod
                
                # Récupérer une méthode de paiement mobile money pour la transaction
                mobile_method = PaymentMethod.objects.filter(
                    method_type='mobile_money'
                ).first()
                
                Transaction.objects.create(
                    transaction_type='deposit',
                    amount=Decimal(str(amount)),
                    currency='FCFA',
                    status='pending',
                    payment_method=mobile_method,
                    external_reference=reference,
                    metadata={
                        'feexpay_payload': payload,
                        'phone_number': phone_number,
                        'reseau': reseau,
                        'needs_manual_assignment': True
                    }
                )
                
                return True
            
            # Traiter le paiement pour l'utilisateur trouvé
            with db_transaction.atomic():
                # Vérifier si la transaction existe déjà
                existing_transaction = Transaction.objects.filter(
                    external_reference=reference
                ).first()
                
                if existing_transaction:
                    logger.info(f"💡 Transaction déjà traitée: {reference}")
                    return True
                
                # Créer la transaction
                from apps.payments.models import PaymentMethod
                
                # Récupérer la méthode de paiement FeexPay (doit exister)
                feexpay_method = PaymentMethod.objects.filter(
                    method_type='mobile_money',
                    name__icontains='feexpay'
                ).first()
                
                # Si pas trouvé, prendre le premier mobile money
                if not feexpay_method:
                    feexpay_method = PaymentMethod.objects.filter(
                        method_type='mobile_money'
                    ).first()
                
                transaction = Transaction.objects.create(
                    user=user,
                    transaction_type='deposit',
                    amount=Decimal(str(amount)),
                    currency='FCFA',
                    status='completed',
                    payment_method=feexpay_method,
                    external_reference=reference,
                    metadata={
                        'feexpay_payload': payload,
                        'phone_number': phone_number,
                        'reseau': reseau
                    }
                )
                
                # Mettre à jour le solde de l'utilisateur
                old_balance = user.get_balance('FCFA')
                new_balance = user.update_balance('FCFA', Decimal(str(amount)), 'add')
                
                logger.info(
                    f"💰 Solde mis à jour pour {user.username}: "
                    f"{old_balance} + {amount} = {new_balance} FCFA"
                )
                
                # Optionnel : Envoyer notification à l'utilisateur
                # self.send_deposit_notification(user, amount, transaction)
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement paiement réussi: {e}")
            return False
    
    def handle_failed_payment(self, reference, payload):
        """
        Traiter un paiement échoué
        """
        try:
            from apps.payments.models import Transaction
            
            # Marquer la transaction comme échouée si elle existe
            Transaction.objects.filter(
                external_reference=reference
            ).update(
                status='failed',
                metadata=payload
            )
            
            logger.info(f"💔 Paiement marqué comme échoué: {reference}")
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement paiement échoué: {e}")
    
    def verify_signature(self, request, payload):
        """
        Vérifier la signature webhook FeexPay (si implémentée)
        """
        try:
            signature = request.headers.get('X-FeexPay-Signature')
            if not signature:
                return True  # Pas de signature requise pour l'instant
            
            # Calculer la signature attendue
            expected_signature = hmac.new(
                FEEXPAY_WEBHOOK_SECRET.encode('utf-8'),
                json.dumps(payload, sort_keys=True).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification signature: {e}")
            return False


# Vue pour test du webhook (développement uniquement)
@csrf_exempt
@require_http_methods(["POST", "GET"])
def test_feexpay_webhook(request):
    """
    Test du webhook FeexPay avec des données fictives
    """
    try:
        if request.method == 'GET':
            return JsonResponse({
                "message": "Webhook FeexPay test endpoint",
                "url": "/api/v1/payments/webhooks/feexpay/",
                "secret": FEEXPAY_WEBHOOK_SECRET[:4] + "****",
                "status": "ready"
            })
        
        # Traitement POST
        logger.info("🧪 Début test webhook FeexPay")
        
        # Lire le payload
        if request.body:
            payload = json.loads(request.body.decode('utf-8'))
            logger.info(f"📋 Payload reçu: {json.dumps(payload, indent=2)}")
        else:
            payload = {
                "reference": "test-manual-001",
                "status": "SUCCESSFUL", 
                "amount": 500
            }
            logger.info("📋 Payload par défaut utilisé")
        
        # Test simple d'ajout de solde
        reference = payload.get('reference')
        status = payload.get('status')
        amount = payload.get('amount', 0)
        phone = payload.get('phoneNumber')
        email = payload.get('email', 'test@rumorush.com')
        
        logger.info(f"🔍 Traitement: ref={reference}, status={status}, amount={amount}")
        
        if status == 'SUCCESSFUL' and amount > 0:
            # Chercher un utilisateur pour le test
            from django.contrib.auth import get_user_model
            from apps.payments.models import Transaction
            
            User = get_user_model()
            
            # Chercher par email d'abord
            user = None
            if email:
                user = User.objects.filter(email=email).first()
                logger.info(f"👤 Utilisateur trouvé par email: {user}")
            
            # Si pas trouvé, prendre le premier utilisateur actif
            if not user:
                user = User.objects.filter(is_active=True).first()
                logger.info(f"👤 Utilisateur par défaut: {user}")
            
            if user:
                # Récupérer ou créer une méthode de paiement FeexPay
                from apps.payments.models import PaymentMethod
                feexpay_method, created = PaymentMethod.objects.get_or_create(
                    method_type='mobile_money',
                    name='FeexPay Mobile Money',
                    defaults={
                        'supported_currencies': ['FCFA'],
                        'min_deposit': {'FCFA': 100},
                        'max_deposit': {'FCFA': 1000000},
                        'deposit_processing_time': 'Instantané',
                        'is_active': True,
                        'description': 'Paiement mobile money via FeexPay'
                    }
                )
                
                # Créer transaction test
                transaction = Transaction.objects.create(
                    user=user,
                    transaction_type='deposit',
                    amount=amount,
                    currency='FCFA', 
                    status='completed',
                    payment_method=feexpay_method,  # Instance, pas string
                    external_reference=reference,
                    metadata=payload
                )
                
                logger.info(f"✅ Transaction créée: {transaction.id}")
                
                # Mettre à jour solde si modèle existe
                try:
                    old_balance = user.get_balance('FCFA')
                    new_balance = user.update_balance('FCFA', amount, 'add')
                    
                    logger.info(f"💰 Solde mis à jour: {old_balance} + {amount} = {new_balance}")
                    
                    return JsonResponse({
                        "status": "success",
                        "message": "Webhook traité avec succès",
                        "transaction_id": str(transaction.id),
                        "user": user.username,
                        "old_balance": float(old_balance),
                        "new_balance": float(new_balance),
                        "amount_added": amount
                    })
                    
                except Exception as wallet_error:
                    logger.error(f"❌ Erreur balance: {wallet_error}")
                    return JsonResponse({
                        "status": "partial_success", 
                        "message": "Transaction créée mais erreur balance",
                        "transaction_id": str(transaction.id),
                        "error": str(wallet_error)
                    })
            else:
                logger.warning("⚠️ Aucun utilisateur trouvé")
                return JsonResponse({
                    "status": "error",
                    "message": "Aucun utilisateur disponible pour le test"
                }, status=400)
        
        else:
            return JsonResponse({
                "status": "ignored",
                "message": f"Status {status} ou amount {amount} invalide"
            })
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON invalide: {e}")
        return JsonResponse({
            "status": "error",
            "message": "JSON invalide",
            "error": str(e)
        }, status=400)
        
    except Exception as e:
        logger.error(f"❌ Erreur webhook test: {e}", exc_info=True)
        return JsonResponse({
            "status": "error",
            "message": "Erreur serveur",
            "error": str(e)
        }, status=500)