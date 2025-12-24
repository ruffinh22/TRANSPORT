# apps/payments/feexpay_views.py
# ===============================

"""
Endpoints API pour l'intégration FeexPay.

3 endpoints principales:
1. POST /api/v1/payments/feexpay/initiate/ - Initier un paiement
2. GET /api/v1/payments/feexpay/{transaction_id}/status/ - Vérifier le statut
3. POST /api/v1/payments/feexpay/webhook/ - Recevoir les callbacks
"""

import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListAPIView

from .models import (
    FeexPayProvider, FeexPayTransaction, FeexPayWebhookSignature, Transaction
)
from .feexpay_serializers import (
    FeexPayProviderSerializer, FeexPayInitiatePaymentSerializer,
    FeexPayTransactionSerializer, FeexPayTransactionDetailSerializer,
    FeexPayStatusSerializer, FeexPayWebhookHandlerSerializer,
    FeexPayPaymentMethodListSerializer, FeexPayRetryTransactionSerializer
)
from .feexpay_client import FeexPayClient, FeexPayAPIError, FeexPayValidationError
from apps.core.utils import get_client_ip
from apps.accounts.permissions import IsVerifiedUser
from apps.core.pagination import StandardResultsSetPagination

logger = logging.getLogger('feexpay')


class FeexPayHealthCheckView(APIView):
    """Vérifier la santé de l'API FeexPay."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Vérifier la connectivité FeexPay."""
        try:
            client = FeexPayClient()
            is_healthy = client.health_check()
            
            return Response({
                'status': 'healthy' if is_healthy else 'unhealthy',
                'api': 'FeexPay',
                'timestamp': timezone.now().isoformat(),
                'message': 'FeexPay API est accessible' if is_healthy else 'FeexPay API n\'est pas accessible'
            })
        except Exception as e:
            logger.error(f"FeexPay health check error: {str(e)}")
            return Response({
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class FeexPayProvidersListView(ListAPIView):
    """Lister les fournisseurs FeexPay disponibles."""
    
    serializer_class = FeexPayProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourner les fournisseurs actifs."""
        queryset = FeexPayProvider.objects.filter(is_active=True)
        
        # Filtrer par code pays si spécifié
        country_code = self.request.query_params.get('country')
        if country_code:
            queryset = queryset.filter(country_code=country_code.upper())
        
        # Filtrer par provider si spécifié
        provider_code = self.request.query_params.get('provider')
        if provider_code:
            queryset = queryset.filter(provider_code=provider_code.lower())
        
        return queryset.order_by('provider_name', 'country_code')


class FeexPayInitiatePaymentView(GenericAPIView):
    """
    Initier un paiement FeexPay.
    
    POST /api/v1/payments/feexpay/initiate/
    
    Body:
    {
        "provider_code": "mtn",
        "amount": "50000",
        "currency": "XOF",
        "recipient_phone": "+221771234567",
        "description": "Dépôt pour jouer"
    }
    """
    
    serializer_class = FeexPayInitiatePaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsVerifiedUser]
    
    def post(self, request, *args, **kwargs):
        """Initier un paiement."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        user = request.user
        
        try:
            # Créer une transaction interne
            with transaction.atomic():
                # Créer la transaction principale
                internal_tx = Transaction.objects.create(
                    user=user,
                    transaction_type='deposit',
                    amount=data['amount'],
                    currency=data['currency'],
                    status='pending',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Récupérer le provider
                try:
                    provider = FeexPayProvider.objects.get(
                        provider_code=data['provider_code']
                    )
                except FeexPayProvider.DoesNotExist:
                    return Response({
                        'error': 'Fournisseur non trouvé',
                        'provider_code': data['provider_code']
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Calculer les frais
                fees_info = provider.calculate_fees(data['amount'])
                fee_amount = fees_info['total_fees']
                gross_amount = fees_info['net_amount']
                
                # Créer la transaction FeexPay
                feexpay_tx = FeexPayTransaction.objects.create(
                    user=user,
                    transaction=internal_tx,
                    provider=provider,
                    internal_transaction_id=internal_tx.transaction_id,
                    amount=data['amount'],
                    currency=data['currency'],
                    payment_method=data.get('payment_method', 'mobile_money'),
                    recipient_phone=data.get('recipient_phone', ''),
                    recipient_email=data.get('recipient_email', ''),
                    recipient_account=data.get('recipient_account', ''),
                    fee_amount=Decimal(str(fee_amount)),
                    gross_amount=Decimal(str(gross_amount)),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Appeler l'API FeexPay
                client = FeexPayClient()
                
                callback_url = data.get('callback_url')
                if not callback_url:
                    # Construire l'URL de callback par défaut
                    callback_url = request.build_absolute_uri('/api/v1/payments/feexpay/webhook/')
                
                feexpay_response = client.initiate_payment(
                    provider_code=data['provider_code'],
                    amount=data['amount'],
                    currency=data['currency'],
                    recipient_phone=data.get('recipient_phone'),
                    recipient_email=data.get('recipient_email'),
                    recipient_account=data.get('recipient_account'),
                    description=data.get('description', f'Dépôt {feexpay_tx.id}'),
                    metadata={'internal_tx_id': str(internal_tx.transaction_id)},
                    customer_id=str(user.id),
                    order_id=str(feexpay_tx.id),
                    callback_url=callback_url
                )
                
                # Mettre à jour la transaction FeexPay
                feexpay_tx.feexpay_response = feexpay_response
                feexpay_tx.status = 'processing'
                feexpay_tx.initiated_at = timezone.now()
                feexpay_tx.payment_reference = feexpay_response.get('reference', '')
                
                # Si FeexPay retourne un ID immédiatement
                if 'transaction_id' in feexpay_response:
                    feexpay_tx.feexpay_transaction_id = feexpay_response['transaction_id']
                
                feexpay_tx.save()
                
                # Mettre à jour la transaction interne
                internal_tx.status = 'processing'
                internal_tx.external_reference = feexpay_tx.feexpay_transaction_id or feexpay_response.get('reference', '')
                internal_tx.fees = Decimal(str(fee_amount))
                internal_tx.net_amount = data['amount']  # Montant net avant frais
                internal_tx.save()
                
                logger.info(
                    f"FeexPay payment initiated: {feexpay_tx.id} - "
                    f"User: {user.id}, Amount: {data['amount']} {data['currency']}"
                )
            
            # Retourner les détails du paiement
            serializer = FeexPayTransactionDetailSerializer(feexpay_tx)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except FeexPayAPIError as e:
            logger.error(f"FeexPay API error: {e.error_code} - {e.message}")
            return Response({
                'error': 'Erreur FeexPay',
                'error_code': e.error_code,
                'details': e.message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Error initiating FeexPay payment: {str(e)}")
            return Response({
                'error': 'Erreur serveur',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeexPayTransactionStatusView(GenericAPIView):
    """
    Vérifier le statut d'une transaction FeexPay.
    
    GET /api/v1/payments/feexpay/{transaction_id}/status/
    """
    
    serializer_class = FeexPayTransactionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, transaction_id, *args, **kwargs):
        """Récupérer le statut d'une transaction."""
        try:
            # Récupérer la transaction
            feexpay_tx = FeexPayTransaction.objects.get(
                internal_transaction_id=transaction_id
            )
            
            # Vérifier les permissions
            if feexpay_tx.user != request.user and not request.user.is_staff:
                return Response({
                    'error': 'Permis refusées'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier le statut auprès de FeexPay si pas complété
            if feexpay_tx.status not in ['successful', 'failed', 'cancelled']:
                try:
                    if feexpay_tx.feexpay_transaction_id:
                        client = FeexPayClient()
                        status_response = client.get_payment_status(
                            feexpay_tx.feexpay_transaction_id
                        )
                        
                        # Mettre à jour si changement
                        current_status = status_response.get('status', '').lower()
                        if current_status == 'successful':
                            feexpay_tx.mark_as_successful(
                                feexpay_tx.feexpay_transaction_id,
                                current_status
                            )
                        elif current_status == 'failed':
                            feexpay_tx.mark_as_failed(
                                status_response.get('error_code', 'UNKNOWN'),
                                status_response.get('error_message', 'Paiement échoué')
                            )
                        
                        feexpay_tx.feexpay_response = status_response
                        feexpay_tx.save()
                
                except FeexPayAPIError as e:
                    logger.warning(f"Error checking FeexPay status: {e.message}")
            
            serializer = self.get_serializer(feexpay_tx)
            return Response(serializer.data)
        
        except FeexPayTransaction.DoesNotExist:
            return Response({
                'error': 'Transaction non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)


class FeexPayWebhookView(APIView):
    """
    Recevoir les webhooks FeexPay.
    
    POST /api/v1/payments/feexpay/webhook/
    
    Headers:
    {
        "X-Webhook-Signature": "hmac_sha256_signature"
    }
    """
    
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        """Traiter un webhook FeexPay."""
        try:
            # Récupérer la signature
            signature = request.META.get('HTTP_X_WEBHOOK_SIGNATURE', '')
            if not signature:
                logger.warning("Webhook reçu sans signature")
                return Response({
                    'error': 'Signature manquante'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Récupérer la charge utile brute
            import json
            payload_raw = request.body.decode('utf-8')
            payload = json.loads(payload_raw)
            
            # Valider la signature
            client = FeexPayClient()
            try:
                client.validate_webhook_signature(payload_raw, signature)
            except Exception as e:
                logger.error(f"Invalid webhook signature: {str(e)}")
                return Response({
                    'error': 'Signature invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Parser la charge utile
            webhook_data = client.parse_webhook_payload(payload)
            
            # Créer l'enregistrement du webhook
            with transaction.atomic():
                # Nettoyer request.META pour éviter la sérialisation de FakePayload en test
                import json
                clean_meta = {}
                for key, value in request.META.items():
                    try:
                        json.dumps(value)  # Tester la sérialisation
                        clean_meta[key] = value
                    except (TypeError, ValueError):
                        # Ignorer les valeurs non-sérialisables (FakePayload, etc.)
                        pass
                
                webhook_sig = FeexPayWebhookSignature.objects.create(
                    webhook_id=payload.get('webhook_id', ''),
                    event_type=webhook_data['event'],
                    payload=payload,
                    signature=signature,
                    headers=clean_meta,  # Utiliser les données nettoyées
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    is_valid=True
                )
                
                # Récupérer la transaction FeexPay
                try:
                    feexpay_tx = FeexPayTransaction.objects.get(
                        feexpay_transaction_id=webhook_data['transaction_id']
                    )
                    webhook_sig.transaction = feexpay_tx
                    webhook_sig.save()
                    
                    # Traiter selon le statut
                    if webhook_data['status'] == 'successful':
                        feexpay_tx.mark_as_successful(
                            webhook_data['transaction_id'],
                            webhook_data['status']
                        )
                        logger.info(f"Payment successful: {feexpay_tx.id}")
                    
                    elif webhook_data['status'] == 'failed':
                        feexpay_tx.mark_as_failed(
                            webhook_data.get('error_code', 'UNKNOWN'),
                            webhook_data.get('error_message', 'Paiement échoué')
                        )
                        logger.warning(f"Payment failed: {feexpay_tx.id}")
                    
                    webhook_sig.mark_as_processed()
                
                except FeexPayTransaction.DoesNotExist:
                    logger.error(f"FeexPay transaction not found: {webhook_data['transaction_id']}")
                    webhook_sig.mark_as_processing_error('Transaction not found')
            
            return Response({
                'status': 'received',
                'webhook_id': webhook_sig.id
            }, status=status.HTTP_200_OK)
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook")
            return Response({
                'error': 'JSON invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Error processing FeexPay webhook: {str(e)}")
            return Response({
                'error': 'Erreur traitement webhook'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeexPayTransactionHistoryView(ListAPIView):
    """Lister l'historique des transactions FeexPay de l'utilisateur."""
    
    serializer_class = FeexPayTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourner les transactions de l'utilisateur."""
        queryset = FeexPayTransaction.objects.filter(
            user=self.request.user
        ).select_related('provider')
        
        # Filtrer par statut si spécifié
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtrer par provider si spécifié
        provider = self.request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(provider__provider_code=provider)
        
        return queryset.order_by('-created_at')


class FeexPayRetryTransactionView(GenericAPIView):
    """Relancer une transaction FeexPay échouée."""
    
    serializer_class = FeexPayRetryTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Relancer une transaction."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        transaction_id = serializer.validated_data['transaction_id']
        
        try:
            feexpay_tx = FeexPayTransaction.objects.get(
                internal_transaction_id=transaction_id
            )
            
            # Vérifier les permissions
            if feexpay_tx.user != request.user and not request.user.is_staff:
                return Response({
                    'error': 'Permis refusées'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier si peut être relancé
            if not feexpay_tx.can_retry():
                return Response({
                    'error': 'Cette transaction ne peut pas être relancée',
                    'current_status': feexpay_tx.status,
                    'retry_count': feexpay_tx.retry_count
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Relancer
            feexpay_tx.retry()
            
            # Réinitier le paiement
            client = FeexPayClient()
            feexpay_response = client.initiate_payment(
                provider_code=feexpay_tx.provider.provider_code,
                amount=feexpay_tx.amount,
                currency=feexpay_tx.currency,
                recipient_phone=feexpay_tx.recipient_phone,
                recipient_email=feexpay_tx.recipient_email,
                recipient_account=feexpay_tx.recipient_account,
                metadata={'internal_tx_id': feexpay_tx.internal_transaction_id}
            )
            
            feexpay_tx.feexpay_response = feexpay_response
            if 'transaction_id' in feexpay_response:
                feexpay_tx.feexpay_transaction_id = feexpay_response['transaction_id']
            feexpay_tx.save()
            
            logger.info(f"FeexPay transaction retried: {feexpay_tx.id} - Attempt: {feexpay_tx.retry_count}")
            
            serializer = FeexPayTransactionDetailSerializer(feexpay_tx)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except FeexPayTransaction.DoesNotExist:
            return Response({
                'error': 'Transaction non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Error retrying FeexPay transaction: {str(e)}")
            return Response({
                'error': 'Erreur relancer transaction',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
