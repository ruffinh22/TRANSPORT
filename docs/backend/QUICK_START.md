# 🚀 RUMO RUSH Backend - Quick Start

## Installation & Setup (5 min)

```bash
# Clone & navigate
git clone https://github.com/ruffinh22/rhumo_rush.git
cd rhumo_rush/backend

# Python environment
python3.10 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env with your settings

# Database
python manage.py migrate

# Create admin
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Quick Commands

```bash
# Health check
curl http://localhost:8000/health/

# API documentation
http://localhost:8000/api/v1/docs/
http://localhost:8000/api/v1/redoc/

# Run tests
pytest
pytest -m unit

# Collect static files
python manage.py collectstatic

# View logs
tail -f logs/django.log
tail -f logs/django.json.log
```

## Project Structure

```
backend/
├── rumo_rush/          # Django config
│   ├── settings/       # Base, dev, prod, testing
│   ├── urls.py         # API routes
│   ├── asgi.py         # WebSockets
│   ├── wsgi.py         # Production
│   └── celery.py       # Async tasks
├── apps/               # Applications
│   ├── accounts/       # Users & auth
│   ├── games/          # Gaming
│   ├── payments/       # Transactions
│   ├── referrals/      # Commissions
│   ├── analytics/      # Metrics
│   └── core/           # Utilities
├── tests/              # Test suite
├── logs/               # Application logs
└── README.md           # This file
```

## Documentation

- **API**: `BACKEND_API.md` (50+ endpoints)
- **Deployment**: `DEPLOYMENT.md` (Docker, Nginx, SSL)
- **Testing**: `TESTING.md` (pytest, fixtures, coverage)
- **Improvements**: `PHASE3_IMPROVEMENTS.md` (drf-spectacular, logging)

## Support

- **Issues**: https://github.com/ruffinh22/rhumo_rush/issues
- **Email**: dev@rumorush.com
- **Status**: https://status.rumorush.com
