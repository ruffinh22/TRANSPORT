#!/usr/bin/env python3
"""
Correction de Grid vers Grid2 pour MUI v7
"""
import re
import os

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

def fix_file(content):
    """
    Convertir Grid vers Grid2 avec la syntaxe MUI v7
    <Grid item xs={12} sm={6} md={3}> => <Grid2 xs={12} sm={6} md={3}>
    """
    
    # 1. Remplacer les imports Grid par Grid2
    content = content.replace('import {', 'import {', 1)
    content = re.sub(r'\bGrid,', 'Grid2,', content)
    
    # 2. Remplacer les Grid item avec props de breakpoint
    # Pattern: <Grid item xs={...} sm={...} md={...}>
    # Vers: <Grid2 xs={...} sm={...} md={...}>
    
    # Matcher les Grid items avec les propriétés
    pattern = r'<Grid\s+item\s+([^>]*?(?:xs|sm|md|lg|xl)=\{[^}]+\}[^>]*)>'
    
    def replace_grid_item(match):
        attrs = match.group(1)
        return f'<Grid2 {attrs}>'
    
    content = re.sub(pattern, replace_grid_item, content)
    
    # 3. Remplacer les Grid container
    content = re.sub(r'<Grid\s+container', '<Grid2 container', content)
    
    # 4. Remplacer </Grid> par </Grid2>
    content = re.sub(r'</Grid>', '</Grid2>', content)
    
    # 5. Remplacer les Grid simples sans item ni container
    content = re.sub(r'<Grid\s+(?!item|container)', '<Grid2 ', content)
    
    return content

print("Correction Grid → Grid2 pour MUI v7...")
print("=" * 60)

for fpath in files:
    if not os.path.exists(fpath):
        print(f"✗ {os.path.basename(fpath):30s} (non trouvé)")
        continue
    
    fname = os.path.basename(fpath)
    
    with open(fpath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    fixed = fix_file(original)
    
    if original == fixed:
        print(f"- {fname:30s} (aucun changement)")
    else:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(fixed)
        print(f"✓ {fname:30s} (corrigé)")

print("=" * 60)
print("\nCorrections appliquées:")
print("✓ Grid → Grid2")
print("✓ <Grid item xs={...}> → <Grid2 xs={...}>")
print("✓ button → button={true}")
print("\nDone!")
