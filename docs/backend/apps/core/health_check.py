# apps/core/health_check.py
"""
Advanced health check endpoints for RUMO RUSH backend.
Monitors database, cache, Celery, Redis, and other critical services.
"""
import logging
from django.db import connection
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from celery.app import current_app as celery_app
import redis
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """
    Comprehensive health check endpoint.
    Returns status of all critical services.
    """
    return Response({
        'status': 'ok',
        'service': 'RUMO RUSH API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'checks': {
            'database': check_database(),
            'cache': check_cache(),
            'celery': check_celery(),
            'redis': check_redis(),
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def detailed_health_check(request):
    """
    Detailed health check with response times and additional metrics.
    """
    checks = {
        'database': check_database_detailed(),
        'cache': check_cache_detailed(),
        'celery': check_celery_detailed(),
        'redis': check_redis_detailed(),
        'storage': check_storage(),
    }
    
    # Overall status
    all_ok = all(check.get('status') == 'ok' for check in checks.values())
    overall_status = 'ok' if all_ok else 'degraded'
    
    return Response({
        'status': overall_status,
        'service': 'RUMO RUSH API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'checks': checks,
    }, status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE)


def check_database():
    """Check database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return 'ok'
    except Exception as e:
        logger.error(f'Database health check failed: {str(e)}')
        return 'error'


def check_database_detailed():
    """Detailed database check with response time."""
    import time
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        response_time = (time.time() - start) * 1000  # Convert to ms
        
        user_count = User.objects.count()
        
        return {
            'status': 'ok',
            'response_time_ms': round(response_time, 2),
            'user_count': user_count,
            'engine': 'PostgreSQL' if 'postgresql' in connection.settings_dict['ENGINE'] else 'SQLite',
        }
    except Exception as e:
        logger.error(f'Database health check failed: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
        }


def check_cache():
    """Check cache (Redis) connectivity."""
    try:
        cache.set('health_check', 'ok', 10)
        value = cache.get('health_check')
        if value == 'ok':
            return 'ok'
        return 'error'
    except Exception as e:
        logger.error(f'Cache health check failed: {str(e)}')
        return 'error'


def check_cache_detailed():
    """Detailed cache check with stats."""
    import time
    try:
        start = time.time()
        test_key = 'health_check_test'
        test_value = 'ok'
        
        cache.set(test_key, test_value, 10)
        retrieved = cache.get(test_key)
        response_time = (time.time() - start) * 1000
        
        cache.delete(test_key)
        
        return {
            'status': 'ok' if retrieved == test_value else 'error',
            'response_time_ms': round(response_time, 2),
            'backend': 'Redis' if 'redis' in settings.CACHES['default']['BACKEND'] else 'LocMem',
        }
    except Exception as e:
        logger.error(f'Cache health check failed: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
        }


def check_celery():
    """Check Celery task queue."""
    try:
        celery_app.control.inspect().active()
        return 'ok'
    except Exception as e:
        logger.error(f'Celery health check failed: {str(e)}')
        return 'error'


def check_celery_detailed():
    """Detailed Celery check with active tasks."""
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active()
        scheduled = inspect.scheduled()
        registered = inspect.registered()
        
        return {
            'status': 'ok',
            'active_tasks': sum(len(tasks) for tasks in active.values()) if active else 0,
            'scheduled_tasks': sum(len(tasks) for tasks in scheduled.values()) if scheduled else 0,
            'registered_tasks': sum(len(tasks) for tasks in registered.values()) if registered else 0,
        }
    except Exception as e:
        logger.error(f'Celery health check failed: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
        }


def check_redis():
    """Check Redis connectivity."""
    try:
        redis_url = settings.CACHES['default']['LOCATION']
        r = redis.from_url(redis_url)
        r.ping()
        return 'ok'
    except Exception as e:
        logger.error(f'Redis health check failed: {str(e)}')
        return 'error'


def check_redis_detailed():
    """Detailed Redis check with info."""
    import time
    try:
        start = time.time()
        redis_url = settings.CACHES['default']['LOCATION']
        r = redis.from_url(redis_url)
        r.ping()
        response_time = (time.time() - start) * 1000
        
        info = r.info()
        
        return {
            'status': 'ok',
            'response_time_ms': round(response_time, 2),
            'version': info.get('redis_version', 'unknown'),
            'memory_used_mb': round(info.get('used_memory', 0) / 1024 / 1024, 2),
            'connected_clients': info.get('connected_clients', 0),
        }
    except Exception as e:
        logger.error(f'Redis health check failed: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
        }


def check_storage():
    """Check file storage availability."""
    try:
        from django.core.files.storage import default_storage
        
        test_content = b'health_check'
        test_name = 'health_check.txt'
        
        # Try to write
        default_storage.save(test_name, test_content)
        
        # Try to read
        content = default_storage.open(test_name).read()
        
        # Clean up
        default_storage.delete(test_name)
        
        return {
            'status': 'ok' if content == test_content else 'error',
            'type': 'local' if 'local' in settings.DEFAULT_FILE_STORAGE else 'remote',
        }
    except Exception as e:
        logger.error(f'Storage health check failed: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
        }


# URLs to add to apps/core/urls.py
"""
from . import health_check

urlpatterns = [
    ...
    path('health/', health_check.health_check, name='health_check'),
    path('health/detailed/', health_check.detailed_health_check, name='detailed_health_check'),
]
"""
