# apps/accounts/views.py
# =======================

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import User, KYCDocument, UserActivity, UserSettings
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, 
    UserBalanceSerializer, KYCDocumentSerializer,
    UserStatisticsSerializer, CustomTokenObtainPairSerializer,
    UserActivitySerializer, UserSettingsSerializer,
    PasswordChangeSerializer, EmailVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, UserSerializer,
    UserRegistrationResponseSerializer
)
from apps.core.permissions import IsOwnerOrReadOnly
from apps.core.utils import log_user_activity, get_client_ip, log_user_activity_with_ip
from apps.core.pagination import StandardResultsSetPagination
from .rate_limit_utils import safe_ratelimit_key, safe_user_or_ip_key, get_user_or_ip


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour l'authentification JWT avec sécurité renforcée."""
    
    serializer_class = CustomTokenObtainPairSerializer
    
    # @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))  # Temporarily disabled for debugging
    def post(self, request, *args, **kwargs):
        """Connexion avec limitation de taux et logging."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Récupérer l'utilisateur connecté
            username = request.data.get('username', '')
            
            try:
                if '@' in username:
                    user = User.objects.get(email=username.lower())
                else:
                    user = User.objects.get(username=username)
                
                # Logger l'activité de connexion
                log_user_activity_with_ip(
                    user=user,
                    activity_type='login',
                    description='Connexion réussie',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'login_method': 'jwt',
                        'device_info': self._get_device_info(request)
                    }
                )
                
                # Mettre à jour les informations de session
                user.last_activity = timezone.now()
                user.last_login_ip = get_client_ip(request)
                user.save(update_fields=['last_activity', 'last_login_ip'])
                
            except User.DoesNotExist:
                pass
        
        return response
    
    def _get_device_info(self, request):
        """Extraire les informations du dispositif."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return {
            'user_agent': user_agent,
            'ip': get_client_ip(request),
            'method': request.method,
        }


class UserRegistrationView(generics.CreateAPIView):
    """Vue d'inscription des utilisateurs avec validation complète."""
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key=safe_ratelimit_key, rate='3/m', method='POST', block=False))
    def post(self, request, *args, **kwargs):
        """Inscription avec limitation de taux.

        Utilise `block=False` pour que nous puissions renvoyer une erreur 429
        (Too Many Requests) avec un message clair au lieu d'un 403 générique.
        Utilise safe_ratelimit_key pour éviter les erreurs d'IP en développement.
        """
        # Si la requête a dépassé la limite, `django-ratelimit` marque
        # `request.limited` à True (avec block=False). Retourner 429.
        if getattr(request, 'limited', False):
            return Response({
                'success': False,
                'error': 'Trop de tentatives d\'inscription. Réessayez dans quelques minutes.'
            }, status=429)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Créer l'utilisateur
            user = serializer.save()
            
            # Logger l'activité d'inscription
            
            
            # Générer token de vérification et envoyer l'email
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            self._send_verification_email(user, request, uid=uid, token=token)
            
            # Créer les tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': _('Inscription réussie. Veuillez vérifier votre email.'),

                'user': UserRegistrationResponseSerializer(user, context={'request': request}).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
    
    def _send_verification_email(self, user, request, uid: str = None, token: str = None):
        """Envoyer l'email de vérification en incluant uid+token."""
        try:
            # Sujet optimisé anti-spam (sans mots suspects)
            subject = 'Confirmez votre inscription - RumoRush'

            # Build verification link (frontend supports both formats)
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://rumorush.com')
            if uid and token:
                verification_link = f"{frontend_url}/verify-email/{uid}/{token}"
            else:
                verification_link = f"{frontend_url}/verify-email/{user.id}/"

            context = {
                'user': user,
                'verification_link': verification_link,
                'site_name': 'RumoRush',  # Sans majuscules excessives
                'support_email': 'support@rumorush.com'
            }
            
            # Template HTML et version texte
            html_message = render_to_string('emails/verify_email.html', context)
            text_message = f"""
Bonjour {user.first_name or user.username},

Merci de vous être inscrit sur RumoRush.

Pour activer votre compte, cliquez sur ce lien :
{verification_link}

Ce lien expire dans 24 heures.

Si vous n'avez pas créé ce compte, ignorez cet email.

Cordialement,
L'équipe RumoRush
support@rumorush.com
            """.strip()

            # Envoi avec version texte ET HTML (meilleur score anti-spam)
            send_mail(
                subject,
                text_message,  # Version texte obligatoire
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=True
            )

            # Logger l'envoi d'email
            log_user_activity_with_ip(
                user=user,
                activity_type='email_sent',
                description='Email de vérification envoyé'
            )

        except Exception as e:
            # Logger l'erreur mais ne pas faire échouer l'inscription
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur envoi email vérification pour {user.email}: {e}")


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour consulter et modifier le profil utilisateur."""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_object(self):
        """Retourner l'utilisateur connecté."""
        return self.request.user
    
    def perform_update(self, serializer):
        """Logger la mise à jour du profil."""
        # ✅ Utiliser UserSerializer au lieu de UserProfileSerializer
        old_data = UserSerializer(self.request.user).data
        user = serializer.save()
        new_data = UserSerializer(user).data
        
        # Identifier les champs modifiés
        changed_fields = []
        for field in new_data:
            if field in old_data and old_data[field] != new_data[field]:
                changed_fields.append(field)
        
        # Logger l'activité
        log_user_activity_with_ip(
            user=user,
            activity_type='profile_updated',
            description=f'Profil mis à jour: {", ".join(changed_fields)}',
            metadata={
                'changed_fields': changed_fields,
                'old_values': {field: old_data.get(field) for field in changed_fields},
                'new_values': {field: new_data.get(field) for field in changed_fields}
            }
        )

