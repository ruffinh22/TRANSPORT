# 🧪 RUMO RUSH Backend - Testing Guide

**Version**: 1.0.0  
**Last Updated**: 15 November 2025

---

## 📋 Table des Matières

1. [Test Setup](#-test-setup)
2. [Running Tests](#-running-tests)
3. [Test Coverage](#-test-coverage)
4. [Writing Tests](#-writing-tests)
5. [Test Fixtures](#-test-fixtures)
6. [Mocking](#-mocking)
7. [Integration Tests](#-integration-tests)

---

## ✅ Test Setup

### Installation Dependencies

```bash
# Activer venv
source venv/bin/activate

# Installer pytest et plugins
pip install -r requirements.txt  # déjà inclus

# Packages clés
pip install pytest==7.4.3
pip install pytest-django==4.7.0
pip install pytest-cov==4.1.0
pip install pytest-xdist==3.5.0
pip install factory-boy==3.3.0
pip install faker==20.1.0
```

### Configuration pytest.ini

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = rumo_rush.settings.testing
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
testpaths = tests apps
markers =
    unit: Unit tests
    integration: Integration tests
    api: API endpoint tests
    slow: Slow running tests
    celery: Celery task tests
```

### Test Database

```bash
# Créer test database
python manage.py migrate --settings=rumo_rush.settings.testing

# Utiliser SQLite en mémoire (plus rapide)
export USE_SQLITE_TESTS=True
pytest
```

---

## 🏃 Running Tests

### Basic Commands

```bash
# Run tous les tests
pytest

# Run avec verbosité
pytest -v

# Run avec output
pytest -s

# Run test spécifique
pytest tests/test_auth.py::TestLogin::test_login_with_email

# Run par marker
pytest -m unit
pytest -m "not slow"
```

### Parallel Execution

```bash
# Run tests en parallèle (4 workers)
pytest -n 4

# Run avec auto-discovery
pytest -n auto
```

### Watch Mode

```bash
# Installer pytest-watch
pip install pytest-watch

# Run tests au changement de fichier
ptw

# Run avec arguments
ptw -- -v --tb=short
```

### Conditional Tests

```bash
# Run seulement les tests modifiés
pytest --lf

# Run tests échoués
pytest --ff

# Run depuis dernière failure
pytest --x

# Stop après N failures
pytest --maxfail=3
```

---

## 📊 Test Coverage

### Generate Coverage Report

```bash
# Générer coverage
pytest --cov=apps --cov-report=html --cov-report=term-missing

# Voir report HTML
open htmlcov/index.html

# Coverage par fichier
pytest --cov=apps --cov-report=term-missing:skip-covered
```

### Coverage Thresholds

```bash
# Fail if coverage < 80%
pytest --cov=apps --cov-fail-under=80

# Avec branches
pytest --cov=apps --cov-branch --cov-fail-under=80
```

### Expected Coverage by App

```
accounts/   : ≥ 85%  (critical for auth)
games/      : ≥ 80%  (complex business logic)
payments/   : ≥ 90%  (financial critical)
referrals/  : ≥ 85%  (revenue related)
analytics/  : ≥ 70%  (informational)
core/       : ≥ 80%  (utilities)
```

---

## ✍️ Writing Tests

### Test Structure

```python
# tests/test_auth.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

@pytest.mark.django_db
class TestUserRegistration:
    """Tests pour l'inscription utilisateur."""
    
    def setup_method(self):
        """Setup avant chaque test."""
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'
    
    def test_register_with_valid_data(self):
        """Test inscription avec données valides."""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'secure_password123',
            'confirm_password': 'secure_password123',
            'country': 'BJ',
            'phone': '+22967123456'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='testuser').exists()
        assert response.data['access_token'] is not None
    
    def test_register_with_existing_email(self):
        """Test inscription avec email existant."""
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='password123'
        )
        
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'secure_password123',
            'confirm_password': 'secure_password123',
            'country': 'BJ'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
```

### Common Assertions

```python
# Status codes
assert response.status_code == status.HTTP_200_OK
assert response.status_code == status.HTTP_201_CREATED
assert response.status_code == status.HTTP_400_BAD_REQUEST
assert response.status_code == status.HTTP_401_UNAUTHORIZED
assert response.status_code == status.HTTP_403_FORBIDDEN
assert response.status_code == status.HTTP_404_NOT_FOUND

# Response data
assert response.json()['id'] == user.id
assert 'access_token' in response.data
assert response.data['username'] == 'johndoe'

# Database state
assert User.objects.count() == 1
assert User.objects.filter(email='test@example.com').exists()
assert not User.objects.filter(username='deleted').exists()

# Queries
from django.test.utils import assertNumQueries
with assertNumQueries(3):
    # Code that should make exactly 3 DB queries
    pass
```

---

## 📦 Test Fixtures

### Using Factories

```python
# tests/factories.py
import factory
from django.contrib.auth import get_user_model
from apps.games.models import Game

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des utilisateurs test."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.set_password(extracted or 'defaultpassword')
        obj.save()

class GameFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des parties test."""
    
    class Meta:
        model = Game
    
    game_type = 'chess'
    status = 'active'
    player1 = factory.SubFactory(UserFactory)
    player2 = factory.SubFactory(UserFactory)
    wager = 5000
    currency = 'fcfa'
```

### Usage

```python
# Créer un utilisateur
user = UserFactory()

# Créer avec données spécifiques
user = UserFactory(username='johndoe', email='john@example.com')

# Créer plusieurs
users = UserFactory.create_batch(5)

# Avec relations
game = GameFactory(player1=user)
```

### Fixtures Pytest

```python
# tests/conftest.py
import pytest
from tests.factories import UserFactory, GameFactory

@pytest.fixture
def authenticated_user():
    """Utilisateur authentifié."""
    return UserFactory()

@pytest.fixture
def authenticated_client(authenticated_user):
    """APIClient avec token JWT."""
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken
    
    client = APIClient()
    refresh = RefreshToken.for_user(authenticated_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client

@pytest.fixture
def game_with_players():
    """Partie avec 2 joueurs."""
    return GameFactory()

# Utilisation dans les tests
def test_game_creation(game_with_players):
    assert game_with_players.status == 'active'
```

---

## 🎭 Mocking

### Mock External APIs

```python
from unittest.mock import patch, MagicMock

class TestStripePayment:
    @patch('apps.payments.processors.stripe.stripe.Charge.create')
    def test_successful_payment(self, mock_stripe):
        """Test paiement Stripe réussi."""
        # Setup mock
        mock_stripe.return_value = {
            'id': 'ch_123',
            'status': 'succeeded',
            'amount': 50000
        }
        
        # Code à tester
        payment = create_payment(amount=50000)
        
        # Assertions
        assert payment.status == 'completed'
        mock_stripe.assert_called_once()
```

### Mock Celery Tasks

```python
@patch('apps.referrals.tasks.process_commission.delay')
def test_referral_commission(self, mock_celery):
    """Test commission de parrainage."""
    # Setup
    referrer = UserFactory()
    referred = UserFactory(referrer=referrer)
    
    # Trigger commission
    apply_commission(referred)
    
    # Vérifier que la task Celery a été appelée
    mock_celery.assert_called_once()
```

### Mock Email

```python
from django.core import mail

@patch('django.core.mail.send_mail')
def test_send_welcome_email(self, mock_mail):
    """Test envoi email de bienvenue."""
    user = UserFactory()
    
    # Envoyer email
    send_welcome_email(user)
    
    # Vérifier
    assert len(mail.outbox) == 1
    assert 'Welcome' in mail.outbox[0].subject
```

---

## 🔗 Integration Tests

### Full API Flow

```python
@pytest.mark.django_db
class TestGameFlow:
    """Test le flow complet d'une partie."""
    
    def test_complete_game_workflow(self, authenticated_client):
        """Test: créer partie → rejoindre → jouer → terminer."""
        
        # 1. Create game
        game_data = {
            'game_type': 'chess',
            'wager': 5000,
            'currency': 'fcfa'
        }
        response = authenticated_client.post('/api/v1/games/create/', game_data)
        game_id = response.data['id']
        assert response.status_code == status.HTTP_201_CREATED
        
        # 2. Join game (autre joueur)
        opponent = UserFactory()
        opponent_client = APIClient()
        refresh = RefreshToken.for_user(opponent)
        opponent_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = opponent_client.post(f'/api/v1/games/{game_id}/join/')
        assert response.status_code == status.HTTP_200_OK
        
        # 3. Make moves
        move_data = {'from': 'e2', 'to': 'e4'}
        response = authenticated_client.post(
            f'/api/v1/games/{game_id}/move/',
            move_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 4. Verify game state
        response = authenticated_client.get(f'/api/v1/games/{game_id}/')
        assert response.data['status'] == 'active'
```

### WebSocket Integration

```python
import asyncio
from channels.testing import WebsocketCommunicator
from rumo_rush.asgi import application

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_websocket_move():
    """Test WebSocket pour les coups."""
    
    game = GameFactory()
    user = game.player1
    
    communicator = WebsocketCommunicator(
        application,
        f"ws/game/{game.id}/",
        headers=[(b"authorization", f"Bearer {token}".encode())]
    )
    
    connected, subprotocol = await communicator.connect()
    assert connected
    
    # Envoyer un coup
    await communicator.send_json_to({
        'type': 'move',
        'from': 'e2',
        'to': 'e4'
    })
    
    # Recevoir confirmation
    response = await communicator.receive_json_from()
    assert response['type'] == 'move_confirmed'
    
    await communicator.disconnect()
```

---

## 📋 Test Checklist

### Unit Tests

```
✓ Serializers validation
✓ Model methods and properties
✓ Permissions classes
✓ Utility functions
✓ Validators
✓ Signal handlers
```

### Integration Tests

```
✓ API endpoints (CRUD)
✓ Authentication flow
✓ Authorization checks
✓ Payment processing
✓ Email notifications
✓ Celery tasks
✓ Cache behavior
```

### Performance Tests

```
✓ N+1 query detection
✓ Slow queries (>100ms)
✓ Large dataset handling
✓ Concurrent requests
✓ Memory leaks
```

---

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest --cov=apps --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📊 Example Test Report

```bash
$ pytest -v --cov=apps

tests/test_auth.py::TestLogin::test_login_with_email PASSED [ 5%]
tests/test_auth.py::TestLogin::test_login_with_username PASSED [ 10%]
tests/test_auth.py::TestRegister::test_register_success PASSED [ 15%]
tests/test_games.py::TestGameCreation::test_create_game PASSED [ 20%]
tests/test_games.py::TestGameFlow::test_complete_workflow PASSED [ 25%]
tests/test_payments.py::TestDeposit::test_deposit_stripe PASSED [ 30%]
tests/test_payments.py::TestWithdraw::test_withdraw_mtn PASSED [ 35%]

======================== Test Summary ========================
passed: 147
failed: 0
skipped: 3
errors: 0

======================== Coverage Summary ====================
Name                  Stmts   Miss  Cover
---------------------------------------------
apps/accounts        487     42    91%
apps/games           523     68    87%
apps/payments        612     38    94%
apps/referrals       389     51    87%
apps/analytics       256     28    89%
apps/core            342     35    90%
---------------------------------------------
TOTAL                2609   262    90%
```

---

## 🆘 Troubleshooting

### Common Issues

```bash
# Test collection errors
pytest --collect-only

# Verbose debugging
pytest -vv --tb=long

# Stop on first error
pytest -x

# Show local variables in traceback
pytest -l

# Capture output
pytest --capture=no

# Show slowest tests
pytest --durations=10
```

### Database Issues

```bash
# Reset test database
rm db.sqlite3
python manage.py migrate --settings=rumo_rush.settings.testing

# Use production DB for testing (careful!)
export USE_PRODUCTION_TEST_DB=True
pytest
```

---

## 📞 Support

- **Documentation** : https://docs.rumorush.com/testing
- **Issues** : https://github.com/ruffinh22/rhumo_rush/issues
- **Slack** : #testing channel

---

**Last Updated**: 15 November 2025  
**Maintainer**: RUMO RUSH QA Team
