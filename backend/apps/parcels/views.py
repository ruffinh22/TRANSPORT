"""Views pour l'app Parcels"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from .models import Parcel, ParcelTracking, ParcelCategory, ParcelInsurance
from .serializers import (
    ParcelListSerializer, ParcelDetailSerializer, ParcelCreateUpdateSerializer,
    ParcelTrackingSerializer, ParcelCategorySerializer, ParcelInsuranceSerializer,
    ParcelStatisticsSerializer
)
from apps.trips.models import Trip
from apps.users.models import User
import random
import string


class ParcelViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des colis"""
    queryset = Parcel.objects.all().prefetch_related('tracking_history', 'category')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'trip', 'priority', 'is_fragile']
    search_fields = ['sender__email', 'recipient_name', 'tracking_number']
    ordering_fields = ['created_at', 'total_price', 'weight']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon l'action"""
        if self.action == 'list':
            return ParcelListSerializer
        elif self.action == 'retrieve':
            return ParcelDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ParcelCreateUpdateSerializer
        return ParcelDetailSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Retourne les statistiques sur les colis"""
        parcels = self.get_queryset()
        
        stats = {
            'total_parcels': parcels.count(),
            'pending_parcels': parcels.filter(status='PENDING').count(),
            'delivered_parcels': parcels.filter(status='DELIVERED').count(),
            'lost_parcels': parcels.filter(status='LOST').count(),
            'total_revenue': parcels.aggregate(Sum('total_price'))['total_price__sum'] or 0,
            'average_price': parcels.aggregate(Avg('total_price'))['total_price__avg'] or 0,
            'total_weight': parcels.aggregate(Sum('weight'))['weight__sum'] or 0,
            'fragile_parcels': parcels.filter(is_fragile=True).count(),
        }
        
        serializer = ParcelStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def seed(self, request):
        """Génère des colis de démonstration"""
        try:
            trips = Trip.objects.all()[:5]
            users = User.objects.filter(is_staff=False)[:5]
            
            if not trips or not users:
                return Response(
                    {'error': 'Données insuffisantes (trajets ou utilisateurs)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            statuses = ['PENDING', 'IN_TRANSIT', 'DELIVERED', 'LOST']
            priorities = ['NORMAL', 'EXPRESS', 'URGENT']
            
            parcels_created = []
            
            # Générer 20 colis de démonstration
            for i in range(20):
                tracking_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                
                parcel = Parcel.objects.create(
                    trip=random.choice(trips),
                    sender=random.choice(users),
                    recipient_name=f'Destinataire {i+1}',
                    recipient_phone=f'+226 {random.randint(10000000, 99999999)}',
                    description=f'Colis de démonstration #{i+1}',
                    weight=random.uniform(0.5, 50),
                    total_price=random.randint(5000, 500000),
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    is_fragile=random.choice([True, False]),
                    tracking_number=tracking_number,
                )
                parcels_created.append(ParcelDetailSerializer(parcel).data)
            
            return Response({
                'message': f'✅ {len(parcels_created)} colis générés avec succès',
                'count': len(parcels_created),
                'parcels': parcels_created
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Retourne les colis groupés par statut"""
        from django.db.models import Count
        
        status_counts = self.get_queryset().values('status').annotate(
            count=Count('id'),
            total_revenue=Sum('total_price')
        )
        
        return Response(status_counts)
    
    @action(detail=False, methods=['get'])
    def my_parcels(self, request):
        """Retourne les colis envoyés par l'utilisateur connecté"""
        parcels = self.get_queryset().filter(sender=request.user)
        serializer = self.get_serializer(parcels, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Met à jour le statut d'un colis"""
        parcel = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        location = request.data.get('location', '')
        
        if not new_status:
            return Response(
                {'error': 'Le statut est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer une entrée de suivi
        ParcelTracking.objects.create(
            parcel=parcel,
            status=new_status,
            location=location,
            notes=notes,
            operator=request.user
        )
        
        # Mettre à jour le statut du colis
        parcel.status = new_status
        if new_status == 'DELIVERED':
            parcel.delivered_at = timezone.now()
        parcel.save()
        
        serializer = ParcelDetailSerializer(parcel)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Retourne l'historique de suivi d'un colis"""
        parcel = self.get_object()
        tracking = parcel.tracking_history.all()
        serializer = ParcelTrackingSerializer(tracking, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Crée plusieurs colis en une seule requête"""
        parcels_data = request.data.get('parcels', [])
        
        if not isinstance(parcels_data, list):
            return Response(
                {'error': 'Les données doivent être une liste'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_parcels = []
        errors = []
        
        for idx, parcel_data in enumerate(parcels_data):
            serializer = ParcelCreateUpdateSerializer(data=parcel_data)
            if serializer.is_valid():
                parcel = serializer.save()
                created_parcels.append(ParcelDetailSerializer(parcel).data)
            else:
                errors.append({'index': idx, 'errors': serializer.errors})
        
        return Response({
            'created': len(created_parcels),
            'parcels': created_parcels,
            'errors': errors
        }, status=status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS)
    
    @action(detail=False, methods=['get'])
    def revenue_by_date(self, request):
        """Retourne le revenu des colis groupé par date"""
        from django.db.models.functions import TruncDate
        
        revenue = self.get_queryset().filter(
            status='DELIVERED'
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            total=Sum('total_price'),
            count=Count('id')
        ).order_by('date')
        
        return Response(revenue)
    
    @action(detail=False, methods=['get'])
    def high_value_parcels(self, request):
        """Retourne les colis de haute valeur (assurés)"""
        threshold = request.query_params.get('threshold', 1000000)
        parcels = self.get_queryset().filter(
            is_insured=True,
            insurance_value__gte=threshold
        ).order_by('-insurance_value')
        
        serializer = ParcelListSerializer(parcels, many=True)
        return Response(serializer.data)


class ParcelCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet pour les catégories de colis"""
    queryset = ParcelCategory.objects.all()
    serializer_class = ParcelCategorySerializer
    permission_classes = [IsAuthenticated]


class ParcelInsuranceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les options d'assurance"""
    queryset = ParcelInsurance.objects.all()
    serializer_class = ParcelInsuranceSerializer
    permission_classes = [IsAuthenticated]


class ParcelTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour l'historique de suivi"""
    queryset = ParcelTracking.objects.all()
    serializer_class = ParcelTrackingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['parcel', 'status']
    ordering = ['-created_at']