class UserBalanceView(APIView):
    """Vue pour consulter les soldes utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir les soldes de l'utilisateur."""
        serializer = UserBalanceSerializer(request.user)
        return Response(serializer.data)


class UserStatisticsView(APIView):
    """Vue pour les statistiques utilisateur détaillées."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir les statistiques complètes de l'utilisateur."""
        serializer = UserStatisticsSerializer(request.user)
        return Response(serializer.data)


class UserActivityListView(generics.ListAPIView):
    """Vue pour lister les activités de l'utilisateur."""
    
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourner les activités de l'utilisateur connecté."""
        return UserActivity.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class UserSettingsView(generics.RetrieveUpdateAPIView):
    """Vue pour gérer les paramètres utilisateur."""
    
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Obtenir ou créer les paramètres utilisateur."""
        settings, created = UserSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings
    
    def perform_update(self, serializer):
        """Logger la mise à jour des paramètres."""
        serializer.save()
        
        log_user_activity_with_ip(
            user=self.request.user,
            activity_type='settings_updated',
            description='Paramètres mis à jour'
        )


class KYCDocumentUploadView(generics.CreateAPIView):
    """Vue pour uploader les documents KYC."""
    
    serializer_class = KYCDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @method_decorator(ratelimit(key=safe_ratelimit_key, rate='10/h', method='POST'))
    def post(self, request, *args, **kwargs):
        """Limiter les uploads KYC par utilisateur."""
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Associer le document à l'utilisateur et mettre à jour le statut KYC."""
        document = serializer.save(user=self.request.user)
        
        # Mettre à jour le statut KYC de l'utilisateur
        user = self.request.user
        if user.kyc_status == 'pending':
            user.kyc_status = 'under_review'
            user.kyc_submitted_at = timezone.now()
            user.save(update_fields=['kyc_status', 'kyc_submitted_at'])
        
        # Logger l'activité
        log_user_activity_with_ip(
            user=user,
            activity_type='kyc_document_uploaded',
            description=f'Document KYC uploadé: {document.get_document_type_display()}',
            metadata={
                'document_type': document.document_type,
                'document_id': str(document.id),
                'file_size': document.file_size
            }
        )


