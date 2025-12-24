#!/usr/bin/env python
"""
Script pour configurer le système de parrainage RUMO RUSH
Conditions exactes :
- Parrain Premium (10 000 FCFA/mois) : 10% commission ILLIMITÉE
- Parrain Non-Premium : 10% commission sur 3 PREMIÈRES parties gagnantes SEULEMENT
- Joueurs sans parrain : Aucune commission générée
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.referrals.models import ReferralProgram
from django.utils.translation import gettext_lazy as _


def setup_referral_system():
    """Configurer le programme de parrainage avec les conditions exactes."""
    
    print("\n" + "="*60)
    print("CONFIGURATION SYSTÈME DE PARRAINAGE RUMO RUSH")
    print("="*60 + "\n")
    
    # Créer ou mettre à jour le programme par défaut
    program, created = ReferralProgram.objects.get_or_create(
        is_default=True,
        defaults={
            'name': 'Programme de Parrainage Standard RUMO RUSH',
            'description': '''
Programme de parrainage avec conditions simplifiées:
- Parrain Premium (10,000 FCFA/mois): 10% commission sur TOUTES les parties gagnantes (illimité)
- Parrain Non-Premium: 10% commission sur les 3 PREMIÈRES parties gagnantes SEULEMENT
- Commission appliquée sur les gains (10% du montant gagné)
- Joueurs sans parrain: aucune commission générée
            ''',
            'commission_type': 'percentage',
            'commission_rate': Decimal('10.00'),  # Toujours 10%
            'fixed_commission': Decimal('0.00'),
            'max_commission_per_referral': Decimal('0.00'),  # Illimité
            'max_daily_commission': Decimal('0.00'),  # Illimité
            'max_monthly_commission': Decimal('0.00'),  # Illimité
            'min_bet_for_commission': Decimal('100.00'),
            'free_games_limit': 3,  # Non-premium: 3 parties seulement
            'status': 'active',
        }
    )
    
    if created:
        print("✅ NOUVEAU PROGRAMME CRÉÉ:")
    else:
        # Mettre à jour les champs existants
        program.name = 'Programme de Parrainage Standard RUMO RUSH'
        program.commission_type = 'percentage'
        program.commission_rate = Decimal('10.00')
        program.fixed_commission = Decimal('0.00')
        program.max_commission_per_referral = Decimal('0.00')
        program.max_daily_commission = Decimal('0.00')
        program.max_monthly_commission = Decimal('0.00')
        program.free_games_limit = 3
        program.status = 'active'
        program.save()
        print("✅ PROGRAMME MIS À JOUR:")
    
    print(f"\nNom: {program.name}")
    print(f"ID: {program.id}")
    print(f"Statut: {program.get_status_display()}")
    print("\nCONDITIONS:")
    print("  └─ Taux Commission: 10% (fixe)")
    print("  └─ Parrain Premium: commission ILLIMITÉE")
    print("  └─ Parrain Non-Premium: 3 premières parties gagnantes SEULEMENT")
    print("  └─ Joueurs sans parrain: ZÉRO commission")
    print("  └─ Commission appliquée sur: les GAINS (pas la mise)")
    
    print("\n" + "="*60)
    print("🎯 RÉSUMÉ DU SYSTÈME DE PARRAINAGE")
    print("="*60 + "\n")
    
    print("SCÉNARIO 1 - Parrain PREMIUM (10,000 FCFA/mois)")
    print("-" * 60)
    print("Filleul gagne 5,000 FCFA → Parrain reçoit 500 FCFA (10%)")
    print("Filleul gagne 10,000 FCFA → Parrain reçoit 1,000 FCFA (10%)")
    print("Filleul gagne 20,000 FCFA → Parrain reçoit 2,000 FCFA (10%)")
    print("→ Cela continue INDÉFINIMENT pour le parrain premium")
    
    print("\nSCÉNARIO 2 - Parrain NON-PREMIUM (gratuit)")
    print("-" * 60)
    print("Filleul gagne 5,000 FCFA (1ère victoire) → Parrain reçoit 500 FCFA ✅")
    print("Filleul gagne 10,000 FCFA (2ème victoire) → Parrain reçoit 1,000 FCFA ✅")
    print("Filleul gagne 20,000 FCFA (3ème victoire) → Parrain reçoit 2,000 FCFA ✅")
    print("Filleul gagne 15,000 FCFA (4ème victoire) → Parrain reçoit 0 FCFA ❌")
    print("→ PLUS AUCUNE COMMISSION APRÈS 3 VICTOIRES")
    
    print("\nSCÉNARIO 3 - Filleul SANS PARRAIN")
    print("-" * 60)
    print("Filleul gagne 10,000 FCFA → Aucune commission générée ✓")
    print("→ Les gains ne bénéficient à personne d'autre")
    
    print("\n" + "="*60)
    print("PROCHAINES ÉTAPES")
    print("="*60)
    print("\n1. Exécuter la migration:")
    print("   python manage.py migrate referrals")
    print("\n2. Les calculs de commission sont automatisés:")
    print("   - Lors de chaque fin de partie")
    print("   - Via l'API: /api/v1/referrals/")
    print("   - Dashboard: /api/v1/referrals/dashboard/")
    print("\n" + "="*60 + "\n")
    
    return program


if __name__ == '__main__':
    setup_referral_system()
