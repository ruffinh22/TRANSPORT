"""Views pour l'app Employees"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from .models import Employee, EmployeeLeave, EmployeePayroll, EmployeePerformance
from .serializers import (
    EmployeeSerializer,
    EmployeeDetailedSerializer,
    EmployeeLeaveSerializer,
    EmployeePayrollSerializer,
    EmployeePerformanceSerializer,
)


class EmployeeFilter(filters.FilterSet):
    """Filtres avancés pour les employés"""
    class Meta:
        model = Employee
        fields = {
            'role': ['exact'],
            'status': ['exact'],
            'city': ['exact', 'icontains'],
            'hire_date': ['gte', 'lte'],
            'salary': ['gte', 'lte'],
        }


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet complet pour les employés"""
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = EmployeeFilter
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'document_id']
    ordering_fields = ['hire_date', 'salary', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        """Utilise le sérialiseur détaillé pour la récupération unique"""
        if self.action == 'retrieve':
            return EmployeeDetailedSerializer
        return self.serializer_class

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques globales sur les employés"""
        total = Employee.objects.count()
        active = Employee.objects.filter(status='active').count()
        by_role = Employee.objects.values('role').annotate(count=Count('id'))
        
        total_payroll = EmployeePayroll.objects.aggregate(
            total=Sum('net_salary')
        )['total'] or 0

        return Response({
            'total_employees': total,
            'active_employees': active,
            'inactive_employees': total - active,
            'by_role': list(by_role),
            'total_monthly_payroll': str(total_payroll),
        })

    @action(detail=True, methods=['get'])
    def performance_summary(self, request, pk=None):
        """Résumé de performance d'un employé"""
        employee = self.get_object()
        reviews = employee.performance_reviews.all()

        if not reviews.exists():
            return Response({
                'employee_id': employee.id,
                'message': 'Aucune évaluation de performance disponible'
            }, status=status.HTTP_404_NOT_FOUND)

        avg_rating = reviews.aggregate(Avg('overall_rating'))['overall_rating__avg']

        return Response({
            'employee_id': employee.id,
            'full_name': employee.get_full_name(),
            'average_rating': round(avg_rating, 2),
            'total_reviews': reviews.count(),
            'latest_review': reviews.first().evaluation_date if reviews.exists() else None,
        })

    @action(detail=True, methods=['get'])
    def leaves(self, request, pk=None):
        """Liste des congés d'un employé"""
        employee = self.get_object()
        leaves = employee.leaves.all()
        serializer = EmployeeLeaveSerializer(leaves, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def payroll(self, request, pk=None):
        """Historique de paie d'un employé"""
        employee = self.get_object()
        payrolls = employee.payrolls.all()
        serializer = EmployeePayrollSerializer(payrolls, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Mise à jour en masse du statut des employés"""
        employee_ids = request.data.get('employee_ids', [])
        new_status = request.data.get('status', '')

        if not employee_ids or not new_status:
            return Response(
                {'error': 'employee_ids et status sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Employee.objects.filter(id__in=employee_ids).update(status=new_status)

        return Response({
            'message': f'{len(employee_ids)} employés ont été mis à jour',
            'status': new_status
        })


class EmployeeLeaveViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des congés"""
    queryset = EmployeeLeave.objects.all()
    serializer_class = EmployeeLeaveSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'leave_type', 'status']
    ordering = ['-start_date']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuver une demande de congé"""
        leave = self.get_object()
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approval_date = timezone.now()
        leave.save()
        
        return Response({
            'message': 'Congé approuvé',
            'leave': EmployeeLeaveSerializer(leave).data
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejeter une demande de congé"""
        leave = self.get_object()
        leave.status = 'rejected'
        leave.save()
        
        return Response({
            'message': 'Congé rejeté',
            'leave': EmployeeLeaveSerializer(leave).data
        })


class EmployeePayrollViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion de la paie"""
    queryset = EmployeePayroll.objects.all()
    serializer_class = EmployeePayrollSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'year', 'month', 'status']
    ordering = ['-year', '-month']

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Résumé de la paie du mois"""
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year or not month:
            return Response(
                {'error': 'year et month sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payrolls = EmployeePayroll.objects.filter(year=year, month=month)
        total_net = payrolls.aggregate(Sum('net_salary'))['net_salary__sum'] or 0
        total_employees = payrolls.count()

        return Response({
            'year': year,
            'month': month,
            'total_employees': total_employees,
            'total_payroll': str(total_net),
            'payrolls': EmployeePayrollSerializer(payrolls, many=True).data
        })


class EmployeePerformanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les évaluations de performance"""
    queryset = EmployeePerformance.objects.all()
    serializer_class = EmployeePerformanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'evaluation_date']
    ordering = ['-evaluation_date']
