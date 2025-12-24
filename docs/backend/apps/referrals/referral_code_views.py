"""
Views pour gérer les codes de parrainage partageables (style 1xBet).
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Q, Count, F, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
import uuid
import logging
from decimal import Decimal

from .models import ReferralCode, ReferralCodeClick, ReferralCodeShare, Referral
from .serializers import (
    ReferralCodeListSerializer,
    ReferralCodeDetailSerializer,
    ReferralCodeCreateSerializer,
    ReferralLinkShareSerializer,
)

logger = logging.getLogger(__name__)


class ReferralCodeViewSet(viewsets.ViewSet):
    """
    ViewSet pour gérer les codes de parrainage partageables.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Lister tous les codes de parrainage de l'utilisateur."""
        codes = ReferralCode.objects.filter(user=request.user).order_by('-created_at')
        serializer = ReferralCodeListSerializer(codes, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Obtenir les détails d'un code de parrainage."""
        try:
            code = ReferralCode.objects.get(id=pk, user=request.user)
            serializer = ReferralCodeDetailSerializer(code)
            return Response(serializer.data)
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def create(self, request):
        """Créer un nouveau code de parrainage."""
        serializer = ReferralCodeCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            code = serializer.save()
            return Response(
                ReferralCodeDetailSerializer(code).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Obtenir les statistiques complètes d'un code."""
        try:
            code = ReferralCode.objects.get(id=pk, user=request.user)
            
            # Statistiques de clics
            total_clicks = code.clicks.count()
            total_conversions = code.clicks.filter(converted_user__isnull=False).count()
            
            # Commissions générées
            converted_users = list(
                code.clicks.filter(
                    converted_user__isnull=False
                ).values_list('converted_user', flat=True).distinct()
            )
            
            referrals = Referral.objects.filter(
                referrer=request.user,
                referred__in=converted_users
            ) if converted_users else Referral.objects.none()
            
            total_commission = referrals.aggregate(
                total=Sum('total_commission_earned')
            )['total'] or Decimal('0.00')
            
            # Statistiques par canal
            shares_by_channel = code.shares.values('channel').annotate(
                count=Count('id')
            )
            
            return Response({
                'code': code.code,
                'total_clicks': total_clicks,
                'total_conversions': total_conversions,
                'conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0,
                'total_commission': str(total_commission),
                'shares_by_channel': list(shares_by_channel),
                'is_active': code.status == 'active',
                'expiration_date': code.expires_at,
                'max_uses': code.max_uses,
                'current_uses': code.current_uses,
            })
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Erreur stats: {str(e)}")
            traceback.print_exc()
            return Response(
                {'detail': f'Erreur: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Partager un code de parrainage."""
        try:
            code = ReferralCode.objects.get(id=pk, user=request.user)
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ReferralLinkShareSerializer(data=request.data)
        
        if serializer.is_valid():
            channel = serializer.validated_data['channel']
            message = serializer.validated_data.get('message', '')
            
            # Créer un enregistrement de partage
            share = ReferralCodeShare.objects.create(
                code=code,
                channel=channel
            )
            
            # Préparer les données de partage selon le canal
            share_data = {
                'channel': channel,
                'message': message,
                'link': code.full_url,
                'short_link': code.short_url,
                'qr_code_url': f"{request.build_absolute_uri('/').rstrip('/')}/api/referral-codes/{pk}/qr-code/",
            }
            
            # Personnaliser le message selon le canal
            if channel == 'whatsapp':
                share_data['share_url'] = f"https://wa.me/?text={message} {code.full_url}"
            elif channel == 'telegram':
                share_data['share_url'] = f"https://t.me/share/url?url={code.full_url}&text={message}"
            elif channel == 'facebook':
                share_data['share_url'] = f"https://www.facebook.com/sharer/sharer.php?u={code.full_url}"
            elif channel == 'twitter':
                share_data['share_url'] = f"https://twitter.com/intent/tweet?url={code.full_url}&text={message}"
            elif channel == 'email':
                share_data['share_url'] = f"mailto:?subject=Rejoins-moi&body={message}%20{code.full_url}"
            elif channel == 'sms':
                share_data['share_url'] = f"sms:?body={message} {code.full_url}"
            
            return Response({
                'success': True,
                'message': _('Lien partagé avec succès.'),
                'share_data': share_data,
                'share_id': str(share.id),
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        """Générer un QR code pour un code de parrainage."""
        try:
            import qrcode
            from io import BytesIO
            
            code = ReferralCode.objects.get(id=pk, user=request.user)
            
            # Générer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(code.full_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="qr_code_{code.code}.png"'
            return response
            
        except ImportError:
            return Response(
                {'detail': _('QR code non disponible')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactiver un code de parrainage."""
        try:
            code = ReferralCode.objects.get(id=pk, user=request.user)
            code.deactivate()
            
            return Response({
                'success': True,
                'message': _('Code de parrainage désactivé.'),
                'code': ReferralCodeDetailSerializer(code).data,
            })
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Réactiver un code de parrainage."""
        try:
            code = ReferralCode.objects.get(id=pk, user=request.user)
            code.activate()
            
            return Response({
                'success': True,
                'message': _('Code de parrainage activé.'),
                'code': ReferralCodeDetailSerializer(code).data,
            })
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def conversions(self, request, pk=None):
        """Obtenir les conversions d'un code de parrainage."""
        try:
            code = ReferralCode.objects.get(id=pk, user=request.user)
            
            # Obtenir les conversions
            conversions = code.clicks.filter(converted_user__isnull=False).select_related(
                'converted_user'
            ).order_by('-converted_at')
            
            # Paginer les résultats
            page = request.query_params.get('page', 1)
            limit = request.query_params.get('limit', 20)
            
            start = (int(page) - 1) * int(limit)
            end = start + int(limit)
            
            total = conversions.count()
            conversions_page = conversions[start:end]
            
            conversion_data = []
            for conversion in conversions_page:
                conversion_data.append({
                    'id': str(conversion.id),
                    'user_id': conversion.converted_user.id if conversion.converted_user else None,
                    'username': conversion.converted_user.username if conversion.converted_user else None,
                    'first_name': conversion.converted_user.first_name if conversion.converted_user else None,
                    'last_name': conversion.converted_user.last_name if conversion.converted_user else None,
                    'email': conversion.converted_user.email if conversion.converted_user else None,
                    'converted_at': conversion.converted_at,
                    'clicked_at': conversion.clicked_at,
                })
            
            return Response({
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': (total + int(limit) - 1) // int(limit),
                'conversions': conversion_data,
            })
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Obtenir les analytiques globales de parrainage."""
        user_codes = ReferralCode.objects.filter(user=request.user)
        
        total_clicks = sum(code.clicks.count() for code in user_codes)
        total_conversions = sum(
            code.clicks.filter(converted_user__isnull=False).count()
            for code in user_codes
        )
        
        # Commissions
        referrals = Referral.objects.filter(referrer=request.user)
        total_commission = referrals.aggregate(
            total=Sum('total_commission_earned')
        )['total'] or Decimal('0.00')
        
        return Response({
            'total_codes': user_codes.count(),
            'active_codes': user_codes.filter(status='active').count(),
            'total_clicks': total_clicks,
            'total_conversions': total_conversions,
            'conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0,
            'total_commission': str(total_commission),
            'total_referrals': referrals.count(),
        })


class ReferralCodeClickTrackingView(viewsets.ViewSet):
    """
    ViewSet pour tracker les clics sur les codes de parrainage.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'], url_path='track/(?P<code>[^/.]+)')
    def track_click(self, request, code=None):
        """Tracker un clic sur un code de parrainage."""
        try:
            referral_code = ReferralCode.objects.get(code=code)
            
            # Créer un enregistrement de clic
            click = ReferralCodeClick.objects.create(
                code=referral_code,
                visitor_ip=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', ''),
            )
            
            return Response({
                'success': True,
                'message': _('Clic enregistré.'),
                'click_id': str(click.id),
                'redirect_url': '/',  # Redirection vers la page d'accueil
            })
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage invalide.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Obtenir l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ReferralLinkView(viewsets.ViewSet):
    """
    ViewSet pour les liens de parrainage publics.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def retrieve(self, request, pk=None):
        """Obtenir les informations publiques d'un code."""
        try:
            code = ReferralCode.objects.get(code=pk)
            
            if not code.is_active:
                return Response(
                    {'detail': _('Ce code de parrainage n\'est pas actif.')},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Tracker le clic
            click = ReferralCodeClick.objects.create(
                code=code,
                visitor_ip=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', ''),
            )
            
            # Obtenir les statistiques publiques
            stats = {
                'code': code.code,
                'referrer_username': code.user.username,
                'is_active': code.is_active,
                'has_capacity': code.has_capacity,
                'total_clicks': code.clicks.count(),
            }
            
            return Response(stats)
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': _('Code de parrainage invalide.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Obtenir l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
