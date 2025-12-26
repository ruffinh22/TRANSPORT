#!/bin/bash

# Script de Build Production
# Usage: ./build.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🔨 BUILD TKF - Environment: $ENVIRONMENT"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}1. Vérification des prérequis...${NC}"
command -v python3.12 >/dev/null 2>&1 || { echo -e "${RED}Python 3.12 non trouvé${NC}"; exit 1; }
command -v yarn >/dev/null 2>&1 || { echo -e "${RED}Yarn non trouvé${NC}"; exit 1; }
echo -e "${GREEN}✓ Prérequis OK${NC}"

# Frontend Build
echo -e "${YELLOW}2. Build Frontend...${NC}"
cd "$ROOT_DIR/frontend"
yarn install
yarn build
echo -e "${GREEN}✓ Frontend build OK ($(du -sh dist | cut -f1))${NC}"

# Backend Setup
echo -e "${YELLOW}3. Setup Backend...${NC}"
cd "$ROOT_DIR/backend"

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "  Créating virtual environment..."
    python3.12 -m venv venv
fi

source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

if [ "$ENVIRONMENT" == "prod" ]; then
    pip install gunicorn whitenoise psycopg2-binary
fi

echo -e "${GREEN}✓ Backend setup OK${NC}"

# Migrations
echo -e "${YELLOW}4. Migrations BD...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ Migrations OK${NC}"

# Static Files
echo -e "${YELLOW}5. Collecte des fichiers statiques...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Static files OK${NC}"

# Build Info
echo -e "${YELLOW}6. Infos de build...${NC}"
BUILD_TIME=$(date '+%Y-%m-%d %H:%M:%S')
BUILD_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

cat > .build-info << EOF
BUILD_TIME=$BUILD_TIME
BUILD_HASH=$BUILD_HASH
BUILD_BRANCH=$BUILD_BRANCH
ENVIRONMENT=$ENVIRONMENT
EOF

echo "  Build Time: $BUILD_TIME"
echo "  Git Hash: $BUILD_HASH"
echo "  Branch: $BUILD_BRANCH"
echo -e "${GREEN}✓ Build info OK${NC}"

# Summary
echo ""
echo -e "${GREEN}=================================================="
echo "✓ BUILD RÉUSSI!"
echo "=================================================="
echo ""
echo "Frontend dist: $ROOT_DIR/frontend/dist"
echo "Backend venv: $ROOT_DIR/backend/venv"
echo "Environment: $ENVIRONMENT"
echo ""

if [ "$ENVIRONMENT" == "prod" ]; then
    echo "Pour démarrer en production:"
    echo "  cd $ROOT_DIR/backend"
    echo "  source venv/bin/activate"
    echo "  gunicorn config.wsgi:application --bind 0.0.0.0:8000"
else
    echo "Pour démarrer en développement:"
    echo "  Terminal 1:"
    echo "    cd $ROOT_DIR/backend"
    echo "    source venv/bin/activate"
    echo "    python manage.py runserver"
    echo ""
    echo "  Terminal 2:"
    echo "    cd $ROOT_DIR/frontend"
    echo "    yarn dev"
fi

echo ""
