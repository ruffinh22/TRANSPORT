"""
URL Configuration pour TKF Project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/cities/', include('apps.cities.urls')),
    path('api/v1/vehicles/', include('apps.vehicles.urls')),
    path('api/v1/employees/', include('apps.employees.urls')),
    path('api/v1/trips/', include('apps.trips.urls')),
    path('api/v1/tickets/', include('apps.tickets.urls')),
    path('api/v1/parcels/', include('apps.parcels.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/revenues/', include('apps.revenues.urls')),
]

# Debug Toolbar
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'apps.common.views.custom_404'
handler500 = 'apps.common.views.custom_500'
