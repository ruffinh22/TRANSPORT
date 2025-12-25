"""Views pour l'app Cities"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from .models import City
from .serializers import CitySerializer, CityListSerializer, CityDetailSerializer


class CityViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les villes"""
    queryset = City.objects.all()
    serializer_class = CitySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region', 'is_active', 'is_hub', 'has_terminal', 'has_parking']
    search_fields = ['name', 'code', 'address', 'region']
    ordering_fields = ['name', 'population', 'trip_count', 'annual_revenue', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return CityListSerializer
        elif self.action == 'retrieve':
            return CityDetailSerializer
        return CitySerializer

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques globales des villes"""
        total_cities = City.objects.filter(is_active=True).count()
        hub_count = City.objects.filter(is_active=True, is_hub=True).count()
        terminal_count = City.objects.filter(is_active=True, has_terminal=True).count()
        
        total_revenue = City.objects.filter(is_active=True).aggregate(
            total=Sum('annual_revenue')
        )['total'] or 0
        
        total_population = City.objects.filter(is_active=True).aggregate(
            total=Sum('population')
        )['total'] or 0
        
        return Response({
            'total_cities': total_cities,
            'hubs': hub_count,
            'terminals': terminal_count,
            'total_revenue': float(total_revenue),
            'total_population': total_population,
            'average_revenue': float(total_revenue / total_cities) if total_cities > 0 else 0,
        })

    @action(detail=False, methods=['get'])
    def hubs(self, request):
        """Liste les hubs majeurs"""
        hubs = City.objects.filter(is_active=True, is_hub=True).order_by('-trip_count')
        serializer = self.get_serializer(hubs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def operational(self, request):
        """Liste les villes opérationnelles"""
        from django.db.models import Q
        operational_cities = City.objects.filter(
            is_active=True
        ).filter(Q(is_hub=True) | Q(has_terminal=True))
        serializer = self.get_serializer(operational_cities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_statistics(self, request, pk=None):
        """Met à jour les statistiques d'une ville"""
        city = self.get_object()
        city.update_statistics()
        serializer = self.get_serializer(city)
        return Response(
            {
                'message': 'Statistiques mises à jour',
                'city': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def update_all_statistics(self, request):
        """Met à jour les statistiques de toutes les villes"""
        cities = City.objects.filter(is_active=True)
        updated_count = 0
        
        for city in cities:
            city.update_statistics()
            updated_count += 1
        
        return Response(
            {
                'message': f'{updated_count} villes mises à jour',
                'updated_count': updated_count
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def by_region(self, request):
        """Groupe les villes par région"""
        region = request.query_params.get('region')
        if not region:
            return Response(
                {'error': 'Le paramètre region est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cities = City.objects.filter(is_active=True, region=region).order_by('name')
        serializer = self.get_serializer(cities, many=True)
        return Response({
            'region': region,
            'count': len(serializer.data),
            'cities': serializer.data
        })

    @action(detail=False, methods=['get'])
    def geolocation(self, request):
        """Retourne toutes les villes avec coordonnées GPS"""
        cities = City.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).values('id', 'name', 'latitude', 'longitude', 'is_hub', 'has_terminal')
        
        return Response({
            'count': len(cities),
            'cities': list(cities)
        })

    @action(detail=True, methods=['get'])
    def routes_from(self, request, pk=None):
        """Liste les trajets partant de cette ville"""
        city = self.get_object()
        from apps.trips.models import Trip
        from apps.trips.serializers import TripSerializer
        
        trips = Trip.objects.filter(departure_city=city.name)
        serializer = TripSerializer(trips, many=True)
        return Response({
            'city': city.name,
            'route_count': len(serializer.data),
            'routes': serializer.data
        })

    @action(detail=True, methods=['get'])
    def routes_to(self, request, pk=None):
        """Liste les trajets arrivant à cette ville"""
        city = self.get_object()
        from apps.trips.models import Trip
        from apps.trips.serializers import TripSerializer
        
        trips = Trip.objects.filter(arrival_city=city.name)
        serializer = TripSerializer(trips, many=True)
        return Response({
            'city': city.name,
            'route_count': len(serializer.data),
            'routes': serializer.data
        })
