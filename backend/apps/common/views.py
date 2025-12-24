"""Views pour l'app Common"""
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


def custom_404(request, exception):
    """Handle 404 errors"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Handle 500 errors"""
    return render(request, '500.html', status=500)


class HealthCheckView(APIView):
    """Health check endpoint"""
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'message': 'API is running'
        }, status=status.HTTP_200_OK)
