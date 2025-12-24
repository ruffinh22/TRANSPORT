"""Admin pour l'app Employés"""
from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'department', 'position', 'hire_date', 'is_active']
    list_filter = ['department', 'is_active', 'hire_date']
    search_fields = ['employee_id', 'user__email', 'position']
    readonly_fields = ['created_at', 'updated_at']
