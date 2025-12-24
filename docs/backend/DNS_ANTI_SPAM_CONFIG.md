# Configuration DNS Anti-Spam pour RumoRush
# ==========================================

# 1. ENREGISTREMENT SPF (Sender Policy Framework)
# Ajouter cet enregistrement TXT dans votre DNS rumorush.com :

TXT: v=spf1 include:mail.rumorush.com ~all

# 2. ENREGISTREMENT DKIM (DomainKeys Identified Mail)
# Demander à votre hébergeur mail.rumorush.com la clé publique DKIM
# Puis ajouter un enregistrement TXT comme :

default._domainkey.rumorush.com TXT: v=DKIM1; k=rsa; p=VOTRE_CLE_PUBLIQUE_DKIM

# 3. ENREGISTREMENT DMARC (Domain-based Message Authentication)
# Ajouter cet enregistrement TXT :

_dmarc.rumorush.com TXT: v=DMARC1; p=quarantine; rua=mailto:dmarc@rumorush.com

# 4. REVERSE DNS (PTR)
# Demander à votre hébergeur de configurer le reverse DNS pour l'IP du serveur
# mail.rumorush.com -> IP serveur -> mail.rumorush.com

# 5. MX RECORD (déjà configuré normalement)
rumorush.com MX: 10 mail.rumorush.com

# INSTRUCTIONS :
# 1. Accédez à votre panneau DNS (Cloudflare, OVH, etc.)
# 2. Ajoutez ces enregistrements TXT
# 3. Attendez la propagation DNS (24-48h)
# 4. Testez avec mail-tester.com