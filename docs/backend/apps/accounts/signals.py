# apps/accounts/signals.py
# ========================

from django.db.models.signals import (
    post_save, pre_save, post_delete, 
    pre_delete, m2m_changed
)
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from decimal import Decimal

from .models import User, KYCDocument, UserSettings
from apps.core.utils import log_user_activity, get_client_ip


# ==========================================
# 🎯 SIGNAUX DE PARRAINAGE
# ==========================================

@receiver(post_save, sender=User)
def reward_referrer_on_signup(sender, instance, created, **kwargs):
    """
    Récompenser le parrain lors de l'inscription d'un filleul.
    Bonus d'inscription : 500 FCFA
    """
    if created and instance.referred_by:
        referrer = instance.referred_by
        
        # Bonus d'inscription
        signup_bonus = Decimal('500.00')
        
        try:
            # Ajouter le bonus au parrain
            referrer.balance_fcfa += signup_bonus
            referrer.save(update_fields=['balance_fcfa'])
            
            # Logger l'activité pour le parrain
            log_user_activity(
                user=referrer,
                activity_type='referral_bonus_earned',
                description=f'🎁 Bonus de parrainage : {instance.username} s\'est inscrit',
                metadata={
                    'referred_user_id': str(instance.id),
                    'referred_username': instance.username,
                    'bonus_amount': str(signup_bonus),
                    'bonus_type': 'signup',
                    'referrer_balance_after': str(referrer.balance_fcfa)
                }
            )
            
            # Logger pour le filleul
            log_user_activity(
                user=instance,
                activity_type='referred_by',
                description=f'Parrainé par {referrer.username}',
                metadata={
                    'referrer_id': str(referrer.id),
                    'referrer_username': referrer.username,
                    'referrer_code': referrer.referral_code
                }
            )
            
            # Envoyer notification email au parrain
            send_referral_bonus_email(referrer, instance, signup_bonus)
            
            print(f"✅ Bonus de parrainage accordé : {signup_bonus} FCFA à {referrer.username}")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur lors du bonus de parrainage : {e}")


def calculate_referral_commission_rate(referrer):
    """
    Calculer le taux de commission selon le nombre de filleuls.
    
    Niveaux :
    - Starter (0-4) : 5%
    - Bronze (5-19) : 10%
    - Silver (20-49) : 15%
    - Gold (50+) : 20%
    """
    total_referrals = User.objects.filter(referred_by=referrer, is_active=True).count()
    
    if total_referrals >= 50:
        return Decimal('0.20'), 'gold', '👑'
    elif total_referrals >= 20:
        return Decimal('0.15'), 'silver', '🥈'
    elif total_referrals >= 5:
        return Decimal('0.10'), 'bronze', '🥉'
    else:
        return Decimal('0.05'), 'starter', '⭐'


@receiver(post_save, sender=User)
def check_referral_level_upgrade(sender, instance, created, **kwargs):
    """
    Vérifier si le parrain a atteint un nouveau niveau.
    Envoyer une notification si niveau supérieur atteint.
    """
    if created and instance.referred_by:
        referrer = instance.referred_by
        
        # Calculer le nouveau niveau
        commission_rate, level, icon = calculate_referral_commission_rate(referrer)
        total_referrals = User.objects.filter(referred_by=referrer, is_active=True).count()
        
        # Vérifier les paliers de niveau
        level_thresholds = {
            5: ('bronze', '🥉', 'Bronze'),
            20: ('silver', '🥈', 'Silver'),
            50: ('gold', '👑', 'Gold')
        }
        
        if total_referrals in level_thresholds:
            level_key, emoji, level_name = level_thresholds[total_referrals]
            
            # Logger le nouveau niveau
            log_user_activity(
                user=referrer,
                activity_type='referral_level_upgraded',
                description=f'{emoji} Niveau de parrainage {level_name} atteint !',
                metadata={
                    'new_level': level_key,
                    'total_referrals': total_referrals,
                    'new_commission_rate': str(commission_rate),
                    'emoji': emoji
                }
            )
            
            # Envoyer email de félicitations
            send_level_upgrade_email(referrer, level_name, commission_rate, total_referrals)
            
            print(f"🎉 {referrer.username} a atteint le niveau {level_name} !")