class KYCDocumentListView(generics.ListAPIView):
    """Vue pour lister les documents KYC de l'utilisateur."""
    
    serializer_class = KYCDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourner les documents KYC de l'utilisateur."""
        return KYCDocument.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class KYCStatusView(APIView):
    """Vue pour vérifier le statut KYC complet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir le statut KYC détaillé."""
        user = request.user
        documents = KYCDocument.objects.filter(user=user)
        
        # Calculer le pourcentage de completion
        required_docs = ['id_card', 'proof_of_address', 'selfie']
        uploaded_docs = documents.values_list('document_type', flat=True)
        completion_percentage = (
            len(set(uploaded_docs) & set(required_docs)) / len(required_docs) * 100
        )
        
        return Response({
            'kyc_status': user.kyc_status,
            'kyc_submitted_at': user.kyc_submitted_at,
            'kyc_reviewed_at': user.kyc_reviewed_at,
            'rejection_reason': user.kyc_rejection_reason if user.kyc_status == 'rejected' else None,
            'completion_percentage': completion_percentage,
            'required_documents': required_docs,
            'uploaded_documents': list(uploaded_docs),
            'documents': KYCDocumentSerializer(documents, many=True, context={'request': request}).data,
            'next_steps': self._get_next_steps(user, uploaded_docs, required_docs)
        })
    
    def _get_next_steps(self, user, uploaded_docs, required_docs):
        """Déterminer les prochaines étapes pour l'utilisateur."""
        if user.kyc_status == 'approved':
            return ['Votre vérification KYC est complète']
        elif user.kyc_status == 'rejected':
            return ['Corrigez les problèmes mentionnés et soumettez de nouveaux documents']
        else:
            missing_docs = set(required_docs) - set(uploaded_docs)
            if missing_docs:
                return [f'Uploadez votre {doc}' for doc in missing_docs]
            else:
                return ['Tous les documents requis sont uploadés. Vérification en cours.']


class EmailVerificationView(APIView):
    """Vue pour vérifier l'email utilisateur."""
    
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key=safe_ratelimit_key, rate='10/h', method='POST'))
    def post(self, request):
        """Vérifier l'email avec limitation de taux."""
        serializer = EmailVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            # Log errors pour diagnostic (dev)
            import logging
            logger = logging.getLogger(__name__)
            logger.debug('EmailVerificationSerializer errors: %s', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']

        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        from django.contrib.auth.tokens import default_token_generator

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)

            if user.is_verified:
                return Response({
                    'success': False,
                    'message': _('Email déjà vérifié')
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le token
            if not default_token_generator.check_token(user, token):
                return Response({
                    'success': False,
                    'error': _('Token invalide ou expiré')
                }, status=status.HTTP_400_BAD_REQUEST)

            # Marquer l'utilisateur comme vérifié
            user.is_verified = True
            user.save(update_fields=['is_verified'])

            # Logger l'activité
            log_user_activity_with_ip(
                user=user,
                activity_type='email_verified',
                description='Adresse email vérifiée',
                ip_address=get_client_ip(request)
            )

            return Response({
                'success': True,
                'message': _('Email vérifié avec succès')
            })

        except (User.DoesNotExist, ValueError, TypeError):
            return Response({
                'success': False,
                'error': _('Utilisateur introuvable ou lien invalide')
            }, status=status.HTTP_404_NOT_FOUND)


class PasswordChangeView(APIView):
    """Vue pour changer le mot de passe."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key=safe_ratelimit_key, rate='5/h', method='POST'))
    def post(self, request):
        """Changer le mot de passe avec limitation."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Sauvegarder le nouveau mot de passe
        user = serializer.save()
        
        # Logger l'activité
        log_user_activity_with_ip(
            user=user,
            activity_type='password_changed',
            description='Mot de passe modifié',
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'success': True,
            'message': _('Mot de passe modifié avec succès')
        })


class PasswordResetRequestView(APIView):
    """Vue pour demander la réinitialisation du mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key=safe_ratelimit_key, rate='3/h', method='POST'))
    def post(self, request):
        """Demander la réinitialisation avec limitation stricte."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Générer un token de réinitialisation
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Envoyer l'email de réinitialisation
            subject = _('Réinitialisation de votre mot de passe - RUMO RUSH')
            context = {
                'user': user,
                'reset_link': f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/",
                'site_name': 'RUMO RUSH'
            }
            message = render_to_string('emails/password_reset.html', context)
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
                fail_silently=True
            )
            
            # Logger l'activité
            log_user_activity_with_ip(
                user=user,
                activity_type='password_reset_requested',
                description='Réinitialisation de mot de passe demandée',
                ip_address=get_client_ip(request)
            )
            
        except User.DoesNotExist:
            # Ne pas révéler si l'email existe ou non
            pass
        
        # Toujours retourner la même réponse pour la sécurité
        return Response({
            'success': True,
            'message': _('Si cet email existe, un lien de réinitialisation a été envoyé')
        })


