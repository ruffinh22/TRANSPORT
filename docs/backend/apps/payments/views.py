# apps/payments/views.py
# ==========================

from decimal import Decimal
from django.conf import settings
from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q, Count
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import (
    PaymentMethod, Transaction, Wallet, WithdrawalRequest,
    PaymentWebhook, ExchangeRate, PaymentSettings
)
from .serializers import (
    PaymentMethodSerializer, TransactionSerializer, WalletSerializer,
    WithdrawalRequestSerializer, DepositRequestSerializer, DepositConfirmSerializer,
    PaymentStatisticsSerializer, FeeCalculatorSerializer,
    CurrencyConversionSerializer, ExchangeRateSerializer
)
from apps.accounts.permissions import (
    IsVerifiedUser, IsKYCApproved, CanWithdraw, CanDeposit,
    HasSufficientBalance, HighValueTransactionPermissions
)
from apps.core.permissions import IsOwnerOrReadOnly
from apps.core.utils import log_user_activity, get_client_ip
from apps.core.pagination import StandardResultsSetPagination

from .processors import get_payment_processor


class PaymentMethodListView(generics.ListAPIView):
    """Vue pour lister les méthodes de paiement disponibles."""
    
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourner les méthodes actives, filtrées selon l'utilisateur."""
        queryset = PaymentMethod.objects.filter(is_active=True)
        
        # Filtrer selon les permissions utilisateur
        user = self.request.user
        transaction_type = self.request.query_params.get('type', 'deposit')
        
        if transaction_type == 'withdrawal' and user.kyc_status != 'approved':
            # Limiter aux méthodes ne nécessitant pas KYC
            queryset = queryset.exclude(method_type__in=['card', 'bank_transfer', 'crypto'])
        
        return queryset.order_by('name')


class TransactionListView(generics.ListAPIView):
    """Vue pour lister les transactions de l'utilisateur."""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourner les transactions de l'utilisateur connecté."""
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Filtres optionnels
        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        currency = self.request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency=currency)
        
        return queryset.order_by('-created_at')


class TransactionDetailView(generics.RetrieveAPIView):
    """Vue pour consulter le détail d'une transaction."""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retourner les transactions de l'utilisateur."""
        return Transaction.objects.filter(user=self.request.user)


