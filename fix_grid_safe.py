#!/usr/bin/env python3
"""
Script pour corriger les props Grid de MUI v7
Convertit xs={12} sm={6} md={3} en size={{ xs: 12, sm: 6, md: 3 }}
"""
import re
import os
from pathlib import Path

files = [
    '/home/lidruf/TRANSPORT/frontend/src/pages/Dashboard.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/LandingPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/TripsPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/TicketsPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/ParcelsPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/PaymentsPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/EmployeesPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/CitiesPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/ReportsPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/pages/SettingsPage.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/components/GovernmentFooter.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/components/AdvancedFilters.tsx',
    '/home/lidruf/TRANSPORT/frontend/src/components/StatisticsChart.tsx'
]

def fix_grid_props(content):
    """
    Convertit xs={12} sm={6} md={3} en size={{ xs: 12, sm: 6, md: 3 }}
    """
    
    # Pattern pour trouver <Grid item avec les props
    # On doit être prudent pour ne pas casser d'autres props
    
    def replace_grid_item(match):
        entire_tag = match.group(0)  # <Grid item ...>
        
        # Extraire tous les props individuels xs, sm, md, lg, xl
        breakpoints = {}
        for bp in ['xs', 'sm', 'md', 'lg', 'xl']:
            pattern = rf'{bp}=\{{(\d+(?:\.\d+)?)\}}'
            m = re.search(pattern, entire_tag)
            if m:
                breakpoints[bp] = m.group(1)
        
        if not breakpoints:
            # Pas de breakpoint à remplacer
            return entire_tag
        
        # Retirer les props breakpoint
        modified = entire_tag
        for bp in ['xs', 'sm', 'md', 'lg', 'xl']:
            modified = re.sub(rf'\s*{bp}=\{{\d+(?:\.\d+)?\}}', '', modified)
        
        # Ajouter size={{...}}
        size_props = ', '.join([f'{bp}: {val}' for bp, val in breakpoints.items()])
        
        # Insérer avant le >
        modified = modified.replace('<Grid item', f'<Grid item size={{ {size_props}', 1)
        modified = modified.replace(' >', '} >', 1)
        
        return modified
    
    # Match <Grid item ... jusqu'à >
    pattern = r'<Grid\s+item\s+[^>]*>'
    return re.sub(pattern, replace_grid_item, content)

print("Correction des props Grid MUI v7...")
print("=" * 60)

for fpath in files:
    if not os.path.exists(fpath):
        print(f"✗ Non trouvé: {fpath}")
        continue
    
    fname = os.path.basename(fpath)
    
    with open(fpath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    fixed = fix_grid_props(original)
    
    if original == fixed:
        print(f"- {fname:30s} (aucun changement)")
    else:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(fixed)
        print(f"✓ {fname:30s} (corrigé)")

print("=" * 60)
print("Correction terminée !")
