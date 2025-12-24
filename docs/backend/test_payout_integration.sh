#!/bin/bash

# Script de test pour l'intégration FeexPay Payout
# Usage: ./test_payout_integration.sh

echo "🧪 Test de l'intégration FeexPay Payout API"
echo "==========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier les variables d'environnement
echo "📋 1. Vérification des variables d'environnement..."

if [ -f .env.feexpay ]; then
    echo -e "${GREEN}✓${NC} Fichier .env.feexpay trouvé"
    source .env.feexpay
    
    if [ -z "$FEEXPAY_API_KEY" ]; then
        echo -e "${RED}✗${NC} FEEXPAY_API_KEY manquante"
        exit 1
    else
        echo -e "${GREEN}✓${NC} FEEXPAY_API_KEY configurée"
    fi
    
    if [ -z "$FEEXPAY_SHOP_ID" ]; then
        echo -e "${RED}✗${NC} FEEXPAY_SHOP_ID manquante"
        exit 1
    else
        echo -e "${GREEN}✓${NC} FEEXPAY_SHOP_ID configurée"
    fi
else
    echo -e "${RED}✗${NC} Fichier .env.feexpay non trouvé"
    echo "Créez le fichier .env.feexpay avec:"
    echo "  FEEXPAY_API_KEY=fp_live_votre_clé"
    echo "  FEEXPAY_SHOP_ID=votre_shop_id"
    exit 1
fi

echo ""

# 2. Vérifier les fichiers Python
echo "📁 2. Vérification des fichiers..."

files=(
    "apps/payments/feexpay_payout.py"
    "apps/payments/views_withdrawal.py"
    "apps/payments/tasks.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file manquant"
        exit 1
    fi
done

echo ""

# 3. Test de syntaxe Python
echo "🐍 3. Test de syntaxe Python..."

for file in "${files[@]}"; do
    python -m py_compile "$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $file - syntaxe OK"
    else
        echo -e "${RED}✗${NC} $file - erreur de syntaxe"
        python -m py_compile "$file"
        exit 1
    fi
done

echo ""

# 4. Test d'import
echo "📦 4. Test d'import des modules..."

python << EOF
try:
    from apps.payments.feexpay_payout import FeexPayPayout
    print("${GREEN}✓${NC} FeexPayPayout importé avec succès")
    
    from apps.payments.tasks import check_pending_payout_status
    print("${GREEN}✓${NC} Tâches Celery importées avec succès")
    
    # Tester l'initialisation
    payout = FeexPayPayout()
    print("${GREEN}✓${NC} Service FeexPay initialisé")
    
    # Tester les réseaux supportés
    networks = payout.get_supported_networks()
    print(f"${GREEN}✓${NC} {len(networks)} réseaux supportés")
    
except Exception as e:
    print(f"${RED}✗${NC} Erreur d'import: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""

# 5. Vérifier configuration Celery
echo "⚡ 5. Vérification configuration Celery..."

grep -q "check-pending-payouts" rumo_rush/celery.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Tâche Celery Beat configurée"
else
    echo -e "${YELLOW}⚠${NC} Tâche Celery Beat non trouvée dans celery.py"
fi

echo ""

# 6. Test de connexion API (mode test)
echo "🌐 6. Test de connexion API FeexPay..."

python << EOF
import os
import requests

api_key = os.getenv('FEEXPAY_API_KEY')
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Test simple: tenter de récupérer un status inexistant (devrait retourner 404 ou erreur propre)
try:
    response = requests.get(
        'https://api.feexpay.me/api/payouts/status/public/test',
        headers=headers,
        timeout=10
    )
    
    if response.status_code in [200, 404, 400]:
        print("${GREEN}✓${NC} API FeexPay accessible (HTTP " + str(response.status_code) + ")")
    else:
        print(f"${YELLOW}⚠${NC} Réponse API inhabituelle: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"${RED}✗${NC} Erreur connexion API: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""

# 7. Récapitulatif
echo "========================================="
echo -e "${GREEN}✅ Tous les tests sont passés !${NC}"
echo ""
echo "📝 Prochaines étapes:"
echo "  1. Lancer Django: python manage.py runserver"
echo "  2. Lancer Celery worker: celery -A rumo_rush worker -l info"
echo "  3. Lancer Celery beat: celery -A rumo_rush beat -l info"
echo "  4. Tester un retrait depuis le frontend"
echo ""
echo "📚 Documentation: backend/FEEXPAY_PAYOUT_INTEGRATION.md"
echo ""