def send_referral_bonus_email(referrer, new_user, bonus_amount):
    """Envoyer un email au parrain pour l'informer du bonus."""
    try:
        subject = f'🎁 Nouveau filleul ! Bonus de {bonus_amount} FCFA reçu'
        context = {
            'referrer': referrer,
            'new_user': new_user,
            'bonus_amount': bonus_amount,
            'dashboard_url': f"{settings.FRONTEND_URL}/referral/",
            'site_name': 'RUMO RUSH'
        }
        
        message = render_to_string('emails/referral_bonus.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [referrer.email],
            html_message=message,
            fail_silently=True
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi email bonus parrainage : {e}")


def send_level_upgrade_email(referrer, level_name, commission_rate, total_referrals):
    """Envoyer un email de félicitations pour le nouveau niveau."""
    try:
        subject = f'🎉 Félicitations ! Niveau {level_name} atteint !'
        context = {
            'referrer': referrer,
            'level_name': level_name,
            'commission_rate': commission_rate * 100,
            'total_referrals': total_referrals,
            'referral_url': f"{settings.FRONTEND_URL}/referral/",
            'site_name': 'RUMO RUSH'
        }
        
        message = render_to_string('emails/referral_level_upgrade.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [referrer.email],
            html_message=message,
            fail_silently=True
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi email upgrade niveau : {e}")


# ==========================================
# SIGNAUX UTILISATEUR (existants)
# ==========================================

@receiver(post_save, sender=User)
def create_user_related_objects(sender, instance, created, **kwargs):
    """Créer les objets liés après création d'un utilisateur."""
    if created:
        # Créer les paramètres utilisateur par défaut
        UserSettings.objects.get_or_create(
            user=instance,
            defaults={
                'email_notifications': True,
                'sms_notifications': False,
                'push_notifications': True,
                'marketing_emails': False,
                'auto_accept_games': False,
                'show_game_tips': True,
                'sound_effects': True,
                'two_factor_enabled': False,
                'login_notifications': True
            }
        )
        
        # Logger la création du compte
        log_user_activity(
            user=instance,
            activity_type='signup',
            description='Nouveau compte créé',
            metadata={
                'country': instance.country,
                'language': instance.preferred_language,
                'has_referrer': bool(instance.referred_by),
                'referrer_code': instance.referred_by.referral_code if instance.referred_by else None
            }
        )


@receiver(post_save, sender=User)
def handle_user_verification_changes(sender, instance, created, **kwargs):
    """Gérer les changements de vérification utilisateur."""
    if not created:
        # Vérifier si l'email vient d'être vérifié
        if instance.is_verified:
            try:
                old_instance = User.objects.get(pk=instance.pk)
                if hasattr(old_instance, '_state') and not old_instance.is_verified:
                    # Email vient d'être vérifié
                    log_user_activity(
                        user=instance,
                        activity_type='email_verified',
                        description='Adresse email vérifiée'
                    )
                    
                    # Envoyer email de bienvenue
                    send_welcome_email(instance)
                    
                    # 🎁 Bonus de bienvenue pour email vérifié
                    welcome_bonus = Decimal('1000.00')
                    instance.balance_fcfa += welcome_bonus
                    instance.save(update_fields=['balance_fcfa'])
                    
                    log_user_activity(
                        user=instance,
                        activity_type='welcome_bonus_received',
                        description=f'🎁 Bonus de bienvenue : {welcome_bonus} FCFA',
                        metadata={'bonus_amount': str(welcome_bonus)}
                    )
                    
            except User.DoesNotExist:
                pass


@receiver(pre_save, sender=User)
def track_kyc_status_changes(sender, instance, **kwargs):
    """Suivre les changements de statut KYC."""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            if old_instance.kyc_status != instance.kyc_status:
                if instance.kyc_status in ['approved', 'rejected'] and not instance.kyc_reviewed_at:
                    instance.kyc_reviewed_at = timezone.now()
                
                log_user_activity(
                    user=instance,
                    activity_type='kyc_status_changed',
                    description=f'Statut KYC changé de {old_instance.kyc_status} à {instance.kyc_status}',
                    metadata={
                        'old_status': old_instance.kyc_status,
                        'new_status': instance.kyc_status,
                        'reviewed_at': instance.kyc_reviewed_at.isoformat() if instance.kyc_reviewed_at else None
                    }
                )
                
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def handle_kyc_status_notifications(sender, instance, created, **kwargs):
    """Envoyer des notifications selon le statut KYC."""
    if not created:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            if old_instance.kyc_status != 'approved' and instance.kyc_status == 'approved':
                send_kyc_approved_email(instance)
                log_user_activity(
                    user=instance,
                    activity_type='kyc_approved',
                    description='KYC approuvé - notification envoyée'
                )
            
            elif old_instance.kyc_status != 'rejected' and instance.kyc_status == 'rejected':
                send_kyc_rejected_email(instance)
                log_user_activity(
                    user=instance,
                    activity_type='kyc_rejected',
                    description='KYC rejeté - notification envoyée',
                    metadata={'rejection_reason': instance.kyc_rejection_reason}
                )
                
        except User.DoesNotExist:
            pass


@receiver(pre_save, sender=User)
def track_balance_changes(sender, instance, **kwargs):
    """Suivre les changements de solde pour audit."""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            balance_changes = {}
            
            if old_instance.balance_fcfa != instance.balance_fcfa:
                balance_changes['fcfa'] = {
                    'old': str(old_instance.balance_fcfa),
                    'new': str(instance.balance_fcfa),
                    'change': str(instance.balance_fcfa - old_instance.balance_fcfa)
                }
            
            if old_instance.balance_eur != instance.balance_eur:
                balance_changes['eur'] = {
                    'old': str(old_instance.balance_eur),
                    'new': str(instance.balance_eur),
                    'change': str(instance.balance_eur - old_instance.balance_eur)
                }
            
            if old_instance.balance_usd != instance.balance_usd:
                balance_changes['usd'] = {
                    'old': str(old_instance.balance_usd),
                    'new': str(instance.balance_usd),
                    'change': str(instance.balance_usd - old_instance.balance_usd)
                }
            
            if balance_changes:
                instance._balance_changes = balance_changes
                
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def log_balance_changes(sender, instance, created, **kwargs):
    """Logger les changements de solde après sauvegarde."""
    if not created and hasattr(instance, '_balance_changes'):
        for currency, change in instance._balance_changes.items():
            log_user_activity(
                user=instance,
                activity_type='balance_updated',
                description=f'Solde {currency.upper()} modifié: {change["change"]}',
                metadata={
                    'currency': currency,
                    'old_balance': change['old'],
                    'new_balance': change['new'],
                    'change_amount': change['change']
                }
            )
        
        delattr(instance, '_balance_changes')


# ==========================================
# SIGNAUX KYC DOCUMENTS
# ==========================================

@receiver(post_save, sender=KYCDocument)
def handle_kyc_document_upload(sender, instance, created, **kwargs):
    """Gérer l'upload de documents KYC."""
    if created:
        user = instance.user
        if user.kyc_status == 'pending':
            user.kyc_status = 'under_review'
            user.kyc_submitted_at = timezone.now()
            user.save(update_fields=['kyc_status', 'kyc_submitted_at'])
        
        log_user_activity(
            user=user,
            activity_type='kyc_document_uploaded',
            description=f'Document KYC uploadé: {instance.get_document_type_display()}',
            metadata={
                'document_type': instance.document_type,
                'document_id': str(instance.id),
                'file_size': instance.file_size,
                'original_filename': instance.original_filename
            }
        )
        
        if getattr(settings, 'NOTIFY_ADMIN_KYC_UPLOAD', False):
            notify_admin_kyc_upload(instance)


@receiver(post_save, sender=KYCDocument)
def handle_kyc_document_status_change(sender, instance, created, **kwargs):
    """Gérer les changements de statut des documents KYC."""
    if not created:
        try:
            old_instance = KYCDocument.objects.get(pk=instance.pk)
            
            if old_instance.status != instance.status:
                log_user_activity(
                    user=instance.user,
                    activity_type='kyc_document_status_changed',
                    description=f'Document {instance.get_document_type_display()} {instance.get_status_display()}',
                    metadata={
                        'document_type': instance.document_type,
                        'old_status': old_instance.status,
                        'new_status': instance.status,
                        'reviewed_by': str(instance.reviewed_by.id) if instance.reviewed_by else None
                    }
                )
                
                if instance.status == 'approved':
                    check_complete_kyc_approval(instance.user)
                    
        except KYCDocument.DoesNotExist:
            pass


@receiver(pre_delete, sender=KYCDocument)
def log_kyc_document_deletion(sender, instance, **kwargs):
    """Logger la suppression de documents KYC."""
    log_user_activity(
        user=instance.user,
        activity_type='kyc_document_deleted',
        description=f'Document KYC supprimé: {instance.get_document_type_display()}',
        metadata={
            'document_type': instance.document_type,
            'document_id': str(instance.id),
            'status': instance.status
        }
    )


# ==========================================
# SIGNAUX D'AUTHENTIFICATION
# ==========================================

@receiver(user_logged_in)
def handle_successful_login(sender, request, user, **kwargs):
    """Gérer les connexions réussies."""
    user.last_activity = timezone.now()
    user.last_login_ip = get_client_ip(request) if request else None
    user.failed_login_attempts = 0
    user.save(update_fields=['last_activity', 'last_login_ip', 'failed_login_attempts'])
    
    log_user_activity(
        user=user,
        activity_type='login',
        description='Connexion réussie',
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
        metadata={
            'login_method': 'web',
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else ''
        }
    )
    
    if hasattr(user, 'settings') and user.settings.login_notifications:
        send_login_notification(user, request)


@receiver(user_logged_out)
def handle_user_logout(sender, request, user, **kwargs):
    """Gérer les déconnexions."""
    if user:
        log_user_activity(
            user=user,
            activity_type='logout',
            description='Déconnexion',
            ip_address=get_client_ip(request) if request else None
        )


@receiver(user_login_failed)
def handle_failed_login(sender, credentials, request, **kwargs):
    """Gérer les tentatives de connexion échouées."""
    username = credentials.get('username')
    if username:
        try:
            if '@' in username:
                user = User.objects.get(email=username.lower())
            else:
                user = User.objects.get(username=username)
            
            user.failed_login_attempts += 1
            
            # Verrouiller après 5 tentatives
            if user.failed_login_attempts >= 5:
                user.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)
            
            user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
            
            log_user_activity(
                user=user,
                activity_type='login_failed',
                description='Tentative de connexion échouée',
                ip_address=get_client_ip(request) if request else None,
                metadata={
                    'failed_attempts': user.failed_login_attempts,
                    'is_locked': user.is_account_locked()
                }
            )
            
        except User.DoesNotExist:
            pass


# ==========================================
# SIGNAUX POUR LES PARAMÈTRES UTILISATEUR
# ==========================================

@receiver(post_save, sender=UserSettings)
def handle_settings_changes(sender, instance, created, **kwargs):
    """Gérer les changements de paramètres utilisateur."""
    if not created:
        log_user_activity(
            user=instance.user,
            activity_type='settings_updated',
            description='Paramètres utilisateur mis à jour'
        )


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def send_welcome_email(user):
    """Envoyer un email de bienvenue après vérification."""
    try:
        subject = f'Bienvenue sur RUMO RUSH, {user.first_name or user.username}!'
        context = {
            'user': user,
            'site_name': 'RUMO RUSH',
            'login_url': f"{settings.FRONTEND_URL}/login/"
        }
        message = render_to_string('emails/welcome.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=True
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi email bienvenue pour {user.email}: {e}")


def send_kyc_approved_email(user):
    """Envoyer un email de KYC approuvé."""
    try:
        subject = 'Votre vérification KYC a été approuvée - RUMO RUSH'
        context = {
            'user': user,
            'site_name': 'RUMO RUSH',
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard/"
        }
        message = render_to_string('emails/kyc_approved.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=True
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi email KYC approuvé pour {user.email}: {e}")


def send_kyc_rejected_email(user):
    """Envoyer un email de KYC rejeté."""
    try:
        subject = 'Votre vérification KYC nécessite des corrections - RUMO RUSH'
        context = {
            'user': user,
            'rejection_reason': user.kyc_rejection_reason,
            'site_name': 'RUMO RUSH',
            'kyc_url': f"{settings.FRONTEND_URL}/kyc/"
        }
        message = render_to_string('emails/kyc_rejected.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=True
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi email KYC rejeté pour {user.email}: {e}")


def send_login_notification(user, request):
    """Envoyer une notification de connexion."""
    try:
        current_ip = get_client_ip(request) if request else None
        if current_ip == user.last_login_ip:
            return
        
        subject = 'Nouvelle connexion détectée - RUMO RUSH'
        context = {
            'user': user,
            'ip_address': current_ip,
            'timestamp': timezone.now(),
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
            'site_name': 'RUMO RUSH'
        }
        message = render_to_string('emails/login_notification.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=True
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi notification connexion pour {user.email}: {e}")


def notify_admin_kyc_upload(document):
    """Notifier les administrateurs d'un nouvel upload KYC."""
    try:
        admin_emails = User.objects.filter(
            is_staff=True, 
            is_active=True
        ).values_list('email', flat=True)
        
        if admin_emails:
            subject = f'Nouveau document KYC - {document.user.username}'
            context = {
                'document': document,
                'user': document.user,
                'admin_url': f"{settings.BACKEND_URL}/admin/accounts/kycdocument/{document.id}/change/"
            }
            message = render_to_string('emails/admin_kyc_notification.html', context)
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                list(admin_emails),
                html_message=message,
                fail_silently=True
            )
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur notification admin KYC: {e}")


def check_complete_kyc_approval(user):
    """Vérifier si l'utilisateur a tous ses documents KYC approuvés."""
    required_docs = ['id_card', 'proof_of_address', 'selfie']
    
    approved_docs = KYCDocument.objects.filter(
        user=user,
        status='approved'
    ).values_list('document_type', flat=True)
    
    if all(doc_type in approved_docs for doc_type in required_docs):
        if user.kyc_status != 'approved':
            user.kyc_status = 'approved'
            user.kyc_reviewed_at = timezone.now()
            user.save(update_fields=['kyc_status', 'kyc_reviewed_at'])
            
            log_user_activity(
                user=user,
                activity_type='kyc_completed',
                description='Vérification KYC complétée avec succès'
            )


@receiver(post_save, sender=User)
def schedule_maintenance_tasks(sender, instance, created, **kwargs):
    """Programmer des tâches de maintenance si nécessaire."""
    if created:
        log_user_activity(
            user=instance,
            activity_type='maintenance_scheduled',
            description='Tâches de maintenance programmées pour ce compte'
        ) 
