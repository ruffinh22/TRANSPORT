"""URLs pour l'app Employees"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet,
    EmployeeLeaveViewSet,
    EmployeePayrollViewSet,
    EmployeePerformanceViewSet,
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'leaves', EmployeeLeaveViewSet, basename='employee-leave')
router.register(r'payroll', EmployeePayrollViewSet, basename='employee-payroll')
router.register(r'performance', EmployeePerformanceViewSet, basename='employee-performance')

urlpatterns = [
    path('', include(router.urls)),
]
