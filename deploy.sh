#!/bin/bash

# Script de déploiement distant
# Usage: ./deploy.sh user@host:/path/to/app

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 user@host:/path/to/app"
    echo "Example: $0 appuser@192.168.1.100:/home/appuser/tkf"
    exit 1
fi

REMOTE_PATH=$1
ENVIRONMENT=${2:-prod}
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🚀 Déploiement TKF"
echo "Target: $REMOTE_PATH"
echo "Environment: $ENVIRONMENT"
echo "=================================================="

# Build local d'abord
echo "1️⃣  Build local..."
cd "$ROOT_DIR"
./build.sh $ENVIRONMENT

# Créer archive
echo ""
echo "2️⃣  Création de l'archive..."
ARCHIVE="tkf-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$ARCHIVE" \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='.env' \
  backend/ \
  frontend/dist/ \
  manage.py \
  requirements.txt \
  .build-info

echo "Archive créée: $ARCHIVE ($(du -sh $ARCHIVE | cut -f1))"

# Envoyer au serveur
echo ""
echo "3️⃣  Envoi au serveur..."
scp "$ARCHIVE" "$REMOTE_PATH/"

# Extraire et démarrer
echo ""
echo "4️⃣  Extraction et setup..."
ssh "${REMOTE_PATH%:*}" "
  cd ${REMOTE_PATH#*:}
  tar -xzf $ARCHIVE
  cd backend
  source venv/bin/activate
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py collectstatic --noinput
"

echo ""
echo "✓ Déploiement terminé!"
echo ""
echo "Redémarrer le service:"
echo "  ssh ${REMOTE_PATH%:*} 'sudo systemctl restart tkf'"
