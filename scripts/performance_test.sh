#!/bin/bash
# scripts/performance_test.sh
# Test de performance et optimisation du système TKF

set -e

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== TKF Performance Testing Suite ===${NC}\n"

# 1. Vérifier les pré-requis
echo -e "${YELLOW}[1/10] Vérification des prérequis...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python non trouvé${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python trouvé: $(python --version)${NC}"

if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL CLI non trouvé (SQLite utilisé)${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL trouvé${NC}"
fi

# 2. Tester la connexion à la base de données
echo -e "\n${YELLOW}[2/10] Test de connexion à la base de données...${NC}"
cd backend
python manage.py dbshell -c "\dt" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Connexion à la base réussie${NC}"
else
    echo -e "${RED}❌ Erreur de connexion à la base${NC}"
    exit 1
fi

# 3. Vérifier les migrations
echo -e "\n${YELLOW}[3/10] Vérification de l'état des migrations...${NC}"
PENDING=$(python manage.py showmigrations --plan | grep -c "\[ \]" || true)
if [ "$PENDING" -eq 0 ]; then
    echo -e "${GREEN}✅ Toutes les migrations appliquées${NC}"
else
    echo -e "${YELLOW}⚠️  $PENDING migrations en attente${NC}"
fi

# 4. Tester les imports
echo -e "\n${YELLOW}[4/10] Test des imports Django...${NC}"
python manage.py shell -c "
from apps.employees.models import Employee
from apps.cities.models import City
from apps.trips.models import Trip
print('✅ Tous les imports réussis')
" 2>&1 | grep -q "✅"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Imports Django validés${NC}"
else
    echo -e "${RED}❌ Erreur lors des imports${NC}"
fi

# 5. Vérifier les comptes de données
echo -e "\n${YELLOW}[5/10] Vérification des données...${NC}"
python manage.py shell << EOF
from django.contrib.auth.models import User
from apps.employees.models import Employee
from apps.cities.models import City
from apps.trips.models import Trip

users = User.objects.count()
employees = Employee.objects.count()
cities = City.objects.count()
trips = Trip.objects.count()

print(f"👥 Utilisateurs: {users}")
print(f"🏢 Employés: {employees}")
print(f"🌍 Villes: {cities}")
print(f"🚌 Trajets: {trips}")
EOF

# 6. Tester les endpoints API
echo -e "\n${YELLOW}[6/10] Test des endpoints API...${NC}"
python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

ENDPOINTS=(
    "http://localhost:8000/api/v1/employees/"
    "http://localhost:8000/api/v1/cities/"
    "http://localhost:8000/api/v1/trips/"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s "$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $endpoint${NC}"
    else
        echo -e "${RED}❌ $endpoint${NC}"
    fi
done

kill $SERVER_PID 2>/dev/null || true

# 7. Tester les performances des requêtes
echo -e "\n${YELLOW}[7/10] Tests de performance des requêtes...${NC}"
python manage.py shell << EOF
import time
from django.db import connection, reset_queries
from django.conf import settings

settings.DEBUG = True
reset_queries()

from apps.employees.models import Employee
from apps.cities.models import City

# Test 1: Query sans optimisation
start = time.time()
employees = list(Employee.objects.all()[:100])
end = time.time()
print(f"⏱️  Query employees (100): {(end-start)*1000:.2f}ms")

# Test 2: Query avec select_related
reset_queries()
start = time.time()
employees = list(Employee.objects.select_related('user')[:100])
end = time.time()
print(f"⏱️  Query employees with select_related: {(end-start)*1000:.2f}ms")

# Test 3: Aggregation
reset_queries()
start = time.time()
cities = City.objects.all()
count = len(cities)
end = time.time()
print(f"⏱️  Query cities (all): {(end-start)*1000:.2f}ms (count: {count})")

print(f"\n📊 Total queries: {len(connection.queries)}")
EOF

# 8. Vérifier l'utilisation disque
echo -e "\n${YELLOW}[8/10] Vérification de l'utilisation disque...${NC}"
if [ -f "db.sqlite3" ]; then
    SIZE=$(du -h db.sqlite3 | cut -f1)
    echo -e "${GREEN}📦 Taille de la base SQLite: $SIZE${NC}"
fi

# 9. Vérifier les logs
echo -e "\n${YELLOW}[9/10] Vérification des logs...${NC}"
LOG_FILES=$(find . -name "*.log" 2>/dev/null | wc -l)
echo -e "${GREEN}📝 Fichiers de log trouvés: $LOG_FILES${NC}"

# 10. Résumé final
echo -e "\n${YELLOW}[10/10] Rapport final...${NC}"
echo -e "${BLUE}==================================${NC}"
echo -e "${GREEN}✅ Tests de performance complétés!${NC}"
echo -e "${BLUE}==================================${NC}"

echo -e "\n${YELLOW}📋 Recommandations:${NC}"
echo "1. Utiliser PostgreSQL en production pour les meilleures performances"
echo "2. Activer le cache Redis"
echo "3. Ajouter des index sur les colonnes fréquemment recherchées"
echo "4. Configurer le CDN pour les fichiers statiques"
echo "5. Utiliser Gunicorn/uWSGI au lieu du serveur de développement"

echo -e "\n${GREEN}Rapport complet généré avec succès!${NC}\n"
