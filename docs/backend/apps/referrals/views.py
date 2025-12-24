# apps/referrals/views.py
# =========================
# ✅ VERSION CORRIGÉE - Dashboard complet implémenté

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Q, Sum, Count, Avg
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from decimal import Decimal
from datetime import date
from io import BytesIO
import logging

# Imports conditionnels pour QR code
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

from .models import (
    ReferralProgram, Referral, ReferralCommission,
    PremiumSubscription, ReferralStatistics, ReferralBonus, ReferralCode
)

from .serializers import (
    ReferralProgramSerializer, ReferralSerializer, CreateReferralSerializer,
    ReferralCommissionSerializer, PremiumSubscriptionSerializer, 
    CreatePremiumSubscriptionSerializer, ReferralStatisticsSerializer,
    ReferralBonusSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


# Pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def generate_qr_code(request, referral_code):
    """Générer un QR code pour un code de parrainage."""
    if not HAS_QRCODE:
        return HttpResponse(
            "QR code non disponible - installer 'pip install qrcode[pil]'",
            status=500
        )
    
    try:
        base_url = request.build_absolute_uri('/').rstrip('/')
        referral_url = f"{base_url}/signup?ref={referral_code}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(referral_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="qr_code_{referral_code}.png"'
        return response
        
    except Exception as e:
        logger.error(f"Erreur QR code: {str(e)}")
        return HttpResponse(f"Erreur: {str(e)}", status=500)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def validate_referral_code(request, referral_code):
    """Valider un code de parrainage."""
    try:
        if referral_code.startswith('USER_'):
            user_id = referral_code.replace('USER_', '')
            try:
                user_id = int(user_id)
                referrer = User.objects.get(id=user_id)
                
                return Response({
                    'valid': True,
                    'referrer_username': referrer.username,
                    'referrer_id': referrer.id,
                    'message': 'Code de parrainage valide'
                })
                
            except (ValueError, User.DoesNotExist):
                return Response({
                    'valid': False,
                    'message': 'Code de parrainage invalide'
                })
        
        return Response({
            'valid': False,
            'message': 'Format de code invalide'
        })
            
    except Exception as e:
        logger.error(f"Erreur validation code: {str(e)}")
        return Response({
            'valid': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)


class ReferralProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les programmes de parrainage."""
    
    queryset = ReferralProgram.objects.filter(status='active')
    serializer_class = ReferralProgramSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['commission_type', 'status']
    ordering_fields = ['created_at', 'commission_rate', 'name']
    ordering = ['-is_default', 'name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return ReferralProgram.objects.all()
        return queryset.filter(status='active')
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Obtenir le programme par défaut."""
        program = ReferralProgram.get_default_program()
        if not program:
            # Si aucun programme par défaut, retourner le premier programme actif
            program = ReferralProgram.objects.filter(status='active').first()
        
        if program:
            serializer = self.get_serializer(program)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Aucun programme disponible'},
            status=status.HTTP_404_NOT_FOUND
        )


class ReferralViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des parrainages."""
    
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['referred__username', 'referred__email']
    filterset_fields = ['status', 'is_premium_referrer']
    ordering_fields = ['created_at', 'total_commission_earned', 'games_played']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Referral.objects.filter(
            referrer=self.request.user
        ).select_related('program', 'referrer', 'referred')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReferralSerializer
        return ReferralSerializer
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        ✅ DASHBOARD COMPLET - ENDPOINT PRINCIPAL
        Retourne toutes les données nécessaires pour le dashboard frontend
        """
        user = request.user
        
        try:
            logger.info(f"Dashboard demandé par {user.username}")
            
            # ===== RÉCUPÉRATION DES DONNÉES DE BASE =====
            referrals = self.get_queryset()
            active_referrals = referrals.filter(status='active')
            
            # Commission totale gagnée
            total_commission = referrals.aggregate(
                total=Sum('total_commission_earned')
            )['total'] or Decimal('0.00')
            
            # Commission ce mois-ci
            current_month = date.today().replace(day=1)
            commission_this_month = ReferralCommission.objects.filter(
                referral__referrer=user,
                created_at__date__gte=current_month,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Commissions en attente de traitement
            pending_commissions = ReferralCommission.objects.filter(
                referral__referrer=user,
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # ===== STATUT PREMIUM =====
            has_premium = PremiumSubscription.objects.filter(
                user=user,
                status='active',
                end_date__gt=timezone.now()
            ).exists()
            
            # ===== CODE DE PARRAINAGE =====
            user_referral_code = ReferralCode.objects.filter(user=user).first()
            referral_code = user_referral_code.code if user_referral_code else f"USER_{user.id}"
            
            # ===== TAUX DE COMMISSION =====
            default_program = ReferralProgram.get_default_program()
            commission_rate = float(default_program.commission_rate) if default_program else 10.0
            
            # ===== TOP FILLEULS =====
            top_referrals = referrals.order_by('-total_commission_earned')[:5]
            top_referrals_data = ReferralSerializer(top_referrals, many=True).data
            
            # ===== COMMISSIONS RÉCENTES =====
            recent_commissions = ReferralCommission.objects.filter(
                referral__referrer=user
            ).select_related(
                'referral__referred', 
                'game'
            ).order_by('-created_at')[:10]
            recent_commissions_data = ReferralCommissionSerializer(
                recent_commissions, 
                many=True
            ).data
            
            # ===== BONUS DISPONIBLES =====
            available_bonuses = ReferralBonus.objects.filter(
                referral__referrer=user,
                status='approved'
            ).order_by('-created_at')[:5]
            available_bonuses_data = ReferralBonusSerializer(
                available_bonuses, 
                many=True
            ).data
            
            # ===== STATISTIQUES AVANCÉES =====
            stats = {
                'conversion_rate': 0.0,
                'average_games_per_referral': 0.0,
                'total_games_played': 0,
            }
            
            if referrals.exists():
                total_games = referrals.aggregate(
                    total=Sum('games_played')
                )['total'] or 0
                
                stats['total_games_played'] = total_games
                
                if active_referrals.exists():
                    stats['conversion_rate'] = (
                        active_referrals.count() / referrals.count()
                    ) * 100
                    stats['average_games_per_referral'] = (
                        total_games / active_referrals.count()
                    )
            
            # ===== CONSTRUCTION DE LA RÉPONSE =====
            response_data = {
                # Statistiques principales
                'total_referrals': referrals.count(),
                'active_referrals': active_referrals.count(),
                'total_commission_earned': float(total_commission),
                'commission_this_month': float(commission_this_month),
                'pending_commissions': float(pending_commissions),
                
                # Informations utilisateur
                'premium_status': has_premium,
                'referral_code': referral_code,
                'commission_rate': commission_rate,
                
                # Données détaillées
                'stats': stats,
                'recent_commissions': recent_commissions_data,
                'top_referrals': top_referrals_data,
                'available_bonuses': available_bonuses_data,
            }
            
            logger.info(f"Dashboard généré avec succès pour {user.username}")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Erreur dashboard pour {user.username}: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Erreur lors du chargement du dashboard',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def my_code(self, request):
        """Obtenir le code de parrainage personnalisé."""
        user = request.user
        referral_code = f"USER_{user.id}"
        
        base_url = request.build_absolute_uri('/').rstrip('/')
        referral_url = f"{base_url}/signup?ref={referral_code}"
        
        # Statistiques du code
        referrals_count = Referral.objects.filter(referrer=user).count()
        total_earnings = Referral.objects.filter(referrer=user).aggregate(
            total=Sum('total_commission_earned')
        )['total'] or Decimal('0.00')
        
        return Response({
            'referral_code': referral_code,
            'referral_url': referral_url,
            'qr_code_url': f"{base_url}/api/v1/referrals/qr-code/{referral_code}/",
            'statistics': {
                'total_referrals': referrals_count,
                'total_earnings': float(total_earnings)
            }
        })


class ReferralCommissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les commissions de parrainage."""
    
    serializer_class = ReferralCommissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['referral__referred__username']
    filterset_fields = ['status', 'currency']
    ordering_fields = ['created_at', 'amount', 'processed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ReferralCommission.objects.filter(
            referral__referrer=self.request.user
        ).select_related('referral__referred', 'game', 'transaction')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des commissions."""
        queryset = self.get_queryset()
        
        total_stats = queryset.aggregate(
            total_earned=Sum('amount', filter=Q(status='completed')),
            total_pending=Sum('amount', filter=Q(status='pending')),
            total_count=Count('id'),
            avg_commission=Avg('amount', filter=Q(status='completed'))
        )
        
        return Response({
            'total_earned': float(total_stats['total_earned'] or 0),
            'total_pending': float(total_stats['total_pending'] or 0),
            'total_commissions': total_stats['total_count'] or 0,
            'average_commission': float(total_stats['avg_commission'] or 0)
        })


class PremiumSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les abonnements premium."""
    
    serializer_class = PremiumSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['plan_type', 'status', 'auto_renewal']
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return PremiumSubscription.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePremiumSubscriptionSerializer
        return PremiumSubscriptionSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer un nouvel abonnement premium."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Créer l'abonnement avec les données validées
        subscription = PremiumSubscription.objects.create(
            user=request.user,
            plan_type=serializer.validated_data['plan_type'],
            price=serializer.validated_data['price'],
            currency=serializer.validated_data['currency'],
            auto_renewal=serializer.validated_data.get('auto_renewal', False),
            status='active'
        )
        
        # Retourner les données du nouvel abonnement
        output_serializer = PremiumSubscriptionSerializer(subscription)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Obtenir l'abonnement premium actuel."""
        subscription = PremiumSubscription.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if subscription and subscription.is_active():
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        
        return Response(
            {'message': 'Aucun abonnement premium actif'},
            status=status.HTTP_404_NOT_FOUND
        )


class ReferralStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les statistiques de parrainage."""
    
    serializer_class = ReferralStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['period_type']
    ordering_fields = ['period_start', 'total_commission_earned']
    ordering = ['-period_start']
    
    def get_queryset(self):
        return ReferralStatistics.objects.filter(user=self.request.user)


class ReferralBonusViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les bonus de parrainage."""
    
    serializer_class = ReferralBonusSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['bonus_type', 'status']
    ordering_fields = ['created_at', 'amount', 'expires_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ReferralBonus.objects.filter(
            referral__referrer=self.request.user
        ).select_related('referral', 'transaction')
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Obtenir les bonus disponibles à réclamer."""
        available_bonuses = self.get_queryset().filter(
            status='approved',
            expires_at__gt=timezone.now()
        ).order_by('expires_at')
        
        serializer = self.get_serializer(available_bonuses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        """Réclamer un bonus."""
        bonus = self.get_object()
        
        try:
            transaction = bonus.claim()
            return Response({
                'message': 'Bonus réclamé avec succès',
                'transaction_id': str(transaction.id),
                'amount': float(bonus.amount)
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            ) 
