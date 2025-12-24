#!/bin/bash

# ============================================
# RUMO RUSH - Script de déploiement PRODUCTION
# ============================================

set -e  # Exit on any error

echo "🚀 Démarrage du déploiement RUMO RUSH..."

# 1. Charger les variables d'environnement
if [ ! -f .env.production ]; then
    echo "❌ Erreur: .env.production introuvable!"
    exit 1
fi

export $(cat .env.production | grep -v '^#' | xargs)

# 2. Vérifications préalables
echo "📋 Vérifications de sécurité..."

# Vérifier que DEBUG=False
if [ "$DEBUG" != "False" ]; then
    echo "❌ ERREUR: DEBUG doit être False en production!"
    exit 1
fi

# Vérifier les secrets
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "CHANGEZ_MOI_EN_PRODUCTION_AVEC_UNE_CLEF_LONGUE_ET_ALEATOIRE_MIN_50_CHARS" ]; then
    echo "❌ ERREUR: SECRET_KEY n'est pas configurée!"
    exit 1
fi

if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "CHANGEZ_MOI_MOT_DE_PASSE_DB_PRODUCTION" ]; then
    echo "❌ ERREUR: DB_PASSWORD n'est pas configurée!"
    exit 1
fi

echo "✅ Vérifications préalables réussies"

# 3. Migrations base de données
echo "📦 Exécution des migrations..."
python manage.py migrate --noinput

# 4. Collecter les fichiers statiques
echo "📂 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear

# 5. Compiler les messages de traduction
echo "🌐 Compilation des traductions..."
python manage.py compilemessages

# 6. Vérifications de sécurité Django
echo "🔒 Vérifications de sécurité Django..."
python manage.py check --deploy

# 7. Créer les répertoires de logs
echo "📝 Création des répertoires de logs..."
mkdir -p /var/log/rumorush
chmod 755 /var/log/rumorush

# 8. Nettoyer les sessions expirées
echo "🧹 Nettoyage des sessions..."
python manage.py clearsessions

# 9. Créer un superuser (optionnel - si n'existe pas)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 Création du superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@rumorush.com', '${ADMIN_PASSWORD}')
    print("✅ Superuser créé")
else:
    print("ℹ️  Superuser existe déjà")
EOF
fi

# 10. Vérifier la connexion à la base de données
echo "🗄️  Vérification de la base de données..."
python manage.py dbshell << EOF
SELECT 1;
\q
EOF

# 11. Vérifier la connexion Redis
echo "🔄 Vérification de Redis..."
python manage.py shell -c "from django.core.cache import cache; cache.set('deploy_test', 'ok', 10); assert cache.get('deploy_test') == 'ok'; print('✅ Redis OK')"

# 12. Vérifier l'envoi d'email
echo "📧 Vérification de l'envoi d'email..."
python manage.py shell -c "
from django.core.mail import send_mail
try:
    send_mail(
        'Test Déploiement RUMO RUSH',
        'Test d\\'envoi d\\'email - Déploiement réussi',
        'noreply@rumorush.com',
        ['admin@rumorush.com'],
        fail_silently=False,
    )
    print('✅ Email de test envoyé')
except Exception as e:
    print(f'⚠️  Erreur email: {e}')
"

# 13. Lancer Celery (si disponible)
if command -v celery &> /dev/null; then
    echo "⚡ Démarrage de Celery..."
    celery -A rumo_rush worker -l info --concurrency=4 --detach
    celery -A rumo_rush beat -l info --detach
    echo "✅ Celery démarré"
fi

# 14. Résumé
echo ""
echo "============================================"
echo "✅ DÉPLOIEMENT RÉUSSI!"
echo "============================================"
echo "🌐 Application: https://$(echo $ALLOWED_HOSTS | cut -d',' -f1)"
echo "🗄️  Base de données: $DB_NAME @ $DB_HOST"
echo "🔄 Cache: Redis"
echo "📧 Email: $EMAIL_HOST_USER"
echo "💳 Stripe: Configuré"
echo "📊 Monitoring: $([ -z '$SENTRY_DSN' ] && echo 'Non configuré' || echo 'Sentry activé')"
echo ""
echo "⏭️  Prochaines étapes:"
echo "1. Redémarrer le service WSGI/Gunicorn"
echo "2. Vérifier les logs: tail -f /var/log/rumorush/django.log"
echo "3. Tester l'application: https://$(echo $ALLOWED_HOSTS | cut -d',' -f1)"
echo "4. Monitorer Sentry (si configuré)"
echo "5. Vérifier les metrics/health check"
echo ""
