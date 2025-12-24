# apps/accounts/email_service.py
# Service d'envoi d'emails avec support Gmail et autres providers

import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

User = get_user_model()
logger = logging.getLogger(__name__)

class EmailService:
    """Service centralisé pour l'envoi d'emails"""
    
    def __init__(self):
        self.smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        self.smtp_user = getattr(settings, 'EMAIL_HOST_USER', '')
        self.smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        self.use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@rumorush.com')
    
    def send_verification_email(self, user: User, verification_token: str = None, uid: str = None) -> bool:
        """Envoyer l'email de vérification. Si `uid` et `verification_token` sont fournis,
        les inclure dans le lien pour vérification sécurisée."""
        try:
            # Générer le lien de vérification
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://rumorush.com')
            if uid and verification_token:
                verification_link = f"{frontend_url}/verify-email/{uid}/{verification_token}"
            else:
                verification_link = f"{frontend_url}/verify-email/{user.id}/"
            
            # Contexte pour le template
            context = {
                'user': user,
                'verification_link': verification_link,
                'site_name': 'RUMO RUSH',
                'support_email': 'support@rumorush.com'
            }
            
            # Rendu des templates
            subject = f"Vérifiez votre email - {context['site_name']}"
            html_content = render_to_string('emails/verify_email.html', context)
            text_content = render_to_string('emails/verify_email.txt', context)
            
            return self._send_email(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipient_list=[user.email],
                context=context
            )
            
        except Exception as e:
            logger.error(f"Erreur envoi email vérification pour {user.email}: {e}")
            return False
    
    def send_password_reset_email(self, user: User, reset_token: str, reset_uid: str) -> bool:
        """Envoyer l'email de réinitialisation de mot de passe"""
        try:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://rumorush.com')
            reset_link = f"{frontend_url}/reset-password/{reset_uid}/{reset_token}/"
            
            context = {
                'user': user,
                'reset_link': reset_link,
                'site_name': 'RUMO RUSH',
                'support_email': 'support@rumorush.com'
            }
            
            subject = f"Réinitialisation de votre mot de passe - {context['site_name']}"
            html_content = render_to_string('emails/password_reset.html', context)
            text_content = render_to_string('emails/password_reset.txt', context)
            
            return self._send_email(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipient_list=[user.email],
                context=context
            )
            
        except Exception as e:
            logger.error(f"Erreur envoi email reset pour {user.email}: {e}")
            return False
    
    def send_welcome_email(self, user: User) -> bool:
        """Envoyer l'email de bienvenue"""
        try:
            context = {
                'user': user,
                'site_name': 'RUMO RUSH',
                'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'https://rumorush.com')}/dashboard",
                'support_email': 'support@rumorush.com'
            }
            
            subject = f"Bienvenue sur {context['site_name']} ! 🎮"
            html_content = render_to_string('emails/welcome.html', context)
            text_content = render_to_string('emails/welcome.txt', context)
            
            return self._send_email(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipient_list=[user.email],
                context=context
            )
            
        except Exception as e:
            logger.error(f"Erreur envoi email bienvenue pour {user.email}: {e}")
            return False
    
    def send_login_notification(self, user: User, login_info: Dict[str, Any]) -> bool:
        """Envoyer une notification de connexion"""
        try:
            context = {
                'user': user,
                'login_info': login_info,
                'site_name': 'RUMO RUSH',
                'ip_address': login_info.get('ip_address', 'Inconnue'),
                'device_type': login_info.get('device_type', 'Inconnu'),
                'timestamp': login_info.get('timestamp'),
                'support_email': 'support@rumorush.com'
            }
            
            subject = f"Nouvelle connexion détectée - {context['site_name']}"
            html_content = render_to_string('emails/login_notification.html', context)
            text_content = render_to_string('emails/login_notification.txt', context)
            
            return self._send_email(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipient_list=[user.email],
                context=context
            )
            
        except Exception as e:
            logger.error(f"Erreur envoi notification connexion pour {user.email}: {e}")
            return False
    
    def _send_email(self, subject: str, html_content: str, text_content: str, 
                   recipient_list: List[str], context: Dict[str, Any] = None) -> bool:
        """Méthode privée pour envoyer les emails"""
        
        # Méthode 1: Utiliser Django EmailMultiAlternatives (recommandé)
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=recipient_list
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Email envoyé avec succès à {recipient_list}")
            return True
            
        except Exception as django_error:
            logger.warning(f"Échec envoi Django mail: {django_error}")
            
            # Méthode 2: Fallback avec SMTP direct
            return self._send_email_smtp_direct(subject, html_content, text_content, recipient_list)
    
    def _send_email_smtp_direct(self, subject: str, html_content: str, 
                               text_content: str, recipient_list: List[str]) -> bool:
        """Envoi direct via SMTP (fallback)"""
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipient_list)
            
            # Ajouter les parties text et HTML
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Connexion SMTP
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls(context=ssl.create_default_context())
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Authentification et envoi
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email SMTP direct envoyé avec succès à {recipient_list}")
            return True
            
        except Exception as smtp_error:
            logger.error(f"Échec envoi SMTP direct: {smtp_error}")
            return False
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Tester la configuration email"""
        test_results = {
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'smtp_user': self.smtp_user,
            'use_tls': self.use_tls,
            'connection_success': False,
            'authentication_success': False,
            'error_message': None
        }
        
        try:
            # Test de connexion
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            test_results['connection_success'] = True
            
            # Test d'authentification
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
                test_results['authentication_success'] = True
            
            server.quit()
            
        except Exception as e:
            test_results['error_message'] = str(e)
            logger.error(f"Test configuration email échoué: {e}")
        
        return test_results

# Instance globale du service
email_service = EmailService()

# Fonctions helper pour compatibilité
def send_verification_email(user: User, verification_token: str = None, uid: str = None) -> bool:
    """Helper function pour l'envoi d'email de vérification"""
    return email_service.send_verification_email(user, verification_token, uid)

def send_password_reset_email(user: User, reset_token: str, reset_uid: str) -> bool:
    """Helper function pour l'envoi d'email de reset"""
    return email_service.send_password_reset_email(user, reset_token, reset_uid)

def send_welcome_email(user: User) -> bool:
    """Helper function pour l'envoi d'email de bienvenue"""
    return email_service.send_welcome_email(user)

def send_login_notification(user: User, login_info: Dict[str, Any]) -> bool:
    """Helper function pour l'envoi de notification de connexion"""
    return email_service.send_login_notification(user, login_info)
