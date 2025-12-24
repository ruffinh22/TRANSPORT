# Configuration DNS Postmark pour akasigroup.com

## Vue d'ensemble
Pour que Postmark puisse envoyer des emails depuis le domaine `akasigroup.com`, vous devez ajouter deux enregistrements DNS chez votre fournisseur DNS :
1. **Enregistrement DKIM** (TXT)
2. **Enregistrement Return-Path** (CNAME)

Cela prend généralement **24-48 heures** pour que les changements se propagent.

---

## Instructions pas à pas

### Étape 1: Accéder à votre fournisseur DNS

Connectez-vous à votre fournisseur DNS (ex: Namecheap, GoDaddy, OVH, AWS Route53, Cloudflare, etc.).

Cherchez la section **DNS Management** ou **DNS Records**.

---

### Étape 2: Ajouter l'enregistrement DKIM

**Type d'enregistrement**: `TXT`

**Hostname / Subdomain**:
```
20251115070146pm._domainkey
```

**Valeur**:
```
k=rsa;p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCQk9VwZdWsT+zLg4t/i1igiu3iigyVCmGqCBawWeS2KOStYBZFZo48knS8HqCMEwnGz+9Ew6Uhpf+UXEf6+F8WeCbGUjSlWp5P2gR174zWa7QwRBZ61ruEeBgBKgef/3C7WqWDxUfIR0zq+prUVf7OsY3B3uFsSxKJc+sKqg52rwIDAQAB
```

**TTL** (Time To Live): `3600` (par défaut)

**Exemple dans différents providers**:

#### Namecheap
1. Connectez-vous à Namecheap
2. Allez à **Domain List** → Votre domaine → **Manage**
3. Onglet **Advanced DNS**
4. Cliquez **Add New Record**
5. Type: `TXT Record`
6. Host: `20251115070146pm._domainkey`
7. Value: Collez la clé RSA ci-dessus
8. TTL: `3600`
9. Cliquez **Save**

#### GoDaddy
1. Connectez-vous à GoDaddy
2. Allez à **My Products** → Votre domaine
3. Cliquez **Manage DNS**
4. Cliquez **Add Record**
5. Type: `TXT`
6. Name: `20251115070146pm._domainkey`
7. Value: Collez la clé RSA
8. TTL: `3600`
9. Cliquez **Save**

#### Cloudflare
1. Connectez-vous à Cloudflare
2. Sélectionnez le domaine
3. Onglet **DNS**
4. Cliquez **Add record**
5. Type: `TXT`
6. Name: `20251115070146pm._domainkey`
7. Content: Collez la clé RSA
8. TTL: `Auto`
9. Cliquez **Save**

#### AWS Route 53
1. Connectez-vous à AWS Console
2. Allez à **Route 53** → **Hosted Zones**
3. Sélectionnez `akasigroup.com`
4. Cliquez **Create record**
5. Record name: `20251115070146pm._domainkey.akasigroup.com`
6. Record type: `TXT`
7. Value: Collez la clé RSA (entre guillemets)
8. Cliquez **Create records**

---

### Étape 3: Ajouter l'enregistrement Return-Path

**Type d'enregistrement**: `CNAME`

**Hostname / Subdomain**:
```
pm-bounces
```

**Valeur / Target**:
```
pm.mtasv.net
```

**TTL**: `3600` (par défaut)

**Exemple dans différents providers**:

#### Namecheap
1. Onglet **Advanced DNS**
2. Cliquez **Add New Record**
3. Type: `CNAME Record`
4. Host: `pm-bounces`
5. Value: `pm.mtasv.net`
6. TTL: `3600`
7. Cliquez **Save**

#### GoDaddy
1. Cliquez **Add Record**
2. Type: `CNAME`
3. Name: `pm-bounces`
4. Value: `pm.mtasv.net`
5. TTL: `3600`
6. Cliquez **Save**

#### Cloudflare
1. Cliquez **Add record**
2. Type: `CNAME`
3. Name: `pm-bounces`
4. Target: `pm.mtasv.net`
5. TTL: `Auto`
6. Cliquez **Save**

#### AWS Route 53
1. Cliquez **Create record**
2. Record name: `pm-bounces.akasigroup.com`
3. Record type: `CNAME`
4. Value: `pm.mtasv.net`
5. Cliquez **Create records**

---

## Vérification

Après avoir ajouté les enregistrements DNS :

1. Retournez au **Postmark Dashboard**
2. Allez à **Servers** → Votre serveur RUMO RUSH
3. Onglet **Sender Signatures**
4. Postmark va vérifier automatiquement (cela peut prendre 5 minutes à 48 heures)
5. Une fois vérifié, le statut passera de `Unverified` à `Verified` ✅

---

## Troubleshooting

### "We couldn't find your DKIM record"
- Vérifiez que le hostname est **exactement**: `20251115070146pm._domainkey`
- Vérifiez que c'est un enregistrement **TXT** (pas A, AAAA, etc.)
- Attendez 24-48 heures pour la propagation DNS
- Testez avec: `dig 20251115070146pm._domainkey.akasigroup.com TXT` (terminal Linux/Mac)

### "We couldn't find your Return-Path record"
- Vérifiez que le hostname est **exactement**: `pm-bounces`
- Vérifiez que c'est un enregistrement **CNAME** (pas A, TXT, etc.)
- Vérifiez que la valeur est **exactement**: `pm.mtasv.net`
- Attendez 24-48 heures pour la propagation DNS
- Testez avec: `dig pm-bounces.akasigroup.com CNAME` (terminal Linux/Mac)

---

## Une fois les DNS configurés

Une fois les enregistrements DNS vérifiés dans Postmark:

1. L'adresse `noreply@akasigroup.com` sera activée
2. Vous pouvez relancer le test d'envoi:

```bash
cd /home/lidruf/rhumo_rush/backend
python manage.py send_test_email --to votre.email@gmail.com
```

3. L'email devrait être envoyé avec succès! ✅

---

## Configuration Django

Votre `.env` est maintenant configuré:
- `EMAIL_BACKEND=anymail.backends.postmark.EmailBackend`
- `POSTMARK_SERVER_TOKEN=d624c8ed-79c0-4c9a-bdd9-e710ecad2ef0`
- `DEFAULT_FROM_EMAIL=noreply@akasigroup.com`

Les emails de confirmation et transactionnels utiliseront Postmark. 🎉