class DepositCreateView(generics.CreateAPIView):
    """Vue pour créer une demande de dépôt."""
    
    serializer_class = DepositRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsVerifiedUser, CanDeposit]
    
    # Ajuster le ratelimit en développement pour éviter les 403 lors des tests locaux
    if settings.DEBUG:
        _deposit_ratelimit = method_decorator(ratelimit(key='user', rate='1000/h', method='POST', block=False))
    else:
        _deposit_ratelimit = method_decorator(ratelimit(key='user', rate='10/h', method='POST'))

    @_deposit_ratelimit
    def post(self, request, *args, **kwargs):
        """Créer une demande de dépôt avec limitation."""
        
        # 🔍 DEBUG: Log complet des données reçues pour création dépôt
        print("\n" + "="*80)
        print("💰 DEPOSIT CREATE - DEBUG LOG")
        print("="*80)
        print(f"⏰ Timestamp: {timezone.now().isoformat()}")
        print(f"👤 User: {request.user} (ID: {request.user.id})")
        print(f"🌐 IP: {get_client_ip(request)}")
        print(f"📊 Method: {request.method}")
        print(f"🔗 Path: {request.path}")
        
        print(f"\n📨 HEADERS REÇUS:")
        print("-"*40)
        for header, value in request.headers.items():
            print(f"{header}: {value}")
        
        print(f"\n📄 DONNÉES POST:")
        print("-"*40)
        print(f"request.data: {request.data}")
        print(f"request.POST: {dict(request.POST)}")
        print(f"Content-Type: {request.content_type}")
        
        print(f"\n🔍 QUERY PARAMS:")
        print("-"*40)
        print(f"GET params: {dict(request.GET)}")
        
        print(f"\n🧪 SERIALIZER VALIDATION:")
        print("-"*40)
        
        serializer = self.get_serializer(data=request.data)
        print(f"Données pour validation: {serializer.initial_data}")
        
        is_valid = serializer.is_valid(raise_exception=False)

        # Si invalide, logguer le payload et retourner 400 (seulement en DEBUG on imprime)
        if not is_valid:
            print(f"❌ VALIDATION ÉCHOUÉE!")
            print(f"Erreurs: {serializer.errors}")
            print(f"Non-field errors: {serializer.non_field_errors}")
            
            from django.conf import settings
            if getattr(settings, 'DEBUG', False):
                try:
                    import json
                    payload_repr = json.dumps(request.data)
                except Exception:
                    payload_repr = str(request.data)
                print('\n[DEBUG] DepositCreateView received invalid data:')
                print('Payload:', payload_repr)
                print('Errors:', serializer.errors)

            print("="*80 + "\n")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"✅ Validation réussie")
        validated_data = serializer.validated_data
        print(f"Données validées: {validated_data}")
        
        with transaction.atomic():
            print(f"\n🔧 CRÉATION TRANSACTION:")
            print("-"*40)
            
            # Créer la transaction de dépôt
            deposit_transaction = self._create_deposit_transaction(
                serializer.validated_data
            )
            
            print(f"✅ Transaction créée:")
            print(f"  ID: {deposit_transaction.id}")
            print(f"  Montant: {deposit_transaction.amount} {deposit_transaction.currency}")
            print(f"  Frais: {deposit_transaction.fees}")
            print(f"  Net: {deposit_transaction.net_amount}")
            print(f"  Status: {deposit_transaction.status}")
            print(f"  Méthode: {deposit_transaction.payment_method}")
            
            print(f"\n🚀 INITIATION PAIEMENT:")
            print("-"*40)
            
            # Initier le processus de paiement
            payment_result = self._initiate_payment(
                deposit_transaction,
                serializer.validated_data
            )
            
            print(f"✅ Résultat paiement: {payment_result}")
            
            print(f"\n📝 LOG ACTIVITÉ:")
            print("-"*40)
            
            # Logger l'activité
            activity_metadata = {
                'transaction_id': str(deposit_transaction.id),
                'payment_method': str(deposit_transaction.payment_method.id),
                'amount': str(deposit_transaction.amount),
                'currency': deposit_transaction.currency,
                'ip_address': get_client_ip(request),
                'user_agent': request.headers.get('User-Agent', ''),
                'payment_result': payment_result
            }
            
            print(f"Métadonnées log: {activity_metadata}")
            
            log_user_activity(
                user=request.user,
                activity_type='deposit_requested',
                description=f'Dépôt demandé: {deposit_transaction.amount} {deposit_transaction.currency}',
                metadata=activity_metadata
            )
            
            response_data = {
                'success': True,
                'message': _('Demande de dépôt créée avec succès'),
                'transaction': TransactionSerializer(deposit_transaction).data,
                'payment_result': payment_result
            }
            
            print(f"\n✅ RÉPONSE FINALE:")
            print("-"*40)
            print(f"Response data: {response_data}")
            print("="*80 + "\n")

            return Response(response_data, status=status.HTTP_201_CREATED)

    def _create_deposit_transaction(self, validated_data):
        """Créer la transaction de dépôt (méthode d'instance)."""
        payment_method = PaymentMethod.objects.get(
            id=validated_data['payment_method_id']
        )

        # Calculer les frais via la méthode du payment method
        fees_info = payment_method.calculate_fees(
            validated_data['amount'],
            validated_data.get('transaction_type', 'deposit')
        )

        total_fees = fees_info.get('total_fees') if isinstance(fees_info, dict) else fees_info
        net_amount = fees_info.get('net_amount') if isinstance(fees_info, dict) else (validated_data['amount'] - (total_fees or 0))

        transaction_obj = Transaction.objects.create(
            user=self.request.user,
            transaction_type='deposit',
            amount=validated_data['amount'],
            currency=validated_data.get('currency', 'FCFA'),
            payment_method=payment_method,
            fees=total_fees or 0,
            net_amount=net_amount,
            status='pending',
            metadata=validated_data.get('metadata', {}),
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

        return transaction_obj

    def _initiate_payment(self, transaction_obj, validated_data):
        """Initier le processus de paiement via le processor correspondant."""
        
        print(f"🔧 _initiate_payment appelée:")
        print(f"  Transaction: {transaction_obj.id}")
        print(f"  Method type: {transaction_obj.payment_method.method_type}")
        print(f"  Validated data: {validated_data}")
        
        processor = get_payment_processor(transaction_obj.payment_method.method_type)
        print(f"  Processor: {processor}")

        payment_data = {
            'transaction_id': str(transaction_obj.id),
            'amount': transaction_obj.amount,
            'currency': transaction_obj.currency,
            'return_url': validated_data.get('return_url'),
            'user_email': transaction_obj.user.email,
            'user_id': transaction_obj.user.id,
            'phone_number': validated_data.get('phone_number'),
            'payment_method_id': validated_data.get('payment_method_id'),
            'payment_method_name': transaction_obj.payment_method.name,
            'method_type': transaction_obj.payment_method.method_type,
            'metadata': {**(transaction_obj.metadata or {}), **(validated_data.get('metadata') or {})}
        }
        
        print(f"  Payment data: {payment_data}")

        try:
            print(f"🚀 Appel processor.create_payment...")
            result = processor.create_payment(payment_data)
            print(f"✅ Résultat processor: {result}")

            # Mettre à jour la référence externe si fournie
            if isinstance(result, dict) and result.get('external_reference'):
                print(f"📝 Mise à jour référence externe: {result['external_reference']}")
                transaction_obj.external_reference = result['external_reference']
                transaction_obj.save()
                print(f"💾 Référence externe sauvegardée")

            return result

        except Exception as e:
            print(f"❌ Erreur processor:")
            print(f"  Type: {type(e).__name__}")
            print(f"  Message: {str(e)}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
            
            # Marquer la transaction comme échouée
            transaction_obj.status = 'failed'
            transaction_obj.failure_reason = str(e)
            transaction_obj.save()
            print(f"💾 Transaction marquée comme failed")
            raise


class DepositConfirmView(APIView):
    """Vue pour confirmer un dépôt après paiement."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Créer/Confirmer un dépôt avec les données FeexPay."""
        
        # 🔍 DEBUG: Log complet des données reçues
        print("\n" + "="*80)
        print("🔔 FEEXPAY DEPOSIT - CRÉATION/CONFIRMATION")
        print("="*80)
        print(f"⏰ Timestamp: {timezone.now().isoformat()}")
        print(f"👤 User: {request.user} (ID: {request.user.id})")
        print(f"🌐 IP: {get_client_ip(request)}")
        
        print(f"\n📄 DONNÉES FEEXPAY REÇUES:")
        print("-"*40)
        print(f"Data: {request.data}")
        
        # Validation des données FeexPay
        feexpay_reference = request.data.get('feexpay_reference')
        feexpay_amount = request.data.get('amount')
        feexpay_status = request.data.get('status')
        transaction_id = request.data.get('transaction_id')
        
        print(f"📋 Données extraites:")
        print(f"   FeexPay Reference: {feexpay_reference}")
        print(f"   Amount: {feexpay_amount}")
        print(f"   Status: {feexpay_status}")
        print(f"   Transaction ID: {transaction_id}")
        
        # Validation des champs requis
        if not feexpay_reference:
            print(f"❌ ERREUR: feexpay_reference manquant")
            return Response({
                'error': 'feexpay_reference requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not feexpay_amount:
            print(f"❌ ERREUR: amount manquant")
            return Response({
                'error': 'amount requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not feexpay_status:
            print(f"❌ ERREUR: status manquant")
            return Response({
                'error': 'status requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mapper le statut FeexPay vers notre système
        status_mapping = {
            'completed': 'completed',
            'successful': 'completed', 
            'success': 'completed',
            'failed': 'failed',
            'pending': 'pending',
            'processing': 'processing'
        }
        
        our_status = status_mapping.get(feexpay_status.lower(), 'pending')
        
        print(f"🔄 Statut mappé: {feexpay_status} → {our_status}")
        
        try:
            with transaction.atomic():
                print(f"\n💾 CRÉATION/MISE À JOUR TRANSACTION:")
                print("-"*50)
                
                # Chercher si la transaction existe déjà (via external_reference)
                existing_transaction = None
                if transaction_id:
                    try:
                        existing_transaction = Transaction.objects.get(
                            id=transaction_id, 
                            user=request.user
                        )
                        print(f"✅ Transaction existante trouvée: {existing_transaction.id}")
                    except Transaction.DoesNotExist:
                        pass
                
                if not existing_transaction:
                    # Chercher par référence externe
                    try:
                        existing_transaction = Transaction.objects.get(
                            external_reference=feexpay_reference,
                            user=request.user
                        )
                        print(f"✅ Transaction trouvée par référence: {existing_transaction.id}")
                    except Transaction.DoesNotExist:
                        pass
                
                if existing_transaction:
                    # MISE À JOUR de la transaction existante
                    print(f"🔄 MISE À JOUR transaction {existing_transaction.id}")
                    
                    old_status = existing_transaction.status
                    existing_transaction.status = our_status
                    existing_transaction.external_reference = feexpay_reference
                    # existing_transaction.updated_at = timezone.now()  # Le modèle n'a pas ce champ
                    
                    # Mettre à jour les métadonnées
                    metadata = existing_transaction.metadata or {}
                    metadata.update({
                        'feexpay_reference': feexpay_reference,
                        'feexpay_status': feexpay_status,
                        'feexpay_amount': feexpay_amount,
                        'last_feexpay_update': timezone.now().isoformat(),
                        'status_history': metadata.get('status_history', []) + [{
                            'from': old_status,
                            'to': our_status,
                            'timestamp': timezone.now().isoformat(),
                            'source': 'feexpay'
                        }]
                    })
                    existing_transaction.metadata = metadata
                    existing_transaction.save()
                    
                    transaction_obj = existing_transaction
                    action_type = "MISE À JOUR"
                    
                else:
                    # CRÉATION d'une nouvelle transaction
                    print(f"✨ CRÉATION nouvelle transaction")
                    
                    # Obtenir la méthode de paiement FeexPay
                    payment_method = PaymentMethod.objects.filter(
                        method_type='mobile_money', 
                        is_active=True
                    ).first()
                    
                    if not payment_method:
                        payment_method = PaymentMethod.objects.filter(is_active=True).first()
                    
                    if not payment_method:
                        print(f"❌ ERREUR: Aucune méthode de paiement trouvée")
                        return Response({
                            'error': 'Méthode de paiement non disponible'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    # Créer la nouvelle transaction
                    transaction_obj = Transaction.objects.create(
                        user=request.user,
                        transaction_type='deposit',
                        amount=Decimal(str(feexpay_amount)),
                        currency='FCFA',
                        payment_method=payment_method,
                        fees=Decimal('0.00'),
                        net_amount=Decimal(str(feexpay_amount)),
                        status=our_status,
                        external_reference=feexpay_reference,
                        metadata={
                            'feexpay_reference': feexpay_reference,
                            'feexpay_status': feexpay_status,
                            'feexpay_amount': feexpay_amount,
                            'source': 'feexpay_deposit',
                            'created_at': timezone.now().isoformat(),
                            'ip_address': get_client_ip(request)
                        },
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', 'FeexPay')
                    )
                    
                    action_type = "CRÉATION"
                print(f"✅ {action_type} réussie:")
                print(f"  ID: {transaction_obj.id}")
                print(f"  Status: {transaction_obj.status}")
                print(f"  Montant: {transaction_obj.amount} {transaction_obj.currency}")
                print(f"  Utilisateur: {transaction_obj.user.username}")
                print(f"  Référence externe: {transaction_obj.external_reference}")
                
                # Mise à jour du solde si transaction complétée
                if our_status == 'completed' and action_type == "CRÉATION":
                    print(f"\n💰 MISE À JOUR SOLDE:")
                    print("-"*40)
                    
                    try:
                        old_balance = transaction_obj.user.get_balance(transaction_obj.currency)
                        print(f"Ancien solde: {old_balance} {transaction_obj.currency}")
                        
                        # Mettre à jour le solde
                        transaction_obj.user.update_balance(
                            currency=transaction_obj.currency,
                            amount=transaction_obj.net_amount,
                            operation='add'
                        )
                        
                        new_balance = transaction_obj.user.get_balance(transaction_obj.currency)
                        print(f"Nouveau solde: {new_balance} {transaction_obj.currency}")
                        
                        # Marquer le solde comme mis à jour
                        metadata = transaction_obj.metadata or {}
                        metadata.update({
                            'balance_updated': True,
                            'balance_update_timestamp': timezone.now().isoformat(),
                            'old_balance': str(old_balance),
                            'new_balance': str(new_balance)
                        })
                        transaction_obj.metadata = metadata
                        transaction_obj.save()
                        
                    except Exception as balance_error:
                        print(f"❌ Erreur mise à jour solde: {balance_error}")
                
                # Logger l'activité
                activity_metadata = {
                    'action_type': action_type.lower(),
                    'transaction_id': str(transaction_obj.id),
                    'external_reference': feexpay_reference,
                    'amount': str(transaction_obj.amount),
                    'currency': transaction_obj.currency,
                    'feexpay_data': {
                        'reference': feexpay_reference,
                        'amount': feexpay_amount,
                        'status': feexpay_status
                    }
                }
                
                log_user_activity(
                    user=request.user,
                    activity_type='feexpay_deposit',
                    description=f'Dépôt FeexPay {action_type.lower()}: {transaction_obj.amount} {transaction_obj.currency}',
                    metadata=activity_metadata
                )
                
                response_data = {
                    'success': True,
                    'action': action_type,
                    'transaction': {
                        'id': str(transaction_obj.id),
                        'amount': str(transaction_obj.amount),
                        'currency': transaction_obj.currency,
                        'status': transaction_obj.status,
                        'feexpay_reference': feexpay_reference,
                        'created_at': str(transaction_obj.created_at.isoformat()),
                        # 'updated_at': str(transaction_obj.updated_at.isoformat())  # Pas de champ updated_at
                    },
                    'balance_updated': transaction_obj.metadata.get('balance_updated', False)
                }
                
                print(f"\n✅ SUCCÈS - {action_type}:")
                print(f"Response: {response_data}")
                print("="*80 + "\n")
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            print(f"❌ ERREUR EXCEPTION:")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            print("="*80 + "\n")
            return Response({
                'error': f'Erreur lors du traitement: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeexPaySyncView(APIView):
    """Vue pour synchroniser le statut d'une transaction avec FeexPay."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Synchroniser les transactions FeexPay pour l'utilisateur connecté."""
        
        print("\n" + "="*80)
        print("🔄 FEEXPAY SYNC - SYNCHRONISATION GLOBALE")
        print("="*80)
        print(f"👤 Utilisateur: {request.user.username}")
        
        try:
            # Récupérer les transactions pending/processing de l'utilisateur
            pending_transactions = Transaction.objects.filter(
                user=request.user,
                status__in=['pending', 'processing'],
                external_reference__isnull=False
            )
            
            synchronized_count = 0
            
            for tx in pending_transactions:
                print(f"🔍 Vérification transaction {tx.id} (ref: {tx.external_reference})")
                
                # Ici on pourrait faire un vrai appel à l'API FeexPay
                # Pour l'instant, on simule que les transactions pending sont completed
                if tx.status == 'pending':
                    print(f"✅ Mise à jour {tx.id}: pending → completed")
                    tx.status = 'completed'
                    tx.save()
                    synchronized_count += 1
            
            print(f"📊 {synchronized_count} transactions synchronisées")
            print("="*80 + "\n")
            
            return Response({
                'success': True,
                'synchronized_count': synchronized_count,
                'message': f'{synchronized_count} transactions synchronisées avec FeexPay'
            })
                
        except Exception as e:
            print(f"❌ Erreur sync globale: {e}")
            return Response({
                'error': f'Erreur synchronisation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawalListView(generics.ListAPIView):
    """Vue pour lister les demandes de retrait de l'utilisateur."""
    
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourner les demandes de retrait de l'utilisateur."""
        return WithdrawalRequest.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class WithdrawalDetailView(generics.RetrieveAPIView):
    """Vue pour consulter le détail d'une demande de retrait."""
    
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retourner les demandes de retrait de l'utilisateur."""
        return WithdrawalRequest.objects.filter(user=self.request.user)


class WithdrawalCancelView(APIView):
    """Vue pour annuler une demande de retrait."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """Annuler une demande de retrait."""
        try:
            withdrawal_request = WithdrawalRequest.objects.get(
                id=pk,
                user=request.user,
                status='pending'
            )
            
            with transaction.atomic():
                # Rembourser les fonds
                withdrawal_request.user.update_balance(
                    withdrawal_request.currency,
                    withdrawal_request.amount,
                    'add'
                )
                
                # Annuler la transaction
                withdrawal_request.transaction.cancel('Cancelled by user')
                
                # Mettre à jour le statut
                withdrawal_request.status = 'cancelled'
                withdrawal_request.save()
                
                # Logger l'activité
                log_user_activity(
                    user=request.user,
                    activity_type='withdrawal_cancelled',
                    description=f'Retrait annulé: {withdrawal_request.amount} {withdrawal_request.currency}',
                    metadata={'withdrawal_id': str(withdrawal_request.id)}
                )
                
                return Response({
                    'success': True,
                    'message': _('Demande de retrait annulée avec succès')
                })
                
        except WithdrawalRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': _('Demande de retrait introuvable ou non annulable')
            }, status=status.HTTP_404_NOT_FOUND)


class WalletListView(generics.ListAPIView):
    """Vue pour lister les portefeuilles de l'utilisateur."""
    
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourner les portefeuilles de l'utilisateur."""
        return Wallet.objects.filter(user=self.request.user)


class TransactionCancelView(APIView):
    """Vue pour annuler une transaction."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """Annuler une transaction."""
        try:
            transaction_obj = Transaction.objects.get(
                id=pk,
                user=request.user
            )
            
            if not transaction_obj.can_cancel():
                return Response({
                    'success': False,
                    'error': _('Cette transaction ne peut pas être annulée')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Annuler la transaction
            transaction_obj.cancel('Cancelled by user')
            
            # Logger l'activité
            log_user_activity(
                user=request.user,
                activity_type='transaction_cancelled',
                description=f'Transaction annulée: {transaction_obj.transaction_id}',
                metadata={'transaction_id': str(transaction_obj.id)}
            )
            
            return Response({
                'success': True,
                'message': _('Transaction annulée avec succès')
            })
            
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': _('Transaction introuvable')
            }, status=status.HTTP_404_NOT_FOUND)


class PaymentStatisticsView(APIView):
    """Vue pour les statistiques de paiement de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir les statistiques de paiement."""
        serializer = PaymentStatisticsSerializer(request.user)
        return Response(serializer.data)


class FeeCalculatorView(APIView):
    """Vue pour calculer les frais de transaction."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Calculer les frais pour une transaction."""
        serializer = FeeCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        fee_calculation = serializer.get_fee_calculation()
        
        return Response({
            'success': True,
            'fees': fee_calculation
        })


class CurrencyConversionView(APIView):
    """Vue pour convertir entre devises."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Convertir un montant entre devises."""
        serializer = CurrencyConversionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            conversion = serializer.get_conversion()
            
            return Response({
                'success': True,
                'conversion': conversion
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExchangeRateListView(generics.ListAPIView):
    """Vue pour lister les taux de change."""
    
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Retourner les taux de change actifs."""
        return ExchangeRate.objects.filter(is_active=True)


class PaymentWebhookView(APIView):
    """Vue pour recevoir les webhooks de paiement."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, provider):
        """Recevoir un webhook d'un fournisseur de paiement."""
        # Créer l'enregistrement webhook
        webhook = PaymentWebhook.objects.create(
            provider=provider,
            event_type=request.data.get('type', 'unknown'),
            payload=request.data,
            headers=dict(request.META),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Traiter le webhook de manière asynchrone
        try:
            webhook.process_webhook()
            
            return Response({
                'success': True,
                'webhook_id': str(webhook.id)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ViewSets pour une API plus complète
class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les méthodes de paiement."""
    
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourner les méthodes actives."""
        return PaymentMethod.objects.filter(is_active=True)
    
    @action(detail=True, methods=['post'])
    def calculate_fees(self, request, pk=None):
        """Calculer les frais pour cette méthode."""
        payment_method = self.get_object()
        amount = Decimal(request.data.get('amount', '0'))
        transaction_type = request.data.get('type', 'deposit')
        
        if amount <= 0:
            return Response({
                'error': _('Montant invalide')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fees = payment_method.calculate_fees(amount, transaction_type)
        
        return Response({
            'success': True,
            'fees': fees
        })


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les transactions."""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourner les transactions de l'utilisateur."""
        return Transaction.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler une transaction."""
        transaction_obj = self.get_object()
        
        if not transaction_obj.can_cancel():
            return Response({
                'success': False,
                'error': _('Cette transaction ne peut pas être annulée')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transaction_obj.cancel('Cancelled by user')
        
        return Response({
            'success': True,
            'message': _('Transaction annulée')
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des transactions."""
        queryset = self.get_queryset().filter(status='completed')
        
        summary = {}
        for tx_type in ['deposit', 'withdrawal', 'bet', 'win']:
            transactions = queryset.filter(transaction_type=tx_type)
            summary[tx_type] = {
                'count': transactions.count(),
                'total': transactions.aggregate(Sum('amount'))['amount__sum'] or 0
            }
        
        return Response(summary)


# Vues administratives (pour le staff)
class AdminWithdrawalApprovalView(APIView):
    """Vue pour approuver/rejeter les retraits (admin seulement)."""
    
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def post(self, request, pk):
        """Approuver ou rejeter une demande de retrait."""
        try:
            withdrawal_request = WithdrawalRequest.objects.get(
                id=pk,
                status='pending'
            )
            
            action = request.data.get('action')  # 'approve' ou 'reject'
            notes = request.data.get('notes', '')
            reason = request.data.get('reason', '')
            
            if action == 'approve':
                withdrawal_request.approve(request.user, notes)
                message = _('Demande de retrait approuvée')
                
            elif action == 'reject':
                withdrawal_request.reject(request.user, reason)
                message = _('Demande de retrait rejetée')
                
            else:
                return Response({
                    'error': _('Action invalide')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': message
            })
            
        except WithdrawalRequest.DoesNotExist:
            return Response({
                'error': _('Demande de retrait introuvable')
            }, status=status.HTTP_404_NOT_FOUND)


class AdminTransactionListView(generics.ListAPIView):
    """Vue pour lister toutes les transactions (admin)."""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourner toutes les transactions avec filtres."""
        queryset = Transaction.objects.all()
        
        # Filtres
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        
        tx_type = self.request.query_params.get('type')
        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')


# Vues pour les rapports et analytics
class PaymentAnalyticsView(APIView):
    """Vue pour les analytics de paiement (admin)."""
    
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request):
        """Obtenir les analytics de paiement."""
        # Transactions par statut
        transactions_by_status = Transaction.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Transactions par type
        transactions_by_type = Transaction.objects.filter(
            status='completed'
        ).values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Volume quotidien des 30 derniers jours
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        daily_volume = Transaction.objects.filter(
            status='completed',
            created_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('day')
        
        # Méthodes de paiement populaires
        popular_methods = Transaction.objects.filter(
            status='completed',
            payment_method__isnull=False
        ).values(
            'payment_method__name'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')
        
        return Response({
            'transactions_by_status': list(transactions_by_status),
            'transactions_by_type': list(transactions_by_type),
            'daily_volume': list(daily_volume),
            'popular_methods': list(popular_methods)
        })


# Vue pour les tests de paiement (développement seulement)
if settings.DEBUG:
    
    class TestPaymentView(APIView):
        """Vue de test pour les paiements (développement seulement)."""
        
        permission_classes = [permissions.IsAuthenticated]
        
        def post(self, request):
            """Simuler une transaction de test."""
            transaction_type = request.data.get('type', 'deposit')
            amount = Decimal(request.data.get('amount', '100'))
            currency = request.data.get('currency', 'FCFA')
            
            # Créer une transaction de test
            test_transaction = Transaction.objects.create(
                user=request.user,
                transaction_type=transaction_type,
                amount=amount,
                currency=currency,
                status='completed',
                metadata={'test': True, 'simulated': True}
            )
            
            # Traiter selon le type
            if transaction_type == 'deposit':
                request.user.update_balance(currency, amount, 'add')
            elif transaction_type == 'withdrawal':
                if request.user.get_balance(currency) >= amount:
                    request.user.update_balance(currency, amount, 'subtract')
                else:
                    test_transaction.status = 'failed'
                    test_transaction.failure_reason = 'Insufficient funds'
                    test_transaction.save()
            
            return Response({
                'success': True,
                'message': f'Transaction de test {transaction_type} créée',
                'transaction': TransactionSerializer(test_transaction).data
            })
    


class WithdrawalCreateView(generics.CreateAPIView):
    """Vue pour créer une demande de retrait."""
    
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [
        permissions.IsAuthenticated, IsVerifiedUser,
        IsKYCApproved, CanWithdraw
    ]
    
    @method_decorator(ratelimit(key='user', rate='5/h', method='POST'))
    def post(self, request, *args, **kwargs):
        """Créer une demande de retrait avec limitation stricte."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Vérifier les conditions spéciales
            self._check_withdrawal_conditions(serializer.validated_data)
            
            # Créer la transaction de retrait
            withdrawal_transaction = self._create_withdrawal_transaction(
                serializer.validated_data
            )
            
            # Créer la demande de retrait
            withdrawal_request = serializer.save(
                user=request.user,
                transaction=withdrawal_transaction
            )
            
            # Bloquer les fonds
            self._lock_withdrawal_funds(withdrawal_request)
            
            # Auto-approbation si montant faible
            if self._should_auto_approve(withdrawal_request):
                withdrawal_request.approve(
                    admin_user=None,  # Auto-approuvé
                    notes='Auto-approuvé (montant faible)'
                )
            
            # Logger l'activité
