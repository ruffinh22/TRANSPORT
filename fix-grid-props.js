#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const glob = require('glob');

/**
 * Convertit les props Grid xs, sm, md, etc. vers le format MUI v7
 * xs={12} sm={6} md={3} => size={{ xs: 12, sm: 6, md: 3 }}
 */
function fixGridProps(content) {
  // Regex pour trouver les Grid items avec xs, sm, md, lg, xl
  const gridItemRegex = /<Grid\s+item\s+([^>]*?)>/g;
  
  return content.replace(gridItemRegex, (match, props) => {
    // Extraire tous les props individuels
    const propsArray = props.trim().split(/\s+(?=[a-zA-Z])/);
    
    const sizeProps = {};
    const otherProps = [];
    
    for (const prop of propsArray) {
      if (prop.match(/^(xs|sm|md|lg|xl)=/)) {
        const [key, value] = prop.split('=');
        sizeProps[key] = value.replace(/[{}]/g, '');
      } else {
        otherProps.push(prop);
      }
    }
    
    // Si des props de taille ont été trouvées
    if (Object.keys(sizeProps).length > 0) {
      const sizeString = Object.entries(sizeProps)
        .map(([k, v]) => `${k}: ${v}`)
        .join(', ');
      
      const newProps = [
        ...otherProps,
        `size={{ ${sizeString} }}`
      ].filter(p => p.trim()).join(' ');
      
      return `<Grid item ${newProps}>`;
    }
    
    return match;
  });
}

// Fichiers à traiter
const files = [
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
];

console.log('Fixing Grid props in MUI files...\n');

files.forEach(filePath => {
  if (fs.existsSync(filePath)) {
    const content = fs.readFileSync(filePath, 'utf8');
    const fixed = fixGridProps(content);
    
    if (content !== fixed) {
      fs.writeFileSync(filePath, fixed, 'utf8');
      console.log(`✓ Fixed: ${path.basename(filePath)}`);
    } else {
      console.log(`- No changes needed: ${path.basename(filePath)}`);
    }
  } else {
    console.log(`✗ File not found: ${filePath}`);
  }
});

console.log('\nDone!');
