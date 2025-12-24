# tests/conftest.py
"""
Pytest configuration and fixtures for RUMO RUSH backend tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import factory

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""
    
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
        password = extracted or 'defaultpassword123'
        obj.set_password(password)
        obj.save()


@pytest.fixture
def user(db):
    """Create a basic test user."""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = UserFactory(is_staff=True, is_superuser=True)
    user.set_password('admin123')
    user.save()
    return user


@pytest.fixture
def authenticated_user(db):
    """Create and return an authenticated user."""
    return UserFactory(password='testpass123')


@pytest.fixture
def api_client():
    """Return a REST API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(authenticated_user):
    """Return an authenticated API client with JWT token."""
    client = APIClient()
    refresh = RefreshToken.for_user(authenticated_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def admin_client(admin_user):
    """Return an authenticated admin API client."""
    client = APIClient()
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def mock_stripe(mocker):
    """Mock Stripe API calls."""
    return mocker.patch('stripe.Charge.create')


@pytest.fixture
def mock_celery(mocker):
    """Mock Celery task execution."""
    return mocker.patch('celery.app.task.Task.delay')
