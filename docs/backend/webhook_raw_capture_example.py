# Test webhook endpoint pour capturer les données brutes FeexPay
# À ajouter dans apps/payments/views.py

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

# Logger spécial pour les webhooks
webhook_logger = logging.getLogger('feexpay.webhook.raw')

@method_decorator(csrf_exempt, name='dispatch')
class FeexPayWebhookRawCapture(View):
    """
    Endpoint de capture brute pour les webhooks FeexPay
    Capture TOUT ce que FeexPay envoie sans traitement
    """
    
    def post(self, request):
        timestamp = datetime.now().isoformat()
        
        # Capturer toutes les données brutes
        capture_data = {
            'timestamp': timestamp,
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'content_type': request.content_type,
            'body_raw': request.body.decode('utf-8', errors='ignore'),
            'GET_params': dict(request.GET),
            'POST_params': dict(request.POST),
            'META': {k: v for k, v in request.META.items() if isinstance(v, str)},
        }
        
        # Tentative de parsing JSON
        try:
            if request.content_type == 'application/json':
                capture_data['body_json'] = json.loads(request.body)
        except:
            capture_data['body_json'] = None
        
        # Log détaillé
        webhook_logger.info(f"WEBHOOK RAW CAPTURE: {json.dumps(capture_data, indent=2, ensure_ascii=False)}")
        
        # Sauvegarder dans un fichier aussi
        self._save_to_file(capture_data)
        
        # Affichage console pour debug
        self._print_capture(capture_data)
        
        # Répondre positivement pour que FeexPay continue d'envoyer
        return JsonResponse({
            'status': 'captured',
            'timestamp': timestamp,
            'message': 'Webhook captured successfully'
        })
    
    def get(self, request):
        """Pour les tests GET aussi"""
        return self.post(request)
    
    def _save_to_file(self, capture_data):
        """Sauvegarder la capture dans un fichier"""
        import os
        
        # Créer le dossier s'il n'existe pas
        os.makedirs('webhook_captures', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"webhook_raw_{timestamp}.json"
        filepath = os.path.join('webhook_captures', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(capture_data, f, indent=2, ensure_ascii=False)
    
    def _print_capture(self, capture_data):
        """Affichage console formaté"""
        print("\n" + "=" * 80)
        print(f"🔔 WEBHOOK REÇU - {capture_data['timestamp']}")
        print("=" * 80)
        
        print(f"📊 Méthode: {capture_data['method']}")
        print(f"🔗 Path: {capture_data['path']}")
        print(f"📄 Content-Type: {capture_data['content_type']}")
        
        print(f"\n📨 HEADERS:")
        print("-" * 40)
        for key, value in capture_data['headers'].items():
            print(f"{key}: {value}")
        
        if capture_data['GET_params']:
            print(f"\n🔍 GET PARAMS:")
            print("-" * 40)
            for key, value in capture_data['GET_params'].items():
                print(f"{key}: {value}")
        
        if capture_data['POST_params']:
            print(f"\n📋 POST PARAMS:")
            print("-" * 40)
            for key, value in capture_data['POST_params'].items():
                print(f"{key}: {value}")
        
        print(f"\n📄 BODY RAW:")
        print("-" * 40)
        print(capture_data['body_raw'])
        
        if capture_data['body_json']:
            print(f"\n📄 BODY JSON PARSED:")
            print("-" * 40)
            print(json.dumps(capture_data['body_json'], indent=2, ensure_ascii=False))
        
        print("=" * 80)

# À ajouter dans urls.py :
# path('webhook/feexpay/raw-capture/', FeexPayWebhookRawCapture.as_view(), name='feexpay_webhook_raw'),