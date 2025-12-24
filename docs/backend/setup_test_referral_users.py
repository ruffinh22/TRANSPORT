#!/usr/bin/env python
"""
Script de test: Créer des utilisateurs et parrainages pour tester le système
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.referrals.models import ReferralProgram, Referral

User = get_user_model()

print("\n" + "="*60)
print("CRÉER DES UTILISATEURS DE TEST POUR PARRAINAGE")
print("="*60 + "\n")

# Nettoyer les utilisateurs de test existants
User.objects.filter(username__startswith='test_').delete()

# Obtenir le programme par défaut
program = ReferralProgram.get_default_program()
if not program:
    print("❌ Aucun programme de parrainage trouvé!")
    print("Exécutez: python install_referral_system.sh")
    exit(1)

# ============================================================================
# Scénario 1: Parrain PREMIUM avec 2 filleuls
# ============================================================================
print("SCÉNARIO 1: PARRAIN PREMIUM")
print("-" * 60)

parrain_premium = User.objects.create_user(
    username='test_premium_parrain',
    email='premium_parrain@test.com',
    password='test123',
    first_name='Parrain',
    last_name='Premium'
)
print(f"✅ Parrain Premium créé: {parrain_premium.username}")

filleul_premium_1 = User.objects.create_user(
    username='test_filleul_premium_1',
    email='filleul_premium_1@test.com',
    password='test123',
    first_name='Filleul',
    last_name='Premium1'
)
print(f"✅ Filleul 1 créé: {filleul_premium_1.username}")

filleul_premium_2 = User.objects.create_user(
    username='test_filleul_premium_2',
    email='filleul_premium_2@test.com',
    password='test123',
    first_name='Filleul',
    last_name='Premium2'
)
print(f"✅ Filleul 2 créé: {filleul_premium_2.username}")

# Créer les parrainages
ref_premium_1 = Referral.objects.create(
    referrer=parrain_premium,
    referred=filleul_premium_1,
    program=program,
    is_premium_referrer=True
)
print(f"✅ Parrainage créé: {parrain_premium.username} → {filleul_premium_1.username}")

ref_premium_2 = Referral.objects.create(
    referrer=parrain_premium,
    referred=filleul_premium_2,
    program=program,
    is_premium_referrer=True
)
print(f"✅ Parrainage créé: {parrain_premium.username} → {filleul_premium_2.username}")

print("\nCommandles de test:")
print(f"  Parrain Premium ID: {parrain_premium.id}")
print(f"  Filleul 1 ID: {filleul_premium_1.id}")
print(f"  Filleul 2 ID: {filleul_premium_2.id}")
print("")

# ============================================================================
# Scénario 2: Parrain NON-PREMIUM avec 3 filleuls
# ============================================================================
print("\nSCÉNARIO 2: PARRAIN NON-PREMIUM")
print("-" * 60)

parrain_free = User.objects.create_user(
    username='test_free_parrain',
    email='free_parrain@test.com',
    password='test123',
    first_name='Parrain',
    last_name='Gratuit'
)
print(f"✅ Parrain Non-Premium créé: {parrain_free.username}")

filleuls_free = []
for i in range(1, 4):
    filleul = User.objects.create_user(
        username=f'test_filleul_free_{i}',
        email=f'filleul_free_{i}@test.com',
        password='test123',
        first_name=f'Filleul',
        last_name=f'Gratuit{i}'
    )
    filleuls_free.append(filleul)
    print(f"✅ Filleul {i} créé: {filleul.username}")

# Créer les parrainages non-premium
refs_free = []
for i, filleul in enumerate(filleuls_free, 1):
    ref = Referral.objects.create(
        referrer=parrain_free,
        referred=filleul,
        program=program,
        is_premium_referrer=False
    )
    refs_free.append(ref)
    print(f"✅ Parrainage créé: {parrain_free.username} → {filleul.username}")

print("\nCommandes de test:")
print(f"  Parrain Non-Premium ID: {parrain_free.id}")
for i, filleul in enumerate(filleuls_free, 1):
    print(f"  Filleul {i} ID: {filleul.id}")
print("")

# ============================================================================
# Scénario 3: Joueurs SANS PARRAIN
# ============================================================================
print("\nSCÉNARIO 3: JOUEURS SANS PARRAIN")
print("-" * 60)

joueur_solo_1 = User.objects.create_user(
    username='test_joueur_solo_1',
    email='joueur_solo_1@test.com',
    password='test123',
    first_name='Joueur',
    last_name='Solo1'
)
print(f"✅ Joueur Solo 1 créé: {joueur_solo_1.username} (SANS PARRAIN)")

joueur_solo_2 = User.objects.create_user(
    username='test_joueur_solo_2',
    email='joueur_solo_2@test.com',
    password='test123',
    first_name='Joueur',
    last_name='Solo2'
)
print(f"✅ Joueur Solo 2 créé: {joueur_solo_2.username} (SANS PARRAIN)")

print("\nCommandes de test:")
print(f"  Joueur Solo 1 ID: {joueur_solo_1.id}")
print(f"  Joueur Solo 2 ID: {joueur_solo_2.id}")
print("")

# ============================================================================
# AFFICHER UN RÉSUMÉ POUR LES TESTS
# ============================================================================
print("\n" + "="*60)
print("📊 RÉSUMÉ POUR TESTS")
print("="*60 + "\n")

print("TEST 1: Parrain PREMIUM - Commission illimitée")
print("-" * 60)
print(f"Utilisateurs:")
print(f"  Parrain: {parrain_premium.username}")
print(f"  Filleul: {filleul_premium_1.username}")
print(f"\nTest:")
print(f"  1. Filleul gagne 1,000 FCFA → Parrain doit recevoir 100 FCFA")
print(f"  2. Filleul gagne 5,000 FCFA → Parrain doit recevoir 500 FCFA")
print(f"  3. Filleul gagne 10,000 FCFA → Parrain doit recevoir 1,000 FCFA")
print(f"  4. Répéter 10 fois → Chaque fois 10% est octroyé ✅")
print("")

print("TEST 2: Parrain NON-PREMIUM - Limite 3 victoires")
print("-" * 60)
print(f"Utilisateurs:")
print(f"  Parrain: {parrain_free.username}")
print(f"  Filleuls: {[f.username for f in filleuls_free]}")
print(f"\nTest:")
print(f"  1. Filleul 1 gagne 1,000 FCFA → Parrain reçoit 100 FCFA ✅ (1/3)")
print(f"  2. Filleul 1 gagne 1,000 FCFA → Parrain reçoit 100 FCFA ✅ (2/3)")
print(f"  3. Filleul 1 gagne 1,000 FCFA → Parrain reçoit 100 FCFA ✅ (3/3)")
print(f"  4. Filleul 1 gagne 1,000 FCFA → Parrain reçoit 0 FCFA ❌ (Limite atteinte)")
print("")

print("TEST 3: Joueur SANS PARRAIN - Aucune commission")
print("-" * 60)
print(f"Utilisateurs:")
print(f"  Joueur: {joueur_solo_1.username}")
print(f"\nTest:")
print(f"  1. Joueur gagne 1,000 FCFA → Aucune commission générée ✓")
print(f"  2. Joueur gagne 5,000 FCFA → Aucune commission générée ✓")
print("")

# ============================================================================
# CODE POUR TESTER LES COMMISSIONS
# ============================================================================
print("\n" + "="*60)
print("CODE POUR TESTER LES COMMISSIONS")
print("="*60 + "\n")

print("""
# Exemple 1: Tester une commission premium
from apps.referrals.models import Referral
from decimal import Decimal
from apps.referrals.services import ReferralCommissionService

