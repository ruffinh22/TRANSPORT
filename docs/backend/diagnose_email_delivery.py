#!/usr/bin/env python
"""
Script avancé de diagnostic des problèmes d'email
"""
import os
import sys
import django
from pathlib import Path
import socket
import dns.resolver

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from email.mime.text import MIMEText
import smtplib

def check_dns_records():
    """Vérifie les enregistrements DNS du domaine"""
    print("=" * 60)
    print("VÉRIFICATION DES ENREGISTREMENTS DNS")
    print("=" * 60)
    
    domain = "rumorush.com"
    issues = []
    
    # Vérifier MX records
    print(f"\n1. Vérification des enregistrements MX pour {domain}...")
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        print("   ✓ Enregistrements MX trouvés:")
        for mx in mx_records:
            print(f"     - {mx.exchange} (priorité: {mx.preference})")
    except Exception as e:
        print(f"   ❌ Erreur MX: {e}")
        issues.append("MX records manquants ou incorrects")
    
    # Vérifier SPF record
    print(f"\n2. Vérification de l'enregistrement SPF...")
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        spf_found = False
        for txt in txt_records:
            txt_str = str(txt)
            if 'v=spf1' in txt_str.lower():
                print(f"   ✓ SPF trouvé: {txt_str}")
                spf_found = True
                break
        if not spf_found:
            print("   ❌ Aucun enregistrement SPF trouvé")
            issues.append("SPF record manquant - vos emails peuvent être marqués comme SPAM")
    except Exception as e:
        print(f"   ⚠️  Erreur SPF: {e}")
        issues.append("SPF record non vérifiable")
    
    # Vérifier DKIM
    print(f"\n3. Vérification DKIM...")
    print("   ℹ️  DKIM nécessite une configuration au niveau du serveur mail")
    print("   Vérifiez avec votre fournisseur mail.rumorush.com")
    
    # Vérifier DMARC
    print(f"\n4. Vérification de l'enregistrement DMARC...")
    try:
        dmarc_domain = f"_dmarc.{domain}"
        dmarc_records = dns.resolver.resolve(dmarc_domain, 'TXT')
        print(f"   ✓ DMARC trouvé: {dmarc_records[0]}")
    except Exception as e:
        print(f"   ❌ Aucun enregistrement DMARC trouvé")
        issues.append("DMARC record manquant - vos emails peuvent être rejetés")
    
    return issues

def send_test_email_with_headers():
    """Envoie un email avec des headers complètes pour diagnostiquer"""
    print("\n" + "=" * 60)
    print("ENVOI D'EMAIL DE TEST AVEC HEADERS COMPLÈTES")
    print("=" * 60)
    
    test_email = input("\nEntrez l'email de test: ").strip()
    if not test_email:
        print("❌ Email non fourni")
        return False
    
    try:
        subject = 'Test Email Rumo Rush - Diagnostic'
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Créer le message texte
        text_content = """
Bonjour,

Ceci est un email de test pour diagnostiquer les problèmes de délivrabilité.

Si vous recevez cet email:
✓ La configuration SMTP est correcte
✓ Les emails sont envoyés avec succès

Si cet email est dans vos SPAM:
⚠️ Il y a un problème de réputation ou de configuration DNS

Cordialement,
L'équipe Rumo Rush
"""
        
        # Créer le message HTML
        html_content = """
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #4CAF50;">Test Email - Rumo Rush</h2>
    <p>Bonjour,</p>
    <p>Ceci est un email de test pour diagnostiquer les problèmes de délivrabilité.</p>
    
    <div style="background-color: #f0f0f0; padding: 15px; margin: 20px 0; border-left: 4px solid #4CAF50;">
        <h3>Si vous recevez cet email:</h3>
        <ul>
            <li>✓ La configuration SMTP est correcte</li>
            <li>✓ Les emails sont envoyés avec succès</li>
        </ul>
    </div>
    
    <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <h3>Si cet email est dans vos SPAM:</h3>
        <ul>
            <li>⚠️ Il y a un problème de réputation ou de configuration DNS</li>
        </ul>
    </div>
    
    <p>Cordialement,<br>L'équipe Rumo Rush</p>
</body>
</html>
"""
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, [test_email])
        msg.attach_alternative(html_content, "text/html")
        
        # Ajouter des headers personnalisées
        msg.extra_headers['X-Test-Email'] = 'Rumo Rush Diagnostic'
        msg.extra_headers['Reply-To'] = from_email
        
        print(f"\nEnvoi de l'email à {test_email}...")
        msg.send(fail_silently=False)
        
        print("✅ Email envoyé avec succès !")
        print(f"\nVérifiez:")
        print(f"  1. La boîte de réception de {test_email}")
        print(f"  2. Le dossier SPAM/Courrier indésirable")
        print(f"  3. Les onglets Promotions/Réseaux sociaux (Gmail)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {type(e).__name__}: {e}")
        return False

