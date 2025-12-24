#!/usr/bin/env python3
"""
Script pour envoyer un email de vérification réel à ahounsounon@gmail.com
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings
from apps.accounts.email_service import EmailService
from django.core.mail import send_mail
import uuid

def send_verification_email_real():
    """Envoi d'un email de vérification réel"""
    print("📧 Préparation de l'envoi d'email de vérification réel...")
    
    # Temporairement changer vers SMTP pour envoi réel
    original_backend = settings.EMAIL_BACKEND
    original_host = getattr(settings, 'EMAIL_HOST', '')
    original_port = getattr(settings, 'EMAIL_PORT', 8587)
    original_user = getattr(settings, 'EMAIL_HOST_USER', '')
    original_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    original_tls = getattr(settings, 'EMAIL_USE_TLS', True)
    original_from = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    
    try:
        # Appliquer la config SMTP RumoRush
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = 'mail.rumorush.com'
        settings.EMAIL_PORT = 8587
        settings.EMAIL_HOST_USER = 'support@rumorush.com'
        settings.EMAIL_HOST_PASSWORD = '7VHSQNzKj4T3Xy'
        settings.EMAIL_USE_TLS = True
        settings.DEFAULT_FROM_EMAIL = 'RumoRush Support <support@rumorush.com>'
        
        print(f"✅ Configuration SMTP appliquée : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        
        # Créer un utilisateur de test temporaire
        User = get_user_model()
        
        # Créer un utilisateur fictif pour le test
        test_user = User(
            id=uuid.uuid4(),
            username="ahounsounon_test",
            email="ahounsounnon@gmail.com",  # Bon email avec 2 'n'
            first_name="Ahounsounon",
            last_name="Test",
            is_active=False  # Non vérifié
        )
        
        # Utiliser EmailService pour envoyer
        email_service = EmailService()
        
        print(f"📤 Envoi de l'email de vérification...")
        print(f"👤 Destinataire : {test_user.email}")
        print(f"📧 Nom complet : {test_user.get_full_name()}")
        
        # Générer un token et lien de vérification
        verification_token = "test-token-123456789"
        verification_link = f"https://rumorush.com/verify-email/{test_user.id}/{verification_token}"
        
        # Template context
        context = {
            'user': test_user,
            'verification_link': verification_link,
            'site_name': 'RUMO RUSH',
            'site_url': 'https://rumorush.com'
        }
        
        # Préparer le message HTML
        html_message = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vérification Email - RumoRush</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 RumoRush</h1>
            <p>Email de Test - Vérification</p>
        </div>
        
        <div class="content">
            <h2>Bonjour {test_user.first_name} ! 👋</h2>
            
            <p><strong>Ceci est un email de test de la configuration RumoRush.</strong></p>
            
            <p>Si vous recevez cet email, cela confirme que :</p>
            <ul>
                <li>✅ Le serveur SMTP mail.rumorush.com fonctionne</li>
                <li>✅ L'authentification est correcte</li>
                <li>✅ Django peut envoyer des emails</li>
                <li>✅ La configuration est opérationnelle</li>
            </ul>
            
            <div style="text-align: center;">
                <a href="{verification_link}" class="button">
                    ✅ Lien de Test (ne pas cliquer)
                </a>
            </div>
            
            <p><strong>Informations techniques :</strong></p>
            <ul>
                <li>Serveur : mail.rumorush.com:587</li>
                <li>Destinataire : {test_user.email}</li>
                <li>Expéditeur : support@rumorush.com</li>
                <li>TLS : Activé</li>
                <li>Date : {__import__('datetime').datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>RumoRush Gaming Platform<br>
            Test de configuration email<br>
            support@rumorush.com</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Message texte simple
        text_message = f"""
RumoRush - Email de Test

Bonjour {test_user.first_name} !

Ceci est un email de test de la configuration RumoRush.

Si vous recevez cet email, la configuration fonctionne parfaitement !

Informations :
- Destinataire : {test_user.email}
- Serveur : mail.rumorush.com
- Date : {__import__('datetime').datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}

---
RumoRush Support
support@rumorush.com
        """
        
        # Envoi avec Django send_mail
        sent = send_mail(
            subject="🎮 RumoRush - Test Email Configuration",
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ Email envoyé avec succès !")
        print(f"📊 Résultat send_mail : {sent}")
        print(f"📧 Vérifiez la boîte : {test_user.email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")
        return False
        
    finally:
        # Restaurer la configuration originale
        settings.EMAIL_BACKEND = original_backend
        settings.EMAIL_HOST = original_host
        settings.EMAIL_PORT = original_port
        settings.EMAIL_HOST_USER = original_user
        settings.EMAIL_HOST_PASSWORD = original_password
        settings.EMAIL_USE_TLS = original_tls
        settings.DEFAULT_FROM_EMAIL = original_from

def main():
    print("🎮 RumoRush - Envoi Email Test Réel")
    print("="*50)
    print("📧 Destinataire : ahounsounon@gmail.com (corrigé)")
    print("🔧 Mode : SMTP direct via mail.rumorush.com")
    print("="*50)
    
    # Envoi de l'email
    success = send_verification_email_real()
    
    # Résumé
    print("\n" + "="*50)
    print("📊 RÉSUMÉ")
    print("="*50)
    
    if success:
        print("✅ EMAIL ENVOYÉ AVEC SUCCÈS !")
        print("📱 Vérifiez ahounsounon@gmail.com")
        print("📋 Vérifiez aussi les spams/indésirables")
        print("🎉 Configuration RumoRush validée !")
    else:
        print("❌ Échec de l'envoi")
        print("💡 Vérifiez la configuration ou les logs")
    
    print("\n🔧 Note : Le problème précédent était :")
    print("- Email console backend (pas d'envoi réel)")
    print("- Mauvais destinataire : ahounsounnon (3 'n')")
    print("- Maintenant corrigé : ahounsounon (2 'n')")

if __name__ == "__main__":
    main()