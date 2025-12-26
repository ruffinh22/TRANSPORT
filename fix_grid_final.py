#!/usr/bin/env python3
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

def fix_grid_props(content):
    """Convert Grid item props from xs, sm, md to size={{xs, sm, md}}"""
    
    # Pattern: <Grid item xs={...} sm={...} md={...}
    # We need to capture the entire Grid item opening tag with breakpoint props
    
    def replace_grid(match):
        full_tag = match.group(0)  # entire match including <Grid item
        attrs = match.group(1)      # everything between 'item' and '>'
        
        # Extract breakpoint props
        breakpoints = {}
        for bp in ['xs', 'sm', 'md', 'lg', 'xl']:
            pattern = rf'{bp}=\{{(\d+(?:\.\d+)?)\}}'
            m = re.search(pattern, attrs)
            if m:
                breakpoints[bp] = m.group(1)
        
        if not breakpoints:
            return full_tag
        
        # Remove all breakpoint props from attrs
        new_attrs = attrs
        for bp in ['xs', 'sm', 'md', 'lg', 'xl']:
            new_attrs = re.sub(rf'\s*{bp}=\{{\d+(?:\.\d+)?\}}\s*', ' ', new_attrs)
        
        # Build the size prop
        size_content = ', '.join([f'{bp}: {val}' for bp, val in breakpoints.items()])
        size_prop = f'size={{ {size_content} }}'
        
        # Reconstruct the tag
        new_attrs = new_attrs.strip()
        if new_attrs:
            new_tag = f'<Grid item {size_prop} {new_attrs}>'
        else:
            new_tag = f'<Grid item {size_prop}>'
        
        return new_tag
    
    # Match <Grid item followed by any attributes
    pattern = r'<Grid\s+item\s+([^>]*)>'
    return re.sub(pattern, replace_grid, content)

for file_path in files:
    if os.path.exists(file_path):
        print(f'Processing: {os.path.basename(file_path)}...', end='', flush=True)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = fix_grid_props(content)
        
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(' ✓ Fixed')
        else:
            print(' - No changes')
    else:
        print(f'✗ Not found: {file_path}')

print('\nDone!')
