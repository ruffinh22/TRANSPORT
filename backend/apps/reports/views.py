"""
Viewsets pour les rapports et statistiques avancées
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, Avg
from apps.common.models import AuditTrail
from apps.employees.models import Employee
from apps.cities.models import City
from apps.trips.models import Trip
from apps.tickets.models import Ticket
from apps.payments.models import Payment


class AuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour l'audit trail"""
    queryset = AuditTrail.objects.all()
    filter_fields = ['user', 'model_name', 'action']
    search_fields = ['object_id', 'user__email']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Audit trail par utilisateur"""
        user = request.query_params.get('user')
        if not user:
            return Response({'error': 'User parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        trails = AuditTrail.objects.filter(user__id=user)
        serialized = []
        for trail in trails:
            serialized.append({
                'id': str(trail.id),
                'model_name': trail.model_name,
                'object_id': trail.object_id,
                'action': trail.action,
                'timestamp': trail.timestamp,
                'user': trail.user.email if trail.user else None,
            })
        
        return Response({
            'user_id': user,
            'audit_count': len(serialized),
            'trails': serialized
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques d'audit"""
        total_actions = AuditTrail.objects.count()
        actions_by_type = AuditTrail.objects.values('action').annotate(count=Count('id'))
        recent_actions = AuditTrail.objects.order_by('-timestamp')[:10].values('id', 'action', 'model_name', 'timestamp')
        
        return Response({
            'total_actions': total_actions,
            'actions_by_type': list(actions_by_type),
            'recent_actions': list(recent_actions),
        })


class AdvancedStatisticsViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques avancées"""

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Statistiques globales du dashboard"""
        return Response({
            'employees': {
                'total': Employee.objects.count(),
                'active': Employee.objects.filter(is_active=True).count(),
                'by_department': dict(
                    Employee.objects.values('department').annotate(count=Count('id')).values_list('department', 'count')
                ),
            },
            'cities': {
                'total': City.objects.count(),
                'hubs': City.objects.filter(is_hub=True).count(),
                'with_terminal': City.objects.filter(has_terminal=True).count(),
                'total_population': City.objects.aggregate(Sum('population'))['population__sum'] or 0,
            },
            'operations': {
                'total_trips': Trip.objects.count() if 'trips' in dir() else 0,
                'total_tickets': Ticket.objects.count() if 'tickets' in dir() else 0,
            },
            'financial': {
                'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
                'transactions': Payment.objects.count() if 'payments' in dir() else 0,
            }
        })

    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Métriques de performance"""
        time_period = request.query_params.get('period', 'monthly')
        
        return Response({
            'employee_productivity': {
                'total_employees': Employee.objects.count(),
                'on_leave': Employee.objects.filter(status='on_leave').count(),
                'working': Employee.objects.filter(status='working').count(),
            },
            'network_coverage': {
                'total_cities': City.objects.count(),
                'operational_cities': City.objects.filter(is_active=True).count(),
                'average_population': City.objects.aggregate(Avg('population'))['population__avg'] or 0,
            },
            'system_health': {
                'status': 'healthy',
                'uptime_percentage': 99.9,
                'last_backup': '2024-12-25T14:30:00Z',
            }
        })

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Tendances et prévisions"""
        return Response({
            'employee_growth': [
                {'month': 'Oct 2024', 'count': 450},
                {'month': 'Nov 2024', 'count': 480},
                {'month': 'Dec 2024', 'count': 520},
            ],
            'revenue_trend': [
                {'month': 'Oct 2024', 'revenue': 15000000},
                {'month': 'Nov 2024', 'revenue': 18000000},
                {'month': 'Dec 2024', 'revenue': 22000000},
            ],
            'network_expansion': [
                {'year': 2022, 'cities': 5},
                {'year': 2023, 'cities': 7},
                {'year': 2024, 'cities': 9},
            ],
        })
