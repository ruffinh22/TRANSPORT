# 🚀 Makefile pour TKF Backend Django

.PHONY: help install migrate run test clean docker-build docker-up docker-down

# Couleurs
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)╔════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║  🚀 TKF Backend Django - Commandes Utiles ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Installation & Setup:$(NC)"
	@echo "  make install          - Installer les dépendances"
	@echo "  make migrate          - Appliquer les migrations"
	@echo "  make superuser        - Créer un superuser"
	@echo "  make init-roles       - Initialiser les rôles"
	@echo "  make seed-users       - Créer les utilisateurs par défaut"
	@echo "  make setup            - Setup complet (install + migrate + roles + users)"
	@echo ""
	@echo "$(GREEN)Développement:$(NC)"
	@echo "  make run              - Lancer le serveur de développement"
	@echo "  make shell            - Django shell"
	@echo "  make makemigrations   - Créer les migrations"
	@echo ""
	@echo "$(GREEN)Tests:$(NC)"
	@echo "  make test             - Exécuter tous les tests"
	@echo "  make test-users       - Tests du module users"
	@echo "  make coverage         - Coverage report"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint             - Exécuter les linters (black, flake8, isort)"
	@echo "  make format           - Formater le code"
	@echo "  make mypy             - Type checking"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make reset-db         - Réinitialiser la DB (⚠️  données perdues)"
	@echo "  make dumpdata         - Backup DB en JSON"
	@echo "  make loaddata         - Restaurer depuis JSON"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build     - Builder les images"
	@echo "  make docker-up        - Lancer les containers"
	@echo "  make docker-down      - Arrêter les containers"
	@echo "  make docker-logs      - Voir les logs"
	@echo ""
	@echo "$(GREEN)Utilitaires:$(NC)"
	@echo "  make clean            - Nettoyer les fichiers temporaires"
	@echo "  make check            - Vérifier la configuration Django"
	@echo ""

# Installation
install:
	@echo "$(BLUE)Installation des dépendances...$(NC)"
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Installation terminée$(NC)"

setup: install migrate init-roles seed-users
	@echo "$(GREEN)✓ Setup complet terminé$(NC)"

# Database
migrate:
	@echo "$(BLUE)Application des migrations...$(NC)"
	python manage.py migrate
	@echo "$(GREEN)✓ Migrations appliquées$(NC)"

makemigrations:
	@echo "$(BLUE)Création des migrations...$(NC)"
	python manage.py makemigrations
	@echo "$(GREEN)✓ Migrations créées$(NC)"

superuser:
	@echo "$(BLUE)Création d'un superuser...$(NC)"
	python manage.py createsuperuser

init-roles:
	@echo "$(BLUE)Initialisation des rôles et permissions...$(NC)"
	python manage.py init_roles
	@echo "$(GREEN)✓ Rôles créés$(NC)"

seed-users:
	@echo "$(BLUE)Création des utilisateurs par défaut...$(NC)"
	python manage.py seed_users
	@echo "$(GREEN)✓ Utilisateurs créés$(NC)"

reset-db:
	@echo "$(YELLOW)⚠️  Réinitialisation de la base de données...$(NC)"
	@read -p "Êtes-vous sûr? (y/n) " confirm && [ "$$confirm" = "y" ] && \
	python manage.py flush --noinput && \
	python manage.py migrate && \
	python manage.py init_roles && \
	python manage.py seed_users && \
	echo "$(GREEN)✓ Base de données réinitialisée$(NC)" || echo "Annulé"

dumpdata:
	@echo "$(BLUE)Backup de la base de données...$(NC)"
	python manage.py dumpdata > backup_$(shell date +%Y%m%d_%H%M%S).json
	@echo "$(GREEN)✓ Backup créé$(NC)"

loaddata:
	@echo "$(BLUE)Restauration de la base de données...$(NC)"
	@read -p "Fichier de backup (ex: backup_20240101_000000.json): " file && \
	python manage.py loaddata $$file && \
	echo "$(GREEN)✓ Données restaurées$(NC)"

# Développement
run:
	@echo "$(BLUE)Démarrage du serveur de développement...$(NC)"
	@echo "$(YELLOW)API:   http://localhost:8000/api/v1/$(NC)"
	@echo "$(YELLOW)Admin: http://localhost:8000/admin$(NC)"
	@echo "$(YELLOW)Docs:  http://localhost:8000/api/v1/docs/$(NC)"
	python manage.py runserver

shell:
	python manage.py shell

check:
	python manage.py check

# Tests
test:
	@echo "$(BLUE)Exécution des tests...$(NC)"
	pytest -v

test-users:
	@echo "$(BLUE)Tests du module users...$(NC)"
	pytest apps/users/tests.py -v

coverage:
	@echo "$(BLUE)Rapport de coverage...$(NC)"
	pytest --cov=apps --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Rapport généré: htmlcov/index.html$(NC)"

# Code Quality
lint:
	@echo "$(BLUE)Exécution des linters...$(NC)"
	black --check .
	flake8 .
	isort --check-only .
	@echo "$(GREEN)✓ Linters passés$(NC)"

format:
	@echo "$(BLUE)Formatage du code...$(NC)"
	black .
	isort .
	@echo "$(GREEN)✓ Code formaté$(NC)"

mypy:
	@echo "$(BLUE)Type checking...$(NC)"
	mypy apps --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complété$(NC)"

# Docker
docker-build:
	@echo "$(BLUE)Building des images Docker...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Images construites$(NC)"

docker-up:
	@echo "$(BLUE)Démarrage des containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers démarrés$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000/api/v1/$(NC)"

docker-down:
	@echo "$(BLUE)Arrêt des containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers arrêtés$(NC)"

docker-logs:
	docker-compose logs -f backend

docker-shell:
	docker-compose exec backend bash

# Utilitaires
clean:
	@echo "$(BLUE)Nettoyage des fichiers temporaires...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Nettoyage terminé$(NC)"

.DEFAULT_GOAL := help
