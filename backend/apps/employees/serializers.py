"""Serializers pour l'app Employees"""
from rest_framework import serializers
from .models import Employee, EmployeeLeave, EmployeePayroll, EmployeePerformance
from apps.users.models import User


class EmployeeSerializer(serializers.ModelSerializer):
    """Sérialiseur principal pour les employés"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'role', 'role_display', 'hire_date',
            'salary', 'commission_rate', 'status', 'status_display',
            'city', 'document_id', 'document_type', 'document_expiry',
            'user', 'user_email', 'trips_completed', 'parcels_delivered',
            'total_earnings', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'trips_completed', 'total_earnings']


class EmployeeLeaveSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les congés employés"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EmployeeLeave
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_display',
            'start_date', 'end_date', 'duration_days', 'reason',
            'status', 'status_display', 'approved_by', 'approval_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approval_date']


class EmployeePayrollSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les fiches de paie"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EmployeePayroll
        fields = [
            'id', 'employee', 'employee_name', 'year', 'month',
            'base_salary', 'bonus', 'commission', 'transport_allowance',
            'social_security', 'tax', 'advance',
            'gross_salary', 'net_salary', 'status', 'status_display',
            'payment_date', 'payment_method', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'gross_salary', 'net_salary']


class EmployeePerformanceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les évaluations de performance"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    evaluator_name = serializers.CharField(source='evaluator.get_full_name', read_only=True)

    class Meta:
        model = EmployeePerformance
        fields = [
            'id', 'employee', 'employee_name', 'evaluation_date',
            'evaluator', 'evaluator_name',
            'punctuality', 'professionalism', 'quality_of_work',
            'teamwork', 'initiative', 'overall_rating',
            'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeDetailedSerializer(EmployeeSerializer):
    """Sérialiseur détaillé incluant les congés et les évaluations"""
    leaves = EmployeeLeaveSerializer(many=True, read_only=True)
    payrolls = EmployeePayrollSerializer(many=True, read_only=True)
    performance_reviews = EmployeePerformanceSerializer(many=True, read_only=True)

    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + [
            'leaves', 'payrolls', 'performance_reviews'
        ]
