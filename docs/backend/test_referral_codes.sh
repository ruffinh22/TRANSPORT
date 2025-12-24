#!/bin/bash

# 🎁 Script de test du système de codes de parrainage
# Permet de tester tous les endpoints de l'API

# Configuration
API_URL="http://localhost:8000/api/v1"
REFERRALS_URL="$API_URL/referrals"

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Fonction de test
test_endpoint() {
  local method=$1
  local endpoint=$2
  local data=$3
  local description=$4
  
  echo -e "${BLUE}🔍 Test: $description${NC}"
  
  if [ -z "$data" ]; then
    curl -X "$method" "$REFERRALS_URL$endpoint" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json"
  else
    curl -X "$method" "$REFERRALS_URL$endpoint" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$data"
  fi
  
  echo -e "\n${GREEN}✅ Test complété${NC}\n"
}

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🎯 Tests API - Codes de Parrainage${NC}"
echo -e "${BLUE}================================${NC}\n"

# Test 1: Lister les codes
test_endpoint "GET" "/codes/" "" "Lister tous les codes"

# Test 2: Créer un code
CODE_DATA='{
  "max_uses": 500,
  "expiration_date": null
}'
test_endpoint "POST" "/codes/" "$CODE_DATA" "Créer un nouveau code"

# Test 3: Obtenir les analytiques
test_endpoint "GET" "/codes/analytics/" "" "Obtenir les analytiques globales"

# Test 4: Partager un code (remplacer {id} par un vrai ID)
SHARE_DATA='{
  "channel": "whatsapp",
  "message": "Rejoins-moi sur RUMO RUSH!"
}'
test_endpoint "POST" "/codes/{id}/share/" "$SHARE_DATA" "Partager un code"

# Test 5: Obtenir les statistiques
test_endpoint "GET" "/codes/{id}/stats/" "" "Obtenir les statistiques d'\''un code"

# Test 6: Obtenir les conversions
test_endpoint "GET" "/codes/{id}/conversions/?page=1&limit=20" "" "Obtenir les conversions"

# Test 7: Générer un QR code
test_endpoint "GET" "/codes/{id}/qr-code/" "" "Générer un QR code"

# Test 8: Désactiver un code
test_endpoint "POST" "/codes/{id}/deactivate/" "" "Désactiver un code"

# Test 9: Réactiver un code
test_endpoint "POST" "/codes/{id}/activate/" "" "Réactiver un code"

echo -e "${GREEN}✨ Tous les tests sont terminés!${NC}"
