#!/usr/bin/env python3
"""
Diagnostic de l'envoi d'email après inscription
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

from django.conf import settings
from django.contrib.auth import get_user_model
from apps.accounts.email_service import EmailService
from django.core.mail import send_mail

def check_email_settings():
    """Vérifier la configuration email actuelle"""
    print("🔧 Configuration Email Actuelle")
    print("="*50)
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    if hasattr(settings, 'EMAIL_HOST'):
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Non défini')}")
        print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Non défini')}")
        print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Non défini')}")
        print(f"EMAIL_HOST_PASSWORD: {'***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'Non défini'}")
        print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Non défini')}")
    else:
        print("❌ Configuration SMTP manquante")
    
    return settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend'

def check_recent_users():
    """Vérifier les utilisateurs récents"""
    print("\n👥 Utilisateurs Récents")
    print("="*50)
    
    User = get_user_model()
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    for user in recent_users:
        print(f"📧 {user.email} - {user.username}")
        print(f"   Créé: {user.date_joined}")
        print(f"   Vérifié: {'✅' if user.is_active else '❌'}")
        print(f"   ID: {user.id}")
        print()

def test_email_sending():
    """Tester l'envoi d'email maintenant"""
    print("\n📧 Test d'Envoi Email Direct")
    print("="*50)
    
    try:
        result = send_mail(
            subject="🎮 Test RumoRush - Email Direct",
            message="Test d'envoi direct avec la configuration actuelle",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@rumorush.com'),
            recipient_list=['ahounsounon@gmail.com'],
            fail_silently=False,
        )
        
        print(f"✅ Email envoyé ! Résultat: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'envoi: {e}")
        return False

def check_email_service():
    """Vérifier le service email"""
    print("\n🔧 Test EmailService")
    print("="*50)
    
    try:
        email_service = EmailService()
        config = email_service.test_email_configuration()
        
        for key, value in config.items():
            status = "✅" if value else "❌"
            print(f"{status} {key}: {value}")
            
        return config.get('connection_success', False)
        
    except Exception as e:
        print(f"❌ Erreur EmailService: {e}")
        return False

def simulate_registration_email():
    """Simuler l'envoi d'email d'inscription"""
    print("\n📋 Simulation Email Inscription")
    print("="*50)
    
    try:
        User = get_user_model()
        
        # Prendre le dernier utilisateur créé
        latest_user = User.objects.order_by('-date_joined').first()
        
        if not latest_user:
            print("❌ Aucun utilisateur trouvé")
            return False
            
        print(f"👤 Utilisateur: {latest_user.email}")
        print(f"📅 Créé: {latest_user.date_joined}")
        
        # Simuler l'envoi d'email de vérification
        verification_link = f"http://localhost:5173/verify-email/{latest_user.id}/test-token"
        
        html_message = f"""
        <h1>🎮 RumoRush - Vérification Email</h1>
        <p>Bonjour {latest_user.first_name or latest_user.username} !</p>
        <p>Cliquez pour vérifier: <a href="{verification_link}">Vérifier</a></p>
        <p>Ceci est un email de test post-diagnostic.</p>
        """
        
        result = send_mail(
            subject="🎮 RumoRush - Vérification Email (Test)",
            message=f"Bonjour {latest_user.first_name or latest_user.username}!\n\nLien: {verification_link}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@rumorush.com'),
            recipient_list=[latest_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ Email de vérification envoyé ! Résultat: {result}")
        print(f"📧 Destinataire: {latest_user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur simulation: {e}")
        return False

def main():
    print("🎮 RumoRush - Diagnostic Email Post-Inscription")
    print("="*60)
    
    # Tests
    smtp_configured = check_email_settings()
    check_recent_users()
    
    if smtp_configured:
        email_service_ok = check_email_service()
        direct_send_ok = test_email_sending()
        registration_simulation_ok = simulate_registration_email()
    else:
        print("⚠️ Configuration SMTP non détectée - mode console actif")
        email_service_ok = False
        direct_send_ok = False
        registration_simulation_ok = False
    
    # Résumé
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC RÉSUMÉ")
    print("="*60)
    print(f"Configuration SMTP:    {'✅ OK' if smtp_configured else '❌ Console'}")
    print(f"EmailService:         {'✅ OK' if email_service_ok else '❌ Erreur'}")
    print(f"Envoi Direct:         {'✅ OK' if direct_send_ok else '❌ Erreur'}")
    print(f"Simulation Inscription: {'✅ OK' if registration_simulation_ok else '❌ Erreur'}")
    
    if all([smtp_configured, direct_send_ok]):
        print("\n🎉 Configuration OK - emails envoyés !")
        print("📧 Vérifiez ahounsounon@gmail.com (et spams)")
    else:
        print("\n⚠️ Problème détecté !")
        if not smtp_configured:
            print("💡 Le backend console est encore actif")
            print("🔧 Redémarrez le serveur pour appliquer les settings SMTP")
        else:
            print("💡 Problème de configuration SMTP ou réseau")

if __name__ == "__main__":
    main()