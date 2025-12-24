#!/usr/bin/env python
"""
Script de diagnostic de la configuration email
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

import smtplib
from email.mime.text import MIMEText
from django.conf import settings
from django.core.mail import send_mail

def test_smtp_connection():
    """Test la connexion SMTP directe"""
    print("=" * 60)
    print("TEST DE CONNEXION SMTP")
    print("=" * 60)
    
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    user = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    use_tls = settings.EMAIL_USE_TLS
    
    print(f"\nConfiguration actuelle:")
    print(f"  HOST: {host}")
    print(f"  PORT: {port}")
    print(f"  USER: {user}")
    print(f"  PASSWORD: {'*' * len(password) if password else 'NON DÉFINI'}")
    print(f"  USE_TLS: {use_tls}")
    print(f"  FROM: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        print(f"\n1. Connexion au serveur SMTP {host}:{port}...")
        
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            print("   ✓ Connexion établie")
            
            print("2. Démarrage TLS...")
            server.starttls()
            print("   ✓ TLS activé")
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            print("   ✓ Connexion établie (sans TLS)")
        
        print("3. Authentification...")
        server.login(user, password)
        print("   ✓ Authentification réussie")
        
        server.quit()
        print("\n✅ TOUS LES TESTS SMTP ONT RÉUSSI !")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ ERREUR D'AUTHENTIFICATION: {e}")
        print("\nVérifiez:")
        print("  - Le nom d'utilisateur EMAIL_HOST_USER")
        print("  - Le mot de passe EMAIL_HOST_PASSWORD")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ ERREUR DE CONNEXION: {e}")
        print("\nVérifiez:")
        print("  - L'adresse du serveur EMAIL_HOST")
        print("  - Le port EMAIL_PORT")
        print("  - Que le serveur est accessible depuis votre machine")
        return False
        
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {type(e).__name__}: {e}")
        return False

def test_django_email():
    """Test l'envoi d'email via Django"""
    print("\n" + "=" * 60)
    print("TEST D'ENVOI D'EMAIL VIA DJANGO")
    print("=" * 60)
    
    test_email = input("\nEntrez l'email de test pour recevoir un message: ").strip()
    
    if not test_email:
        print("❌ Email non fourni, test annulé")
        return False
    
    try:
        print(f"\nEnvoi d'un email de test à {test_email}...")
        
        send_mail(
            subject='Test Email - Rumo Rush',
            message='Ceci est un email de test pour vérifier la configuration email de Rumo Rush.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        print("✅ Email envoyé avec succès via Django !")
        print(f"\nVérifiez la boîte de réception de {test_email}")
        print("N'oubliez pas de vérifier le dossier SPAM/Courrier indésirable")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR LORS DE L'ENVOI: {type(e).__name__}: {e}")
        return False

def check_email_settings():
    """Vérifie les paramètres email"""
    print("\n" + "=" * 60)
    print("VÉRIFICATION DE LA CONFIGURATION")
    print("=" * 60)
    
    issues = []
    
    if not settings.EMAIL_HOST_USER:
        issues.append("❌ EMAIL_HOST_USER n'est pas défini")
    
    if not settings.EMAIL_HOST_PASSWORD:
        issues.append("❌ EMAIL_HOST_PASSWORD n'est pas défini")
    
    if settings.EMAIL_PORT == 8587:
        issues.append("⚠️  Port 8587 inhabituel (ports standards: 587 pour TLS, 465 pour SSL, 25 pour non-sécurisé)")
    
    if not settings.DEFAULT_FROM_EMAIL:
        issues.append("❌ DEFAULT_FROM_EMAIL n'est pas défini")
    
    if issues:
        print("\nProblèmes détectés:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Configuration de base OK")
        return True

if __name__ == '__main__':
    print("\n🔍 DIAGNOSTIC EMAIL - RUMO RUSH\n")
    
    # Vérification de la configuration
    config_ok = check_email_settings()
    
    if not config_ok:
        print("\n⚠️  Des problèmes de configuration ont été détectés.")
        print("Voulez-vous continuer les tests ? (o/n): ", end='')
        response = input().strip().lower()
        if response != 'o':
            sys.exit(1)
    
    # Test de connexion SMTP
    smtp_ok = test_smtp_connection()
    
    if not smtp_ok:
        print("\n❌ Le test SMTP a échoué. Corrigez les erreurs avant de continuer.")
        sys.exit(1)
    
    # Test d'envoi Django
    print("\nVoulez-vous tester l'envoi d'un email réel ? (o/n): ", end='')
    response = input().strip().lower()
    
    if response == 'o':
        django_ok = test_django_email()
        if django_ok:
            print("\n" + "=" * 60)
            print("✅ TOUS LES TESTS SONT RÉUSSIS !")
            print("=" * 60)
        else:
            sys.exit(1)
    else:
        print("\n✅ Tests terminés (envoi d'email ignoré)")
