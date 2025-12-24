#!/bin/bash
# TKF - Transport Management System - Useful Commands

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TKF - Transport Management System    ║${NC}"
echo -e "${BLUE}║  Useful Commands Reference            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

# ===== SETUP =====
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}SETUP & INSTALLATION${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Backend Setup:${NC}"
echo "  cd /home/lidruf/TRANSPORT/backend"
echo "  conda activate envrl"
echo "  pip install -r requirements.txt"
echo "  python manage.py migrate"
echo "  python manage.py init_roles"
echo "  python manage.py createsuperuser"

echo -e "\n${BLUE}Frontend Setup:${NC}"
echo "  cd /home/lidruf/TRANSPORT/frontend"
echo "  yarn install"

# ===== START SERVERS =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}START DEVELOPMENT SERVERS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Start Backend (Terminal 1):${NC}"
echo "  cd /home/lidruf/TRANSPORT/backend"
echo "  conda activate envrl"
echo "  python manage.py runserver 0.0.0.0:8000"

echo -e "\n${BLUE}Start Frontend (Terminal 2):${NC}"
echo "  cd /home/lidruf/TRANSPORT/frontend"
echo "  yarn dev"

echo -e "\n${BLUE}Access URLs:${NC}"
echo "  • Frontend:     http://localhost:3001"
echo "  • Backend API:  http://localhost:8000/api/v1"
echo "  • Admin Panel:  http://localhost:8000/admin"
echo "  • Swagger Docs: http://localhost:8000/api/v1/docs/"

# ===== DJANGO COMMANDS =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}DJANGO MANAGEMENT COMMANDS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Database:${NC}"
echo "  python manage.py migrate                # Apply migrations"
echo "  python manage.py makemigrations         # Create new migrations"
echo "  python manage.py sqlmigrate app 0001   # Show SQL for migration"
echo "  python manage.py showmigrations         # List all migrations"

echo -e "\n${BLUE}Users & Auth:${NC}"
echo "  python manage.py createsuperuser        # Create admin user"
echo "  python manage.py changepassword user    # Change user password"
echo "  python manage.py init_roles             # Initialize system roles"

echo -e "\n${BLUE}Development:${NC}"
echo "  python manage.py shell                  # Interactive Python shell"
echo "  python manage.py runserver              # Start dev server"
echo "  python manage.py runserver 0.0.0.0:8000 # Listen on all interfaces"
echo "  python manage.py test                   # Run tests"

echo -e "\n${BLUE}Static Files:${NC}"
echo "  python manage.py collectstatic         # Collect static files"
echo "  python manage.py findstatic app file   # Find static file location"

echo -e "\n${BLUE}Data:${NC}"
echo "  python manage.py dumpdata > backup.json   # Export database"
echo "  python manage.py loaddata backup.json     # Import database"

# ===== TESTING =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}TESTING${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Backend Tests:${NC}"
echo "  pytest                                  # Run all tests"
echo "  pytest apps/users/tests.py              # Run specific app tests"
echo "  pytest -v                               # Verbose output"
echo "  pytest --cov                            # With coverage report"
echo "  pytest --cov=apps --html=report.html    # Coverage HTML report"

echo -e "\n${BLUE}Frontend Tests:${NC}"
echo "  yarn test                               # Run tests"
echo "  yarn test:watch                         # Watch mode"
echo "  yarn test:coverage                      # Coverage report"

# ===== CODE QUALITY =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}CODE QUALITY & FORMATTING${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Backend:${NC}"
echo "  black apps/                             # Format code"
echo "  flake8 apps/                            # Lint code"
echo "  isort apps/                             # Sort imports"
echo "  pylint apps/                            # Advanced linting"
echo "  mypy apps/                              # Type checking"

echo -e "\n${BLUE}Frontend:${NC}"
echo "  yarn lint                               # Lint code"
echo "  yarn format                             # Format code"
echo "  yarn type-check                         # Type checking"

# ===== BUILD & DEPLOYMENT =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}BUILD & DEPLOYMENT${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Frontend Build:${NC}"
echo "  yarn build                              # Build for production"
echo "  yarn preview                            # Preview production build"
echo "  yarn build --outDir dist                # Build to custom directory"

echo -e "\n${BLUE}Backend Production:${NC}"
echo "  gunicorn config.wsgi --workers 4        # Production WSGI server"
echo "  daphne -b 0.0.0.0 -p 8000 config.asgi   # Production ASGI server"

echo -e "\n${BLUE}Docker:${NC}"
echo "  docker-compose up                       # Start all services"
echo "  docker-compose up -d                    # Start in background"
echo "  docker-compose down                     # Stop all services"
echo "  docker-compose logs -f                  # View logs"
echo "  docker-compose ps                       # List services"

# ===== GIT COMMANDS =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}GIT COMMANDS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Branching:${NC}"
echo "  git checkout -b feature/name             # Create feature branch"
echo "  git checkout develop                     # Switch to develop"
echo "  git pull origin develop                  # Pull latest changes"
echo "  git push origin feature/name             # Push feature branch"

echo -e "\n${BLUE}Commits:${NC}"
echo "  git add .                                # Stage all changes"
echo "  git commit -m 'message'                  # Commit with message"
echo "  git push origin branch-name              # Push commits"

echo -e "\n${BLUE}History:${NC}"
echo "  git log --oneline                        # View commit history"
echo "  git diff                                 # Show unstaged changes"
echo "  git status                               # Show status"

# ===== DATABASE COMMANDS =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}DATABASE MANAGEMENT${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}SQLite:${NC}"
echo "  sqlite3 db.sqlite3                      # Open database"
echo "  .tables                                  # List tables"
echo "  SELECT COUNT(*) FROM users;              # Count records"
echo "  .quit                                    # Exit"

echo -e "\n${BLUE}PostgreSQL (Production):${NC}"
echo "  psql -U postgres -d tkf_db               # Connect to DB"
echo "  \\dt                                      # List tables"
echo "  SELECT COUNT(*) FROM users;              # Count records"
echo "  \\q                                       # Disconnect"

# ===== USEFUL SHORTCUTS =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}USEFUL SHORTCUTS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Backend Terminal Alias:${NC}"
echo '  alias django-shell="cd ~/TRANSPORT/backend && conda activate envrl && python manage.py shell"'

echo -e "\n${BLUE}Frontend Terminal Alias:${NC}"
echo '  alias frontend-dev="cd ~/TRANSPORT/frontend && yarn dev"'

echo -e "\n${BLUE}Run both servers:${NC}"
echo '  # Terminal 1:'
echo '  cd ~/TRANSPORT/backend && conda activate envrl && python manage.py runserver'
echo '  # Terminal 2:'
echo '  cd ~/TRANSPORT/frontend && yarn dev'

# ===== TROUBLESHOOTING =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}TROUBLESHOOTING${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Port Already in Use:${NC}"
echo "  lsof -i :8000                           # Find process on port 8000"
echo "  kill -9 <PID>                           # Kill process"

echo -e "\n${BLUE}Reset Database:${NC}"
echo "  rm backend/db.sqlite3"
echo "  python manage.py migrate"
echo "  python manage.py init_roles"

echo -e "\n${BLUE}Clear Python Cache:${NC}"
echo "  find . -type d -name __pycache__ -exec rm -r {} +"
echo "  find . -name '*.pyc' -delete"

echo -e "\n${BLUE}Clear Node Cache:${NC}"
echo "  rm -rf frontend/node_modules"
echo "  rm frontend/yarn.lock"
echo "  yarn install"

echo -e "\n${BLUE}Fix Import Errors:${NC}"
echo "  pip install -r requirements.txt --upgrade"
echo "  pip install -r requirements.txt --force-reinstall"

# ===== USEFUL RESOURCES =====
echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}USEFUL RESOURCES${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}Documentation:${NC}"
echo "  • Django: https://docs.djangoproject.com"
echo "  • DRF: https://www.django-rest-framework.org"
echo "  • React: https://react.dev"
echo "  • Material-UI: https://mui.com"
echo "  • Vite: https://vitejs.dev"

echo -e "\n${BLUE}API Documentation:${NC}"
echo "  • Swagger: http://localhost:8000/api/v1/docs/"
echo "  • ReDoc: http://localhost:8000/api/v1/redoc/"

echo -e "\n${BLUE}Project Files:${NC}"
echo "  • README.md - Main documentation"
echo "  • PROJECT_SUMMARY.md - Detailed summary"
echo "  • ROADMAP.md - Future plans"
echo "  • ITERATION_COMPLETE.md - Backend details"

echo -e "\n${BLUE}Configuration:${NC}"
echo "  • Backend: /home/lidruf/TRANSPORT/backend/config/settings.py"
echo "  • Frontend: /home/lidruf/TRANSPORT/frontend/vite.config.ts"
echo "  • Environment: .env files in backend and frontend"

echo -e "\n\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Happy Coding! 🚀${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
