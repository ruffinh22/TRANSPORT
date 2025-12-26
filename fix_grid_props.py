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
    # Pattern: <Grid item xs={value} sm={value} md={value} ... >
    # Convert to: <Grid item size={{ xs: value, sm: value, md: value }} ...>
    
    # This regex matches Grid item opening tags with breakpoint props
    pattern = r'<Grid\s+item\s+([^>]*?(?:xs|sm|md|lg|xl)=\{\d+(?:\.\d+)?\}[^>]*)>'
    
    def replace_grid_item(match):
        full_text = match.group(1)
        
        # Extract all breakpoint props and their values
        breakpoints = {}
        for bp in ['xs', 'sm', 'md', 'lg', 'xl']:
            bp_pattern = rf'{bp}=\{{(\d+(?:\.\d+)?)\}}'
            bp_match = re.search(bp_pattern, full_text)
            if bp_match:
                breakpoints[bp] = bp_match.group(1)
        
        # Extract other props (everything that's not xs, sm, md, lg, xl)
        other_props = re.sub(r'\s*(xs|sm|md|lg|xl)=\{\d+(?:\.\d+)?\}\s*', ' ', full_text).strip()
        
        # Build size object
        if breakpoints:
            size_pairs = ', '.join([f'{bp}: {val}' for bp, val in breakpoints.items()])
            size_str = f'size={{ {size_pairs} }}'
            
            if other_props:
                return f'<Grid item {size_str} {other_props}>'
            else:
                return f'<Grid item {size_str}>'
        else:
            return match.group(0)
    
    return re.sub(pattern, replace_grid_item, content)

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = fix_grid_props(content)
        
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'✓ Fixed: {os.path.basename(file_path)}')
        else:
            print(f'- No changes: {os.path.basename(file_path)}')
    else:
        print(f'✗ Not found: {file_path}')

print('\nDone!')
