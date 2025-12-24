# Configuration Email pour RUMO RUSH

Ce document explique comment configurer l'envoi d'emails en développement et en production.

## Principe
- En `DEBUG=True` l'application utilise par défaut le backend console (`console.EmailBackend`) : les emails sont affichés dans la console (utile pour le développement).
- En production (`DEBUG=False`) l'application essaie d'utiliser `django-anymail` (SendGrid) si une clé API est fournie. Sinon elle utilise SMTP classique configuré par les variables d'environnement.

## Variables d'environnement utiles
- `DEBUG` (True/False)
- `EMAIL_BACKEND` (optionnel) — forcer le backend complet
- `DEFAULT_FROM_EMAIL` (ex: `noreply@yourdomain.com`)

SMTP (Gmail exemple)
- `EMAIL_HOST` (ex: `smtp.gmail.com`)
- `EMAIL_PORT` (ex: `587`)
- `EMAIL_USE_TLS` (True)
- `EMAIL_USE_SSL` (False)
- `EMAIL_HOST_USER` (votre adresse email)
- `EMAIL_HOST_PASSWORD` (mot de passe SMTP / App Password Gmail)

AnyMail / SendGrid
- `SENDGRID_API_KEY` (clé API SendGrid)
- `ANYMAIL_PROVIDER` (optionnel) — ex: `sendgrid`

## Gmail (recommandé uniquement pour petits volumes)
1. Activez la validation en deux étapes sur le compte Google.
2. Créez un App Password (Mail) et utilisez-le ici comme `EMAIL_HOST_PASSWORD`.
3. Exemple `.env`:

```
DEBUG=False
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=YOUR_APP_PASSWORD
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## Postmark (recommandé pour production)
1. Créez un compte Postmark et créez un serveur.
2. Allez dans Servers → Votre serveur → API Tokens → Server API tokens.
3. Copiez le **Server API token** et définissez-le comme `POSTMARK_SERVER_TOKEN` dans `.env`.
4. Exemple `.env`:

```
DEBUG=False
EMAIL_BACKEND=anymail.backends.postmark.EmailBackend
POSTMARK_SERVER_TOKEN=your_server_api_token_here
DEFAULT_FROM_EMAIL=no-reply@yourdomain.com
```

### Étapes de vérification Postmark
- **Vérifier l'expéditeur** : Servers → Sender Signatures → vérifiez que votre adresse email / domaine est confirmé (Status = Verified).
- **Resend verification** si nécessaire (vous recevrez un email de confirmation).
- **Tester la clé** via curl :

```bash
export POSTMARK_TOKEN='your_server_api_token'
curl -i -X POST "https://api.postmarkapp.com/email" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Postmark-Server-Token: $POSTMARK_TOKEN" \
  -d '{
    "From": "no-reply@yourdomain.com",
    "To": "you@example.com",
    "Subject": "Test from RUMO RUSH",
    "TextBody": "This is a test email"
  }'
```

- 200/201 : OK. 401/422 : clé invalide, serveur incorrect, ou expéditeur non vérifié.

### Avantages Postmark
- Excellente délivrabilité.
- Dashboard avec statistiques d'envoi, bouncedmail, etc.
- Support réactif.
- Intégration simple via AnyMail.


1. Créez un compte SendGrid et générez une API key.
2. Utilisez django-anymail pour l'intégration (config déjà ajoutée).
3. Exemple `.env`:

```
DEBUG=False
EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
SENDGRID_API_KEY=SG.xxxxx
DEFAULT_FROM_EMAIL=no-reply@yourdomain.com
```

### Dépannage SendGrid: "You are not authorized to access this account"

- Erreur typique: l'API key utilisée n'a pas la permission "Mail Send" ou elle est liée à un autre compte.
- Vérifications rapides:
	- Assurez-vous que `SENDGRID_API_KEY` commence par `SG.` et qu'il s'agit bien de la clé actuelle dans votre dashboard SendGrid.
	- Dans SendGrid UI -> Settings -> API Keys, vérifiez que la clé a la permission "Full Access" ou au minimum "Mail Send".
	- Vérifiez que `DEFAULT_FROM_EMAIL` est un expéditeur vérifié (Sender Identity) ou un domaine vérifié dans SendGrid.
	- Vérifiez que le compte SendGrid n'est pas suspendu (par ex. pour dépassement de quota ou problèmes de réputation).

### Tester la clé SendGrid via curl
Vous pouvez tester la clé directement avec l'API SendGrid v3 pour isoler le problème (ne dépend pas de Django):

```bash
curl -s -X POST https://api.sendgrid.com/v3/mail/send \
	-H "Authorization: Bearer $SENDGRID_API_KEY" \
	-H "Content-Type: application/json" \
	-d '{
		"personalizations": [{"to": [{"email": "you@example.com"}], "subject": "Test"}],
		"from": {"email": "no-reply@yourdomain.com"},
		"content": [{"type": "text/plain", "value": "Test message"}]
	}'

# Si la réponse contient '"errors"' ou un message 401/403, la clé est incorrecte/insuffisante.
```

Si la commande renvoie 401/403 ou un message d'erreur "not authorized", révoquez et recréez une clé avec les permissions nécessaires et revérifiez l'expéditeur.

## Tester l'envoi d'un email
Nous avons ajouté une commande Django `send_test_email` pour tester facilement :

```bash
cd backend/
python manage.py send_test_email --to you@example.com
```

Optionnel :
```bash
python manage.py send_test_email --to you@example.com --subject "Mon sujet" --body "Mon corps"
```

Ou dans la shell Django interactive :

```bash
python manage.py shell
```

puis:

```python
from django.core.mail import send_mail
send_mail('Test RUMO RUSH', 'Corps de test', 'noreply@yourdomain.com', ['you@example.com'], fail_silently=False)
```

Si vous êtes en `DEBUG=True` le message apparaîtra dans la console. En production vous devriez recevoir l'email.


## Dépannage
- `SMTPAuthenticationError` : vérifiez `EMAIL_HOST_USER` et `EMAIL_HOST_PASSWORD`. Pour Gmail, utilisez un App Password.
- `ConnectionRefusedError` : vérifiez `EMAIL_HOST`/`EMAIL_PORT` et connectivité réseau.
- Problèmes de délivrabilité : préférez SendGrid/Mailgun/SES avec un domaine vérifié.

## Ajout de django-anymail
Une dépendance `django-anymail` a été ajoutée à `backend/requirements.txt` pour faciliter l'intégration d'API transactional email (SendGrid, Mailgun, Amazon SES, etc.).

---

Si vous voulez, je peux :
- ajouter un petit script de test (`manage.py` command) pour envoyer un email de vérification,
- ou préparer un commit et push des fichiers modifiés (`settings`, `requirements`, `.env.example`, `EMAIL_SETUP.md`).
