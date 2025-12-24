#!/bin/bash
# ============================================================================
# SCRIPT D'INSTALLATION: SYSTÈME DE PARRAINAGE RUMO RUSH
# ============================================================================
# Ce script configures le système de parrainage avec les nouvelles règles:
# - Parrain Premium: 10% illimité
# - Parrain Non-Premium: 10% sur 3 victoires seulement
# - Sans parrain: aucune commission
# ============================================================================

echo "=================================================="
echo "🎯 INSTALLATION SYSTÈME DE PARRAINAGE RUMO RUSH"
echo "=================================================="
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé"
    echo "Exécutez ce script depuis le répertoire backend/"
    exit 1
fi

# ============================================================================
# 1. APPLIQUER LES MIGRATIONS
# ============================================================================
echo "📦 Étape 1: Appliquer les migrations Django..."
echo ""
python manage.py migrate referrals
if [ $? -eq 0 ]; then
    echo "✅ Migrations appliquées avec succès"
else
    echo "❌ Erreur lors de l'application des migrations"
    exit 1
fi
echo ""

# ============================================================================
# 2. CONFIGURER LE PROGRAMME DE PARRAINAGE
# ============================================================================
echo "⚙️  Étape 2: Configurer le programme de parrainage..."
echo ""
python manage.py shell << 'EOF'
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.referrals.models import ReferralProgram

# Supprimer les anciens programmes
ReferralProgram.objects.filter(is_default=True).delete()

# Créer le nouveau programme
program = ReferralProgram.objects.create(
    name='Programme de Parrainage Standard RUMO RUSH',
    description='''
Programme simplifié avec commission fixe de 10%:
- Premium (10,000 FCFA/mois): 10% ILLIMITÉE
- Non-Premium: 10% sur 3 victoires SEULEMENT
- Sans parrain: 0% (aucune commission)
    ''',
    commission_type='percentage',
    commission_rate=Decimal('10.00'),
    fixed_commission=Decimal('0.00'),
    max_commission_per_referral=Decimal('0.00'),
    max_daily_commission=Decimal('0.00'),
    max_monthly_commission=Decimal('0.00'),
    min_bet_for_commission=Decimal('100.00'),
    free_games_limit=3,
    status='active',
    is_default=True
)

print("✅ Programme créé:")
print(f"   ID: {program.id}")
print(f"   Nom: {program.name}")
print(f"   Commission: {program.commission_rate}%")
print(f"   Statut: {program.get_status_display()}")
EOF

if [ $? -eq 0 ]; then
    echo "✅ Programme configuré avec succès"
else
    echo "❌ Erreur lors de la configuration du programme"
    exit 1
fi
echo ""

# ============================================================================
# 3. EXÉCUTER LES TESTS
# ============================================================================
echo "🧪 Étape 3: Exécuter les tests..."
echo ""
python manage.py test apps.referrals.test_referral_system_new -v 2

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tous les tests sont passés!"
else
    echo ""
    echo "⚠️  Certains tests ont échoué. Consultez les erreurs ci-dessus."
fi
echo ""

# ============================================================================
# 4. AFFICHER LE RÉSUMÉ
# ============================================================================
echo "=================================================="
echo "✅ INSTALLATION COMPLÈTE!"
echo "=================================================="
echo ""
echo "🎯 RÉSUMÉ DU SYSTÈME:"
echo ""
echo "PARRAIN PREMIUM (10,000 FCFA/mois):"
echo "  └─ Commission: 10% sur TOUTES les victoires"
echo "  └─ Limite: AUCUNE (illimitée)"
echo "  └─ Exemple: Filleul gagne 5,000 FCFA → 500 FCFA pour le parrain"
echo ""
echo "PARRAIN NON-PREMIUM (GRATUIT):"
echo "  └─ Commission: 10% sur les victoires"
echo "  └─ Limite: 3 VICTOIRES SEULEMENT"
echo "  └─ Exemple:"
echo "     • 1ère victoire (5K) → 500 FCFA ✅"
echo "     • 2ème victoire (5K) → 500 FCFA ✅"
echo "     • 3ème victoire (5K) → 500 FCFA ✅"
echo "     • 4ème victoire (5K) → 0 FCFA ❌"
echo ""
echo "SANS PARRAIN:"
echo "  └─ Commission: AUCUNE (0%)"
echo ""
echo "=================================================="
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo ""
echo "1️⃣  Intégrer le service dans votre flux de jeu:"
echo "    from apps.referrals.services import ReferralCommissionService"
echo "    result = ReferralCommissionService.process_game_referral_commission(...)"
echo ""
echo "2️⃣  Consulter le guide d'intégration:"
echo "    cat REFERRAL_INTEGRATION_GUIDE.py"
echo ""
echo "3️⃣  Consulter la documentation complète:"
echo "    cat REFERRAL_SYSTEM_UPDATED.md"
echo ""
echo "4️⃣  Créer des utilisateurs de test:"
echo "    python manage.py shell < setup_test_referral_users.py"
echo ""
echo "=================================================="
echo ""
echo "✨ Système de parrainage prêt! 🎉"