# Obtenir le parrainage
ref = Referral.objects.get(
    referrer__username='test_premium_parrain',
    referred__username='test_filleul_premium_1'
)

# Vérifier que la commission peut être gagnée
can_earn, msg = ref.can_earn_commission(game_won=True)
print(f"Peut gagner commission: {can_earn}")  # Should be True

# Calculer la commission pour 1,000 FCFA
commission, msg = ref.calculate_commission(
    game_amount=Decimal('1000.00'),
    game_won=True
)
print(f"Commission: {commission} FCFA")  # Should be 100.00

# Exemple 2: Tester une commission non-premium
ref = Referral.objects.get(
    referrer__username='test_free_parrain',
    referred__username='test_filleul_free_1'
)

# Première victoire: ✅ Commission
can_earn, msg = ref.can_earn_commission(game_won=True)
commission, msg = ref.calculate_commission(Decimal('1000.00'), game_won=True)
print(f"Victoire 1: {commission} FCFA")  # 100.00

# Mettre à jour les stats
ref.update_stats(game_won=True, commission_amount=commission)
ref.refresh_from_db()
print(f"Compteur: {ref.winning_games_count}/3")

# Après 3 victoires
ref.winning_games_count = 3
ref.save()

can_earn, msg = ref.can_earn_commission(game_won=True)
print(f"4ème victoire possible: {can_earn}")  # Should be False

# Exemple 3: Tester un joueur sans parrain
from apps.referrals.services import ReferralCommissionService

summary = ReferralCommissionService.get_referral_summary(joueur_solo_1)
print(f"Has referrer: {summary['has_referrer']}")  # False
""")

print("\n" + "="*60)
print("✅ UTILISATEURS DE TEST CRÉÉS!")
print("="*60 + "\n")

print("Vous pouvez maintenant:")
print("1. Vous connecter avec ces utilisateurs")
print("2. Tester les commissions de parrainage")
print("3. Vérifier le dashboard du parrain")
print("4. Voir les commissions s'appliquer sur les victoires")
print("")
print("Logins de test:")
print(f"  Parrain Premium: test_premium_parrain / test123")
print(f"  Parrain Non-Premium: test_free_parrain / test123")
print(f"  Joueur Solo: test_joueur_solo_1 / test123")
print("")
