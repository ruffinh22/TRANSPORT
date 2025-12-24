# apps/referrals/additional_views.py
# =====================================
# Vues supplémentaires à ajouter progressivement

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
import json
import logging

from .models import Referral, ReferralProgram

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def join_via_referral(request, referral_code):
    """Lien de parrainage direct pour inscription."""
    try:
        # Valider le code de parrainage
        if referral_code.startswith('USER_'):
            user_id = referral_code.replace('USER_', '')
            try:
                user_id = int(user_id)
                referrer = User.objects.get(id=user_id)
                
                # Rediriger vers la page d'inscription avec le code
                signup_url = f"/signup?ref={referral_code}&referrer={referrer.username}"
                return redirect(signup_url)
                
            except (ValueError, User.DoesNotExist):
                return Response({
                    'error': 'Code de parrainage invalide'
                }, status=status.HTTP_404_NOT_FOUND)
        
        else:
            return Response({
                'error': 'Format de code invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Erreur join_via_referral: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_commissions(request):
    """Export des commissions au format CSV."""
    try:
        # Pour le moment, retourner un placeholder
        return Response({
            'message': 'Export des commissions - Fonction à implémenter',
            'format': 'CSV',
            'user': request.user.username
        })
        
    except Exception as e:
        logger.error(f"Erreur export_commissions: {str(e)}")
        return Response({
            'error': 'Erreur lors de l\'export'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def premium_payment_webhook(request):
    """Webhook pour les paiements premium."""
    try:
        # Validation basique du webhook
        if request.content_type != 'application/json':
            return JsonResponse({
                'error': 'Content-Type doit être application/json'
            }, status=400)
        
        data = json.loads(request.body)
        
        # Log pour debug
        logger.info(f"Webhook premium reçu: {data}")
        
        # Placeholder pour traitement
        return JsonResponse({
            'status': 'success',
            'message': 'Webhook reçu - Traitement à implémenter'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON invalide'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Erreur premium_payment_webhook: {str(e)}")
        return JsonResponse({
            'error': 'Erreur interne'
        }, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def referral_analytics_view(request):
    """Vue analytics globale."""
    try:
        user = request.user
        
        # Statistiques de base
        referrals = Referral.objects.filter(referrer=user)
        
        analytics_data = {
            'user': user.username,
            'total_referrals': referrals.count(),
            'active_referrals': referrals.filter(status='active').count(),
            'total_commission': float(referrals.aggregate(
                total=models.Sum('total_commission_earned')
            )['total'] or 0),
            'message': 'Analytics détaillées - Fonction à développer'
        }
        
        return Response(analytics_data)
        
    except Exception as e:
        logger.error(f"Erreur referral_analytics_view: {str(e)}")
        return Response({
            'error': 'Erreur lors du calcul des analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def bulk_bonus_creation(request):
    """Création de bonus en masse."""
    try:
        # Placeholder pour création en masse
        return Response({
            'message': 'Création de bonus en masse - Fonction à implémenter',
            'admin_user': request.user.username
        })
        
    except Exception as e:
        logger.error(f"Erreur bulk_bonus_creation: {str(e)}")
        return Response({
            'error': 'Erreur lors de la création des bonus'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_dashboard_view(request):
    """Tableau de bord admin."""
    try:
        # Statistiques globales
        dashboard_data = {
            'total_users': User.objects.count(),
            'total_referrals': Referral.objects.count(),
            'active_programs': ReferralProgram.objects.filter(status='active').count(),
            'message': 'Dashboard admin - Données détaillées à implémenter'
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        logger.error(f"Erreur admin_dashboard_view: {str(e)}")
        return Response({
            'error': 'Erreur lors du chargement du dashboard'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Fonction utilitaire pour créer un parrainage
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_referral_from_code(request):
    """Créer un parrainage à partir d'un code."""
    try:
        referral_code = request.data.get('referral_code')
        
        if not referral_code:
            return Response({
                'error': 'Code de parrainage requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider le code
        if referral_code.startswith('USER_'):
            user_id = referral_code.replace('USER_', '')
            try:
                user_id = int(user_id)
                referrer = User.objects.get(id=user_id)
                
                # Vérifier que l'utilisateur ne se parraine pas lui-même
                if referrer == request.user:
                    return Response({
                        'error': 'Impossible de se parrainer soi-même'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Vérifier si un parrainage existe déjà
                existing_referral = Referral.objects.filter(
                    referrer=referrer,
                    referred=request.user
                ).first()
                
                if existing_referral:
                    return Response({
                        'message': 'Parrainage déjà existant',
                        'referral_id': str(existing_referral.id)
                    })
                
                # Créer le parrainage
                program = ReferralProgram.get_default_program()
                if not program:
                    return Response({
                        'error': 'Aucun programme de parrainage actif'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                referral = Referral.objects.create(
                    referrer=referrer,
                    referred=request.user,
                    program=program
                )
                
                return Response({
                    'message': 'Parrainage créé avec succès',
                    'referral_id': str(referral.id),
                    'referrer': referrer.username
                }, status=status.HTTP_201_CREATED)
                
            except (ValueError, User.DoesNotExist):
                return Response({
                    'error': 'Code de parrainage invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({
                'error': 'Format de code invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Erreur create_referral_from_code: {str(e)}")
        return Response({
            'error': 'Erreur lors de la création du parrainage'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
