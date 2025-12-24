#!/bin/bash

# Script de configuration automatique pour RUMO RUSH Backend
# Ce script configure l'environnement de développement complet

echo "🚀 Configuration de RUMO RUSH Backend"
echo "====================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier Python
echo "🐍 Vérification de Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python trouvé: $PYTHON_VERSION"
else
    print_error "Python 3 n'est pas installé"
    exit 1
fi

# Créer un environnement virtuel
echo "📦 Création de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Environnement virtuel créé"
else
    print_warning "Environnement virtuel existe déjà"
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate
print_status "Environnement virtuel activé"

# Installer les dépendances
echo "📚 Installation des dépendances..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Dépendances installées"
else
    print_error "requirements.txt non trouvé"
    exit 1
fi

# Créer le fichier .env
echo "⚙️  Configuration des variables d'environnement..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Fichier .env créé à partir de .env.example"
    print_warning "Veuillez modifier .env avec vos paramètres"
else
    print_warning "Fichier .env existe déjà"
fi

# Créer les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p logs
mkdir -p media/kyc_documents
mkdir -p media/game_icons
mkdir -p media/payment_icons
mkdir -p static
mkdir -p staticfiles

print_status "Dossiers créés"

# Vérifier la base de données
echo "🗄️  Configuration de la base de données..."
if command -v sqlite3 &> /dev/null; then
    print_status "SQLite disponible pour le développement"
else
    print_warning "SQLite non trouvé - utilisez PostgreSQL en production"
fi

# Exécuter les migrations
echo "🔄 Exécution des migrations..."
python manage.py makemigrations
python manage.py migrate
print_status "Migrations exécutées"

# Créer les données de test
echo "🎮 Création des données de test..."
python manage.py shell << EOF
from apps.games.models import GameType
from apps.payments.models import PaymentMethod
from apps.referrals.models import ReferralProgram
from decimal import Decimal

# Créer les types de jeux
game_types = [
    {'name': 'chess', 'display_name': 'Échecs', 'category': 'strategy', 'description': 'Jeu d\'échecs classique'},
    {'name': 'checkers', 'display_name': 'Dames', 'category': 'strategy', 'description': 'Jeu de dames classique'},
    {'name': 'ludo', 'display_name': 'Ludo', 'category': 'board', 'description': 'Jeu de Ludo pour 2 joueurs'},
    {'name': 'cards', 'display_name': 'Cartes', 'category': 'cards', 'description': 'Jeu de cartes Rami simplifié'},
]

for gt_data in game_types:
    GameType.objects.get_or_create(
        name=gt_data['name'],
        defaults=gt_data
    )

# Créer les méthodes de paiement
payment_methods = [
    {
        'name': 'Mobile Money',
        'method_type': 'mobile_money',
        'supported_currencies': ['FCFA'],
        'min_deposit': {'FCFA': 1000},
        'max_deposit': {'FCFA': 1000000},
        'deposit_fee_percentage': Decimal('2.5')
    },
    {
        'name': 'Carte Bancaire',
        'method_type': 'card',
        'supported_currencies': ['EUR', 'USD'],
        'min_deposit': {'EUR': 2, 'USD': 2},
        'max_deposit': {'EUR': 1500, 'USD': 1800},
        'deposit_fee_percentage': Decimal('3.0')
    }
]

for pm_data in payment_methods:
    PaymentMethod.objects.get_or_create(
        name=pm_data['name'],
        defaults=pm_data
    )

# Créer le programme de parrainage par défaut
ReferralProgram.objects.get_or_create(
    name='Programme Standard',
    defaults={
        'description': 'Programme de parrainage standard',
        'commission_type': 'percentage',
        'commission_rate': Decimal('10.00'),
        'free_games_limit': 3,
        'is_default': True
    }
)

print("Données de test créées")
EOF

print_status "Données de test créées"

# Créer un superutilisateur (optionnel)
echo "👤 Création d'un superutilisateur..."
read -p "Voulez-vous créer un superutilisateur maintenant? (y/N): " create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
    print_status "Superutilisateur créé"
else
    print_warning "Superutilisateur non créé - utilisez 'python manage.py createsuperuser' plus tard"
fi

# Exécuter les tests
echo "🧪 Exécution des tests..."
read -p "Voulez-vous exécuter la suite de tests? (y/N): " run_tests
if [[ $run_tests =~ ^[Yy]$ ]]; then
    python test_suite.py
    print_status "Tests exécutés"
else
    print_warning "Tests non exécutés - utilisez 'python test_suite.py' plus tard"
fi

# Résumé final
echo ""
echo "🎉 Configuration terminée!"
echo "========================"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Modifier le fichier .env avec vos paramètres"
echo "2. Configurer PostgreSQL et Redis pour la production"
echo "3. Démarrer le serveur: python manage.py runserver"
echo "4. Accéder à l'admin: http://localhost:8000/admin/"
echo "5. Tester l'API: http://localhost:8000/api/"
echo ""
echo "📚 Documentation:"
echo "- API: http://localhost:8000/api/docs/"
echo "- Admin: http://localhost:8000/admin/"
echo "- Health: http://localhost:8000/api/health/"
echo ""
echo "🔧 Commandes utiles:"
echo "- Tests: python test_suite.py"
echo "- Shell: python manage.py shell"
echo "- Migrations: python manage.py makemigrations && python manage.py migrate"
echo "- Collectstatic: python manage.py collectstatic"
echo ""

# Rendre le script exécutable
chmod +x setup_project.sh

print_status "Script de configuration terminé avec succès!"