def check_blacklist():
    """Vérifie si le domaine/IP est blacklisté"""
    print("\n" + "=" * 60)
    print("VÉRIFICATION DES BLACKLISTS")
    print("=" * 60)
    
    domain = "rumorush.com"
    mail_server = "mail.rumorush.com"
    
    print(f"\nPour vérifier si votre serveur est blacklisté:")
    print(f"\n1. Vérifiez l'IP de {mail_server}:")
    try:
        ip = socket.gethostbyname(mail_server)
        print(f"   IP: {ip}")
        print(f"\n2. Testez sur ces sites:")
        print(f"   - https://mxtoolbox.com/blacklists.aspx")
        print(f"   - https://multirbl.valli.org/lookup/{ip}.html")
        print(f"   - https://www.dnsbl.info/dnsbl-database-check.php")
    except Exception as e:
        print(f"   ❌ Impossible de résoudre l'IP: {e}")

def show_recommendations():
    """Affiche les recommandations pour améliorer la délivrabilité"""
    print("\n" + "=" * 60)
    print("RECOMMANDATIONS POUR AMÉLIORER LA DÉLIVRABILITÉ")
    print("=" * 60)
    
    print("""
1. CONFIGURATION DNS (CRITIQUE):
   • SPF: Ajoutez un enregistrement TXT pour rumorush.com:
     v=spf1 ip4:VOTRE_IP_SERVER include:mail.rumorush.com ~all
   
   • DKIM: Configurez DKIM sur votre serveur mail
     Contactez votre hébergeur pour activer DKIM
   
   • DMARC: Ajoutez un enregistrement TXT pour _dmarc.rumorush.com:
     v=DMARC1; p=quarantine; rua=mailto:dmarc@rumorush.com

2. RÉPUTATION DU SERVEUR:
   • Vérifiez que votre IP n'est pas blacklistée
   • Évitez d'envoyer trop d'emails trop rapidement
   • Commencez par de petits volumes et augmentez progressivement

3. CONTENU DES EMAILS:
   • Utilisez un ratio texte/HTML équilibré
   • Évitez les mots-clés SPAM (gratuit, gagner, urgent, etc.)
   • Incluez toujours un lien de désabonnement
   • Utilisez une vraie adresse Reply-To

4. AUTHENTIFICATION:
   • Assurez-vous que le FROM correspond au domaine configuré en SPF
   • Utilisez support@rumorush.com (déjà configuré ✓)

5. TEST ALTERNATIF:
   • Essayez d'envoyer à différents fournisseurs (Gmail, Outlook, etc.)
   • Vérifiez les headers de l'email reçu pour voir les scores SPAM

6. MONITORING:
   • Configurez des alertes pour les bounces
   • Suivez le taux de délivrabilité
   • Analysez régulièrement les logs du serveur mail
""")

if __name__ == '__main__':
    print("\n🔍 DIAGNOSTIC AVANCÉ DES PROBLÈMES D'EMAIL\n")
    
    # Vérification DNS
    try:
        dns_issues = check_dns_records()
        if dns_issues:
            print("\n⚠️  PROBLÈMES DNS DÉTECTÉS:")
            for issue in dns_issues:
                print(f"  • {issue}")
    except ImportError:
        print("\n⚠️  Module 'dnspython' non installé")
        print("Installez-le avec: pip install dnspython")
        dns_issues = ["Vérification DNS non disponible"]
    
    # Vérification blacklist
    check_blacklist()
    
    # Test d'envoi
    print("\nVoulez-vous envoyer un email de test ? (o/n): ", end='')
    response = input().strip().lower()
    if response == 'o':
        send_test_email_with_headers()
    
    # Afficher les recommandations
    show_recommendations()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC TERMINÉ")
    print("=" * 60)
