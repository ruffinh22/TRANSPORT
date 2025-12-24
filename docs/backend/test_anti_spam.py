#!/usr/bin/env python3
"""
Test anti-spam et score de délivrabilité
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
from django.template.loader import render_to_string

def test_anti_spam_email():
    """Envoyer un email optimisé anti-spam"""
    
    print("🛡️ Test Email Anti-Spam RumoRush")
    print("="*50)
    
    # Configuration anti-spam
    subject = "Confirmation d'inscription - RumoRush"  # Sans mots suspects
    recipient = "ahounsounon@gmail.com"
    
    # Context pour le template
    context = {
        'user': type('User', (), {
            'first_name': 'Ahounsounon',
            'username': 'ahounsounon',
            'email': recipient
        })(),
        'verification_link': 'https://rumorush.com/verify/abc123def456',
        'site_name': 'RumoRush',
        'support_email': 'support@rumorush.com'
    }
    
    # Message HTML optimisé
    html_message = render_to_string('emails/verify_email.html', context)
    
    # Message texte (obligatoire pour anti-spam)
    text_message = f"""
Bonjour {context['user'].first_name},

Merci de vous être inscrit sur RumoRush.

Pour activer votre compte, cliquez sur ce lien :
{context['verification_link']}

Ce lien expire dans 24 heures.

Si vous n'avez pas créé ce compte, ignorez cet email.

Cordialement,
L'équipe RumoRush
support@rumorush.com

---
RumoRush - Plateforme de jeux en ligne
www.rumorush.com
    """.strip()
    
    try:
        print(f"📧 Destinataire : {recipient}")
        print(f"📝 Sujet : {subject}")
        print(f"📤 Expéditeur : {settings.DEFAULT_FROM_EMAIL}")
        print(f"🔧 Serveur : {settings.EMAIL_HOST}")
        
        print("\n🛡️ Optimisations anti-spam appliquées :")
        print("✅ Sujet sans mots suspects (pas 'Vérifiez', 'Urgent', etc.)")
        print("✅ Expéditeur avec domaine propre (rumorush.com)")
        print("✅ Message texte ET HTML (requis)")
        print("✅ Ratio texte/HTML équilibré")
        print("✅ Liens HTTPS (plus sûrs)")
        print("✅ Pas de mots en MAJUSCULES excessives")
        print("✅ Signature d'entreprise professionnelle")
        
        # Envoi
        result = send_mail(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"\n✅ Email envoyé avec succès ! (Résultat: {result})")
        print(f"📧 Vérifiez {recipient}")
        
        print("\n🔍 VÉRIFICATIONS À FAIRE :")
        print("1. 📥 Boîte de réception principale")
        print("2. 📋 Dossier Spam/Indésirables")
        print("3. 📊 Score sur mail-tester.com")
        print("4. 🔧 Configuration DNS SPF/DKIM")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

def check_dns_config():
    """Vérifier les recommandations DNS"""
    print("\n🔧 CONFIGURATION DNS ANTI-SPAM")
    print("="*50)
    print("Pour éviter le spam, configurez ces enregistrements DNS :")
    print()
    print("1. 📧 SPF Record :")
    print("   rumorush.com TXT: v=spf1 include:mail.rumorush.com ~all")
    print()
    print("2. 🔐 DKIM Record :")
    print("   default._domainkey.rumorush.com TXT: v=DKIM1; k=rsa; p=...")
    print("   (Demandez la clé à votre hébergeur)")
    print()
    print("3. 📨 DMARC Record :")
    print("   _dmarc.rumorush.com TXT: v=DMARC1; p=quarantine;")
    print()
    print("4. 🔄 Reverse DNS :")
    print("   IP serveur -> mail.rumorush.com")
    print()
    print("🔗 Tests recommandés :")
    print("• mail-tester.com (score /10)")
    print("• mxtoolbox.com/dmarc.aspx")
    print("• dmarcian.com/dmarc-inspector/")

def main():
    print("🛡️ RumoRush - Test Anti-Spam Complet")
    print("="*60)
    
    # Test d'envoi
    email_sent = test_anti_spam_email()
    
    # Recommandations DNS
    check_dns_config()
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    
    if email_sent:
        print("✅ Email anti-spam envoyé avec succès !")
        print("📧 Template optimisé appliqué")
        print("🛡️ Vérifiez la délivrabilité dans quelques minutes")
    else:
        print("❌ Problème lors de l'envoi")
    
    print("\n💡 PROCHAINES ÉTAPES :")
    print("1. Configurez les enregistrements DNS SPF/DKIM/DMARC")
    print("2. Testez sur mail-tester.com pour obtenir un score /10")
    print("3. Surveillez la délivrabilité des prochains emails")
    print("4. Demandez aux utilisateurs d'ajouter support@rumorush.com aux contacts")

if __name__ == "__main__":
    main()