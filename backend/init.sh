#!/bin/bash
# 🚀 Script d'initialisation du Backend Django TKF

set -e  # Arrêter en cas d'erreur

echo "🎯 Initialisation du Backend Django TKF"
echo "======================================"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigation
cd /home/lidruf/TRANSPORT/backend

# 1. Environnement virtuel
echo -e "${BLUE}1. Création de l'environnement virtuel${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Environnement créé${NC}"
else
    echo -e "${YELLOW}✓ Environnement existe déjà${NC}"
fi

# Activation
source venv/bin/activate

# 2. Copier .env
echo -e "${BLUE}2. Configuration de l'environnement${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Fichier .env créé${NC}"
else
    echo -e "${YELLOW}✓ Fichier .env existe déjà${NC}"
fi

# 3. Installer les dépendances
echo -e "${BLUE}3. Installation des dépendances${NC}"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo -e "${GREEN}✓ Dépendances installées${NC}"

# 4. Migrations
echo -e "${BLUE}4. Initialisation de la base de données${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ Migrations appliquées${NC}"

# 5. Initialiser les rôles
echo -e "${BLUE}5. Initialisation des rôles et permissions${NC}"
python manage.py init_roles
echo -e "${GREEN}✓ Rôles créés${NC}"

# 6. Créer un superuser (optionnel)
echo -e "${BLUE}6. Création d'un superuser${NC}"
echo -e "${YELLOW}Laissez vide pour sauter...${NC}"
python manage.py createsuperuser --noinput || true

# 7. Collecter les statics
echo -e "${BLUE}7. Collecte des fichiers statiques${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Fichiers statiques collectés${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ INITIALISATION COMPLÉTÉE !             ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Pour démarrer le serveur :                ║${NC}"
echo -e "${GREEN}║  $ python manage.py runserver             ║${NC}"
echo -e "${GREEN}║                                            ║${NC}"
echo -e "${GREEN}║  Accès :                                   ║${NC}"
echo -e "${GREEN}║  API:   http://localhost:8000/api/v1/     ║${NC}"
echo -e "${GREEN}║  Admin: http://localhost:8000/admin       ║${NC}"
echo -e "${GREEN}║  Docs:  http://localhost:8000/api/v1/docs/║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
