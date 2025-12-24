#!/usr/bin/env python3
"""
Envoi forcé d'email avec traçabilité complète
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

from django.core.mail import send_mail
from django.conf import settings
import datetime

def send_test_email_with_tracking():
    """Envoi d'email avec tracking complet"""
    
    timestamp = datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')
    
    # Email avec informations de traçabilité
    subject = f"🎮 RumoRush - Test Email {datetime.datetime.now().strftime('%H:%M:%S')}"
    
    html_message = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Test RumoRush Email</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f4f4f4; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 20px; }}
        .info {{ background: #e9f7ef; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #28a745; }}
        .tracking {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 RumoRush</h1>
            <p>Email de Test avec Traçabilité</p>
        </div>
        
        <div class="info">
            <h3>✅ Email Envoyé avec Succès !</h3>
            <p>Si vous recevez cet email, la configuration RumoRush fonctionne parfaitement.</p>
        </div>
        
        <div class="tracking">
            <h3>📊 Informations de Traçabilité</h3>
            <ul>
                <li><strong>Date/Heure :</strong> {timestamp}</li>
                <li><strong>Serveur SMTP :</strong> {settings.EMAIL_HOST}:{getattr(settings, 'EMAIL_PORT', 587)}</li>
                <li><strong>Expéditeur :</strong> {getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@rumorush.com')}</li>
                <li><strong>Destinataire :</strong> ahounsounon@gmail.com</li>
                <li><strong>Backend :</strong> {settings.EMAIL_BACKEND}</li>
                <li><strong>TLS :</strong> {'Activé' if getattr(settings, 'EMAIL_USE_TLS', False) else 'Désactivé'}</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>🔍 Que Faire si Vous ne Voyez pas cet Email ?</h3>
            <ol>
                <li>Vérifiez le <strong>dossier Spam/Indésirables</strong></li>
                <li>Vérifiez les <strong>onglets Gmail</strong> (Promotions, Social)</li>
                <li>Recherchez <strong>"RumoRush"</strong> dans Gmail</li>
                <li>Vérifiez l'<strong>adresse email exacte</strong> utilisée</li>
                <li>Patientez <strong>1-5 minutes</strong> (délai possible)</li>
            </ol>
        </div>
        
        <h3>🎯 Test des Inscriptions</h3>
        <p>Pour tester l'email d'inscription :</p>
        <ol>
            <li>Utilisez une <strong>nouvelle adresse email</strong></li>
            <li>Ou créez un compte avec un <strong>email non vérifié</strong></li>
            <li>L'email sera envoyé automatiquement</li>
        </ol>
        
        <div class="footer">
            <p>RumoRush Gaming Platform<br>
            Configuration Email Validée<br>
            support@rumorush.com</p>
            <p>Cet email confirme que le système fonctionne !</p>
        </div>
    </div>
</body>
</html>
    """
    
    text_message = f"""
RumoRush - Email de Test avec Traçabilité

✅ Email envoyé avec succès !

📊 Informations :
- Date/Heure : {timestamp}
- Serveur : {settings.EMAIL_HOST}:{getattr(settings, 'EMAIL_PORT', 587)}
- Destinataire : ahounsounon@gmail.com
- Backend : {settings.EMAIL_BACKEND}

🔍 Si vous ne voyez pas cet email :
1. Vérifiez les spams/indésirables
2. Vérifiez les onglets Gmail
3. Recherchez "RumoRush"
4. Patientez 1-5 minutes

La configuration RumoRush fonctionne parfaitement !

---
RumoRush Support
support@rumorush.com
    """
    
    try:
        print("📤 Envoi d'email de test avec traçabilité...")
        print(f"📧 Destinataire : ahounsounon@gmail.com")
        print(f"🕐 Heure : {timestamp}")
        
        result = send_mail(
            subject=subject,
            message=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@rumorush.com'),
            recipient_list=['ahounsounon@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ Email envoyé avec succès !")
        print(f"📊 Résultat Django : {result}")
        print(f"📧 Vérifiez ahounsounon@gmail.com maintenant")
        print(f"🔍 N'oubliez pas de vérifier :")
        print(f"   - Boîte de réception principale")
        print(f"   - Dossier Spam/Indésirables") 
        print(f"   - Onglets Promotions/Social")
        print(f"   - Recherche 'RumoRush' dans Gmail")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")
        return False

def main():
    print("🎮 RumoRush - Email Test avec Traçabilité Complète")
    print("="*60)
    
    success = send_test_email_with_tracking()
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    
    if success:
        print("🎉 EMAIL ENVOYÉ AVEC SUCCÈS !")
        print("⏱️ L'email devrait arriver dans 1-5 minutes")
        print("📱 Vérifiez ahounsounon@gmail.com (et tous les dossiers)")
    else:
        print("❌ Problème lors de l'envoi")
    
    print("\n💡 NOTE IMPORTANTE :")
    print("Les emails d'inscription sont envoyés automatiquement.")
    print("Si les comptes sont déjà vérifiés, pas d'email supplémentaire.")
    print("Utilisez une nouvelle adresse pour tester l'inscription.")

if __name__ == "__main__":
    main()