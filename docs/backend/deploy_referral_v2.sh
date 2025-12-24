#!/bin/bash

# ==============================================================================
# SCRIPT DE DÉPLOIEMENT SYSTÈME PARRAINAGE V2
# Déploie la correction du système de commission (10% de 14% = 1.4%)
# ==============================================================================

set -e  # Arrêter si erreur

echo "=================================================="
echo "🚀 DÉPLOIEMENT SYSTÈME PARRAINAGE V2 (CORRIGÉ)"
echo "=================================================="
echo ""

# Vérifier que nous sommes dans le répertoire backend
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé"
    echo "Exécutez ce script depuis le répertoire backend/"
    exit 1
fi

echo "✅ Répertoire backend détecté"
echo ""

# Étape 1: Vérifier la migration
echo "=================================================="
echo "1️⃣  VÉRIFICATION DE LA MIGRATION"
echo "=================================================="
echo ""

if [ -f "apps/referrals/migrations/0002_update_referral_system.py" ]; then
    echo "✅ Migration trouvée: 0002_update_referral_system.py"
else
    echo "⚠️  Migration non trouvée"
    echo "📝 Création de la migration..."
    python manage.py makemigrations referrals
fi

echo ""

# Étape 2: Appliquer les migrations
echo "=================================================="
echo "2️⃣  APPLICATION DES MIGRATIONS"
echo "=================================================="
echo ""

echo "Vérification des migrations en attente..."
python manage.py migrate referrals --dry-run

echo ""
echo "Application des migrations..."
python manage.py migrate referrals

echo "✅ Migrations appliquées"
echo ""

# Étape 3: Exécuter les tests
echo "=================================================="
echo "3️⃣  EXÉCUTION DES TESTS"
echo "=================================================="
echo ""

echo "Lancement des tests du système de parrainage V2..."
python manage.py test apps.referrals.test_referral_system_v2 -v 2

echo ""
echo "✅ Tests complétés"
echo ""

# Étape 4: Afficher le résumé
echo "=================================================="
echo "4️⃣  RÉSUMÉ DE DÉPLOIEMENT"
echo "=================================================="
echo ""

echo "✅ DÉPLOIEMENT COMPLÉTÉ AVEC SUCCÈS"
echo ""
echo "📝 CHANGEMENTS:"
echo "  - ✅ Commission = Mise × 14% × 10% = Mise × 1.4%"
echo "  - ✅ Parrain Premium: Commission ILLIMITÉE"
echo "  - ✅ Parrain Non-Premium: Commission 3 parties MAX"
echo "  - ✅ Tests V2 ajoutés et passants"
echo ""

echo "🔌 INTÉGRATION REQUISE:"
echo ""
echo "Dans votre code de fin de partie:"
echo ""
echo "  from apps.referrals.services import ReferralCommissionService"
echo "  from decimal import Decimal"
echo ""
echo "  # Après une victoire"
echo "  result = ReferralCommissionService.process_game_referral_commission("
echo "      game=game,"
echo "      winner_user=winner,"
echo "      game_bet_amount=mise_initiale,  # ← IMPORTANTE: la MISE, pas les gains"
echo "      is_win=True"
echo "  )"
echo ""
echo "  if result['status'] == 'success':"
echo "      # Ajouter la commission au portefeuille du parrain"
echo "      referrer = result['referrer_username']"
echo "      commission = result['commission']"
echo ""

echo "=================================================="
echo "✨ PRÊT POUR LA PRODUCTION"
echo "=================================================="
