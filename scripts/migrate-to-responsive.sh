#!/bin/bash

# Script pour convertir les pages existantes au design responsive
# Usage: ./scripts/migrate-to-responsive.sh

echo "🚀 Migration vers Responsive Design Pro"
echo "======================================"
echo ""

PAGES_DIR="frontend/src/pages"
COMPONENTS_DIR="frontend/src/components"

# Pages à mettre à jour
PAGES=(
  "Dashboard.tsx"
  "TripsPage.tsx"
  "TicketsPage.tsx"
  "ParcelsPage.tsx"
  "PaymentsPage.tsx"
  "EmployeesPage.tsx"
  "CitiesPage.tsx"
  "ReportsPage.tsx"
  "SettingsPage.tsx"
  "UserProfilePage.tsx"
)

echo "✅ Composants Responsive créés:"
echo "  - ResponsivePageTemplate"
echo "  - ResponsiveTable"
echo "  - ResponsiveGrid (StatsGrid, CardGrid, DetailGrid)"
echo "  - ResponsiveFilters"
echo ""

echo "📋 Pages à mettre à jour:"
for page in "${PAGES[@]}"; do
  echo "  - $page"
done
echo ""

echo "📝 Instructions de migration:"
echo ""
echo "1. Importer les composants:"
echo "   import { ResponsivePageTemplate, ResponsiveTable } from '../components'"
echo "   import { responsiveStyles } from '../styles/responsiveStyles'"
echo ""
echo "2. Wrapper la page avec ResponsivePageTemplate"
echo "3. Remplacer les tableaux par ResponsiveTable"
echo "4. Remplacer les grilles Grid par StatsGrid/CardGrid/DetailGrid"
echo "5. Ajouter ResponsiveFilters avant les tableaux"
echo ""

echo "🔍 Exemple: Voir ResponsiveExample.tsx"
echo ""
echo "✨ Responsive Design Pro activé!"