class PasswordResetConfirmView(APIView):
    """Vue pour confirmer la réinitialisation du mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Confirmer la réinitialisation."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                # Réinitialiser le mot de passe
                user.set_password(password)
                user.save()
                
                # Réinitialiser les tentatives de connexion
                user.reset_failed_login()
                
                # Logger l'activité
                log_user_activity_with_ip(
                    user=user,
                    activity_type='password_reset_completed',
                    description='Mot de passe réinitialisé avec succès',
                    ip_address=get_client_ip(request)
                )
                
                return Response({
                    'success': True,
                    'message': _('Mot de passe réinitialisé avec succès')
                })
            else:
                return Response({
                    'success': False,
                    'error': _('Token invalide ou expiré')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({
                'success': False,
                'error': _('Lien de réinitialisation invalide')
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Vue pour la déconnexion sécurisée."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Déconnexion avec blacklist du token."""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except (AttributeError, Exception):
                    # Si le blacklist échoue, on continue quand même
                    pass
            
            # Logger l'activité
            log_user_activity_with_ip(
                user=request.user,
                activity_type='logout',
                description='Déconnexion',
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'success': True,
                'message': _('Déconnexion réussie')
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': _('Erreur lors de la déconnexion'),
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """Vue pour renvoyer l'email de vérification."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key=safe_ratelimit_key, rate='3/h', method='POST'))
    def post(self, request):
        """Renvoyer l'email avec limitation."""
        user = request.user
        
        if user.is_verified:
            return Response({
                'success': True,
                'message': _('Votre email est déjà vérifié')
            }, status=status.HTTP_200_OK)
        
        try:
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://rumorush.com')
            verification_link = f"{frontend_url}/verify-email/{uid}/{token}"

            subject = _('Vérifiez votre adresse email - RUMO RUSH')
            context = {
                'user': user,
                'verification_link': verification_link,
                'site_name': 'RUMO RUSH'
            }
            message = render_to_string('emails/verify_email.html', context)

            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
                fail_silently=False
            )

            # Logger l'activité
            log_user_activity(
                user=user,
                activity_type='verification_email_resent',
                description='Email de vérification renvoyé'
            )

            return Response({
                'success': True,
                'message': _('Email de vérification envoyé')
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': _('Erreur lors de l\'envoi de l\'email')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountDeactivationView(APIView):
    """Vue pour désactiver temporairement le compte."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Désactiver le compte temporairement."""
        reason = request.data.get('reason', 'Demande utilisateur')
        
        user = request.user
        user.is_active = False
        user.save(update_fields=['is_active'])
        
        # Logger l'activité
        log_user_activity_with_ip(
            user=user,
            activity_type='account_deactivated',
            description=f'Compte désactivé: {reason}',
            metadata={'reason': reason}
        )
        
        return Response({
            'success': True,
            'message': _('Compte désactivé avec succès')
        })


# Vues utilitaires pour le debugging (en développement seulement)
if settings.DEBUG:
    
    class DebugUserInfoView(APIView):
        """Vue de debug pour obtenir des informations détaillées sur l'utilisateur."""
        
        permission_classes = [permissions.IsAuthenticated]
        
        def get(self, request):
            """Informations de debug complètes."""
            user = request.user
            
            return Response({
                'user_info': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'is_verified': user.is_verified,
                    'kyc_status': user.kyc_status,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'last_login': user.last_login,
                    'date_joined': user.created_at,
                },
                'balances': {
                    'fcfa': str(user.balance_fcfa),
                    'eur': str(user.balance_eur),
                    'usd': str(user.balance_usd),
                    'total_fcfa': str(user.total_balance_fcfa),
                },
                'security': {
                    'failed_login_attempts': user.failed_login_attempts,
                    'account_locked_until': user.account_locked_until,
                    'last_login_ip': user.last_login_ip,
                },
                'referral': {
                    'referral_code': user.referral_code,
                    'referred_by': user.referred_by.username if user.referred_by else None,
                    'total_referrals': user.referred_users.count(),
                },
                'recent_activities': UserActivitySerializer(
                    user.activities.order_by('-created_at')[:10],
                    many=True
                ).data
            })
    
    
    class DebugClearUserActivitiesView(APIView):
        """Vue de debug pour nettoyer les anciennes activités."""
        
        permission_classes = [permissions.IsAuthenticated]
        
        def delete(self, request):
            """Supprimer les anciennes activités (plus de 30 jours)."""
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            deleted_count, _ = UserActivity.objects.filter(
                user=request.user,
                created_at__lt=cutoff_date
            ).delete()
            
            return Response({
                'success': True,
                'message': f'{deleted_count} activités supprimées'
            })
