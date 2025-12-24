# apps/core/pagination.py
# ============================

from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from collections import OrderedDict
from typing import Dict, Any, Optional
from django.core.paginator import Paginator, InvalidPage
from django.db.models import QuerySet
from . import PERFORMANCE_CONFIG


class StandardResultsSetPagination(PageNumberPagination):
    """
    Pagination standard pour l'API RUMO RUSH.
    Optimisée pour les performances et l'expérience utilisateur.
    """
    
    page_size = PERFORMANCE_CONFIG['PAGE_SIZE_DEFAULT']
    page_size_query_param = 'page_size'
    max_page_size = PERFORMANCE_CONFIG['PAGE_SIZE_MAX']
    
    def get_paginated_response(self, data: list) -> Response:
        """Response avec métadonnées étendues."""
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('has_next', self.page.has_next()),
            ('has_previous', self.page.has_previous()),
            ('start_index', self.page.start_index()),
            ('end_index', self.page.end_index()),
        ]))


class CursorPagination(PageNumberPagination):
    """
    Pagination par curseur pour les flux en temps réel.
    Optimisée pour les grandes collections et les mises à jour fréquentes.
    """
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    cursor_query_param = 'cursor'
    cursor_query_description = 'The pagination cursor value.'
    
    def paginate_queryset(self, queryset: QuerySet, request, view=None) -> Optional[list]:
        """Paginer avec un système de curseur."""
        
        self.request = request
        self.view = view
        
        # Obtenir le curseur depuis les paramètres
        cursor = request.query_params.get(self.cursor_query_param)
        
        if cursor:
            try:
                # Décoder le curseur (timestamp ou ID)
                cursor_value = self.decode_cursor(cursor)
                queryset = queryset.filter(created_at__lt=cursor_value)
            except ValueError:
                # Curseur invalide, ignorer
                pass
        
        # Ordonner par date décroissante
        queryset = queryset.order_by('-created_at')
        
        # Obtenir la page
        page_size = self.get_page_size(request)
        paginator = Paginator(queryset, page_size + 1)  # +1 pour détecter s'il y a une page suivante
        
        try:
            page = paginator.page(1)
        except InvalidPage:
            return None
        
        # Séparer les résultats et vérifier s'il y a une page suivante
        results = list(page.object_list)
        if len(results) > page_size:
            self.has_next = True
            results = results[:-1]  # Supprimer le dernier élément
        else:
            self.has_next = False
        
        self.results = results
        return results
    
    def get_paginated_response(self, data: list) -> Response:
        """Response avec curseur pour pagination continue."""
        
        next_cursor = None
        if self.has_next and self.results:
            # Le curseur suivant est la date du dernier élément
            last_item = self.results[-1]
            if hasattr(last_item, 'created_at'):
                next_cursor = self.encode_cursor(last_item.created_at)
        
        return Response(OrderedDict([
            ('next_cursor', next_cursor),
            ('has_next', self.has_next),
            ('page_size', self.get_page_size(self.request)),
            ('results', data),
        ]))
    
    def encode_cursor(self, timestamp) -> str:
        """Encoder le timestamp en curseur."""
        import base64
        return base64.b64encode(str(timestamp.timestamp()).encode()).decode()
    
    def decode_cursor(self, cursor: str):
        """Décoder le curseur en timestamp."""
        import base64
        from datetime import datetime
        timestamp = float(base64.b64decode(cursor.encode()).decode())
        return datetime.fromtimestamp(timestamp)


class GameHistoryPagination(StandardResultsSetPagination):
    """
    Pagination optimisée pour l'historique des jeux.
    """
    
    page_size = 15
    max_page_size = 50
    
    def get_paginated_response(self, data: list) -> Response:
        """Response avec statistiques supplémentaires."""
        
        # Calculer des statistiques sur la page courante
        stats = self.calculate_page_stats(data)
        
        response_data = OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('page_stats', stats),
        ])
        
        return Response(response_data)
    
    def calculate_page_stats(self, data: list) -> Dict[str, Any]:
        """Calculer les statistiques de la page."""
        if not data:
            return {}
        
        wins = sum(1 for game in data if game.get('winner_id') == self.request.user.id)
        losses = len(data) - wins
        total_bet = sum(float(game.get('bet_amount', 0)) for game in data)
        
        return {
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(data)) * 100 if data else 0,
            'total_bet_amount': total_bet,
            'games_count': len(data)
        }


class TransactionPagination(StandardResultsSetPagination):
    """
    Pagination pour les transactions avec groupement par date.
    """
    
    page_size = 25
    max_page_size = 100
    
    def get_paginated_response(self, data: list) -> Response:
        """Response avec groupement par date."""
        
        # Grouper les transactions par date
        grouped_data = self.group_by_date(data)
        
        # Calculer les totaux
        totals = self.calculate_totals(data)
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('grouped_results', grouped_data),
            ('totals', totals),
        ]))
    
    def group_by_date(self, data: list) -> Dict[str, list]:
        """Grouper les transactions par date."""
        grouped = {}
        
        for transaction in data:
            date_key = transaction.get('created_at', '')[:10]  # YYYY-MM-DD
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(transaction)
        
        return grouped
    
    def calculate_totals(self, data: list) -> Dict[str, float]:
        """Calculer les totaux par type de transaction."""
        totals = {
            'deposits': 0,
            'withdrawals': 0,
            'bets': 0,
            'wins': 0,
            'commissions': 0,
        }
        
        for transaction in data:
            transaction_type = transaction.get('transaction_type', '')
            amount = float(transaction.get('amount', 0))
            
            if transaction_type == 'deposit':
                totals['deposits'] += amount
            elif transaction_type == 'withdrawal':
                totals['withdrawals'] += amount
            elif transaction_type == 'bet':
                totals['bets'] += amount
            elif transaction_type == 'win':
                totals['wins'] += amount
            elif transaction_type == 'commission':
                totals['commissions'] += amount
        
        return totals


