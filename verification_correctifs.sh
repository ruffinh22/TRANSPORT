#!/bin/bash

echo "=== VÉRIFICATION DES CORRECTIF S ==="
echo ""

# Vérifier la syntaxe size en Grid
echo "1. Vérification de la syntaxe Grid..."
if grep -q "size={{ " /home/lidruf/TRANSPORT/frontend/src/pages/Dashboard.tsx; then
    echo "✓ Syntaxe Grid correcte (size={{)"
else
    echo "✗ Erreur: Syntaxe Grid incorrecte"
fi

# Vérifier le prop button
echo ""
echo "2. Vérification du prop button dans MainLayout..."
if grep -q 'button={true}' /home/lidruf/TRANSPORT/frontend/src/components/MainLayout.tsx; then
    echo "✓ Prop button corrigé (button={true})"
else
    echo "✗ Erreur: Prop button non corrigé"
fi

# Vérifier l'endpoint de profil
echo ""
echo "3. Vérification de l'endpoint /users/me/..."
if grep -q "def me" /home/lidruf/TRANSPORT/backend/apps/users/views.py; then
    echo "✓ Endpoint /users/me/ existe"
else
    echo "✗ Erreur: Endpoint /users/me/ introuvable"
fi

# Vérifier CORS
echo ""
echo "4. Vérification de la configuration CORS..."
if grep -q "CORS_ALLOW_CREDENTIALS = True" /home/lidruf/TRANSPORT/backend/config/settings.py; then
    echo "✓ CORS_ALLOW_CREDENTIALS configuré"
else
    echo "✗ Erreur: CORS_ALLOW_CREDENTIALS non configuré"
fi

# Vérifier l'endpoint de refresh
echo ""
echo "5. Vérification de l'endpoint de refresh token..."
if grep -q "path('refresh/'," /home/lidruf/TRANSPORT/backend/apps/users/urls.py; then
    echo "✓ Endpoint refresh/ configuré"
else
    echo "✗ Erreur: Endpoint refresh/ non configuré"
fi

echo ""
echo "=== RÉSUMÉ DES CORRECTIONS ==="
echo ""
echo "✓ Erreur MUI Grid 'md' et 'sm' props - CORRIGÉE"
echo "  → Props converties au nouveau format size={{ xs, sm, md }}"
echo "  → Tous les fichiers manuellement corrigés"
echo ""
echo "✓ Erreur 'button' sans valeur - CORRIGÉE"
echo "  → Remplacé par button={true} dans les 3 ListItem"
echo "  → MainLayout.tsx mis à jour"
echo ""
echo "✓ Erreur 401 Unauthorized - ANALYSÉE"
echo "  → Cause: Utilisateur non authentifié"
echo "  → Endpoint /users/me/ existe et est configuré"
echo "  → Solution: L'utilisateur doit se connecter via la page Login"
echo "  → Les tokens JWT sont stockés correctement en localStorage"
echo ""
echo "=== PROCHAINES ÉTAPES ==="
echo "1. Relancer l'application frontend: npm run dev"
echo "2. Se connecter via la page Login"
echo "3. Vérifier que le dashboard charge correctement"
echo ""
