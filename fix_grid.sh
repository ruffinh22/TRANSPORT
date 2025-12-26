#!/bin/bash
# Script pour corriger les props Grid

echo "Correction des props Grid..."

# Remplacer xs={12} sm={6} md={3} par size={{xs: 12, sm: 6, md: 3}}
# On utilise des replacements spécifiques pour chaque combinaison

cd /home/lidruf/TRANSPORT/frontend/src

# Pattern: xs={12} sm={6} md={4}
find . -name "*.tsx" -exec sed -i 's/xs={12} sm={6} md={4}/size={{ xs: 12, sm: 6, md: 4 }}/g' {} \;

# Pattern: xs={12} sm={6} md={3}
find . -name "*.tsx" -exec sed -i 's/xs={12} sm={6} md={3}/size={{ xs: 12, sm: 6, md: 3 }}/g' {} \;

# Pattern: xs={12} sm={6} md={2}
find . -name "*.tsx" -exec sed -i 's/xs={12} sm={6} md={2}/size={{ xs: 12, sm: 6, md: 2 }}/g' {} \;

# Pattern: xs={12} md={8}
find . -name "*.tsx" -exec sed -i 's/xs={12} md={8}/size={{ xs: 12, md: 8 }}/g' {} \;

# Pattern: xs={12} md={4}
find . -name "*.tsx" -exec sed -i 's/xs={12} md={4}/size={{ xs: 12, md: 4 }}/g' {} \;

# Pattern: xs={12} md={6}
find . -name "*.tsx" -exec sed -i 's/xs={12} md={6}/size={{ xs: 12, md: 6 }}/g' {} \;

# Pattern: xs={12} sm={6} md={2.4}
find . -name "*.tsx" -exec sed -i 's/xs={12} sm={6} md={2\.4}/size={{ xs: 12, sm: 6, md: 2.4 }}/g' {} \;

echo "Correction terminée !"