class LeaderboardPagination(StandardResultsSetPagination):
    """
    Pagination pour les classements avec position de l'utilisateur.
    """
    
    page_size = 50
    max_page_size = 100
    
    def get_paginated_response(self, data: list) -> Response:
        """Response avec position de l'utilisateur actuel."""
        
        # Trouver la position de l'utilisateur actuel
        user_position = self.find_user_position()
        
        # Ajouter les rangs aux résultats
        start_rank = (self.page.number - 1) * self.get_page_size(self.request) + 1
        for i, item in enumerate(data):
            item['rank'] = start_rank + i
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('user_position', user_position),
        ]))
    
    def find_user_position(self) -> Optional[Dict[str, Any]]:
        """Trouver la position de l'utilisateur actuel dans le classement."""
        if not hasattr(self.request, 'user') or not self.request.user.is_authenticated:
            return None
        
        try:
            # Chercher dans le queryset complet
            full_queryset = getattr(self, 'queryset', None)
            if not full_queryset:
                return None
            
            user_id = self.request.user.id
            for i, item in enumerate(full_queryset):
                if getattr(item, 'user_id', None) == user_id or getattr(item, 'id', None) == user_id:
                    return {
                        'rank': i + 1,
                        'user': {
                            'id': user_id,
                            'username': self.request.user.username
                        }
                    }
        except Exception:
            pass
        
        return None


class SmartPagination(LimitOffsetPagination):
    """
    Pagination intelligente qui s'adapte au type de contenu et à l'appareil.
    """
    
    default_limit = 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def get_limit(self, request):
        """Adapter la limite selon l'appareil."""
        
        # Détecter le type d'appareil
        is_mobile = getattr(request, 'is_mobile', False)
        
        # Limites adaptées
        if is_mobile:
            default_limit = 10  # Moins d'éléments sur mobile
            max_limit = 50
        else:
            default_limit = self.default_limit
            max_limit = self.max_limit
        
        if self.limit_query_param:
            try:
                limit = int(request.query_params[self.limit_query_param])
                if limit <= 0:
                    raise ValueError()
                return min(limit, max_limit)
            except (KeyError, ValueError):
                pass
        
        return default_limit
    
    def get_paginated_response(self, data: list) -> Response:
        """Response adaptée au contexte."""
        
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('pagination_info', {
                'limit': self.limit,
                'offset': self.offset,
                'device_optimized': getattr(self.request, 'is_mobile', False),
                'total_pages': (self.count + self.limit - 1) // self.limit,
                'current_page': (self.offset // self.limit) + 1,
            }),
        ]))


class InfiniteScrollPagination(CursorPagination):
    """
    Pagination pour le défilement infini (infinite scroll).
    Optimisée pour les applications mobiles et SPA.
    """
    
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50
    
    def get_paginated_response(self, data: list) -> Response:
        """Response optimisée pour le défilement infini."""
        
        return Response(OrderedDict([
            ('results', data),
            ('has_more', self.has_next),
            ('next_cursor', self.get_next_cursor()),
            ('count_estimate', self.get_count_estimate()),
            ('load_more_url', self.get_next_link()),
        ]))
    
    def get_next_cursor(self) -> Optional[str]:
        """Obtenir le curseur suivant pour le défilement."""
        if self.has_next and self.results:
            last_item = self.results[-1]
            if hasattr(last_item, 'created_at'):
                return self.encode_cursor(last_item.created_at)
        return None
    
    def get_count_estimate(self) -> str:
        """Estimation du nombre total d'éléments."""
        # Pour le défilement infini, on évite de compter tous les éléments
        # pour des raisons de performance
        if hasattr(self, 'paginator') and self.paginator.count < 1000:
            return f"{self.paginator.count} éléments"
        else:
            return "1000+ éléments"


class SearchResultsPagination(StandardResultsSetPagination):
    """
    Pagination pour les résultats de recherche avec méta-informations.
    """
    
    page_size = 20
    max_page_size = 50
    
    def get_paginated_response(self, data: list) -> Response:
        """Response avec informations de recherche."""
        
        search_query = self.request.query_params.get('search', '')
        search_time = getattr(self.request, 'search_time', 0)
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('search_meta', {
                'query': search_query,
                'search_time': f"{search_time:.3f}s",
                'results_found': self.page.paginator.count > 0,
                'suggestions': self.get_search_suggestions(search_query) if self.page.paginator.count == 0 else None,
            }),
        ]))
    
    def get_search_suggestions(self, query: str) -> list:
        """Générer des suggestions de recherche."""
        # Suggestions basiques - à améliorer avec un système plus sophistiqué
        common_terms = [
            'échecs', 'dames', 'ludo', 'cartes',
            'parties', 'tournois', 'classement',
            'gains', 'transactions', 'dépôt'
        ]
        
        suggestions = []
        query_lower = query.lower()
        
        for term in common_terms:
            if query_lower in term or term.startswith(query_lower[:3]):
                suggestions.append(term)
        
        return suggestions[:5]  # Maximum 5 suggestions
