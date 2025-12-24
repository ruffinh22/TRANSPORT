#!/usr/bin/env python
"""
Capture et analyse brute des retours FeexPay
Usage: python capture_feexpay_raw.py
"""

import os
import sys
import django
import json
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from apps.payments.models import FeexPayTransaction
from apps.payments.services.feexpay_service import FeexPayService
import requests

class FeexPayRawCapture:
    def __init__(self):
        self.feexpay_service = FeexPayService()
        
    def capture_transaction_raw(self, reference):
        """Capturer les données brutes d'une transaction"""
        print(f"🔍 Capture brute pour référence: {reference}")
        print("=" * 60)
        
        try:
            # Appel direct à l'API FeexPay pour récupérer les données brutes
            url = f"{self.feexpay_service.base_url}/transaction/{reference}"
            headers = {
                'Authorization': f'Bearer {self.feexpay_service.api_key}',
                'Content-Type': 'application/json'
            }
            
            print(f"🌐 URL appelée: {url}")
            print(f"🔑 Headers: {json.dumps(dict(headers), indent=2)}")
            print("\n" + "=" * 60)
            
            response = requests.get(url, headers=headers)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"⏰ Timestamp: {datetime.now().isoformat()}")
            print("\n📨 HEADERS DE RÉPONSE:")
            print("-" * 40)
            for header, value in response.headers.items():
                print(f"{header}: {value}")
            
            print("\n📄 CONTENU BRUT DE LA RÉPONSE:")
            print("-" * 40)
            raw_content = response.text
            print(f"Taille: {len(raw_content)} caractères")
            print(f"Contenu brut:\n{raw_content}")
            
            # Tentative de parsing JSON si possible
            print("\n🔧 ANALYSE DU CONTENU:")
            print("-" * 40)
            try:
                json_data = response.json()
                print("✅ JSON valide détecté")
                print(f"📋 Données parsées:\n{json.dumps(json_data, indent=2, ensure_ascii=False)}")
                
                # Analyse détaillée des champs
                print("\n🔍 ANALYSE DES CHAMPS:")
                print("-" * 40)
                self._analyze_fields(json_data)
                
            except json.JSONDecodeError as e:
                print(f"❌ Erreur parsing JSON: {str(e)}")
                print("🔤 Le contenu n'est pas du JSON valide")
                
                # Tentative d'analyse du contenu texte
                self._analyze_text_content(raw_content)
            
            # Sauvegarder la capture
            self._save_capture(reference, response)
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': raw_content,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la capture: {str(e)}")
            return None
    
    def _analyze_fields(self, data, prefix=""):
        """Analyser récursivement les champs JSON"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                value_type = type(value).__name__
                
                if isinstance(value, (dict, list)):
                    print(f"📁 {current_path} ({value_type})")
                    self._analyze_fields(value, current_path)
                else:
                    print(f"📄 {current_path}: {value} ({value_type})")
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{prefix}[{i}]"
                self._analyze_fields(item, current_path)
    
    def _analyze_text_content(self, content):
        """Analyser le contenu texte"""
        print(f"📊 Longueur: {len(content)} caractères")
        print(f"📝 Lignes: {content.count(chr(10)) + 1}")
        
        # Chercher des patterns communs
        patterns = [
            ('XML', '<'),
            ('HTML', '<html'),
            ('Form Data', '='),
            ('CSV', ','),
            ('Pipe Separated', '|'),
        ]
        
        for pattern_name, pattern in patterns:
            if pattern in content.lower():
                print(f"🔍 Pattern détecté: {pattern_name}")
    
    def _save_capture(self, reference, response):
        """Sauvegarder la capture dans un fichier"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"feexpay_capture_{reference}_{timestamp}.json"
        
        capture_data = {
            'reference': reference,
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'url': response.url
        }
        
        # Créer le dossier captures s'il n'existe pas
        os.makedirs('captures', exist_ok=True)
        
        filepath = os.path.join('captures', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(capture_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Capture sauvegardée: {filepath}")
    
    def capture_all_pending(self):
        """Capturer toutes les transactions en attente"""
        print("🔄 Capture de toutes les transactions en attente...")
        print("=" * 60)
        
        pending_txs = FeexPayTransaction.objects.filter(status='pending')
        
        if not pending_txs.exists():
            print("✅ Aucune transaction en attente à capturer")
            return
        
        captures = []
        for tx in pending_txs:
            print(f"\n📋 Traitement: {tx.external_reference}")
            capture = self.capture_transaction_raw(tx.external_reference)
            if capture:
                captures.append({
                    'reference': tx.external_reference,
                    'capture': capture
                })
        
        print(f"\n✅ Capture terminée: {len(captures)} transactions traitées")
        return captures
    
    def webhook_simulator(self, reference):
        """Simuler la réception d'un webhook pour voir les données"""
        print(f"🎯 Simulation webhook pour: {reference}")
        print("=" * 60)
        
        # Récupérer les données de la transaction
        capture = self.capture_transaction_raw(reference)
        
        if not capture:
            return
        
        print(f"\n🔧 SIMULATION DU TRAITEMENT:")
        print("-" * 40)
        
        # Simuler ce qu'on recevrait en webhook
        try:
            data = json.loads(capture['content'])
            
            print("📨 Données reçues en webhook (simulation):")
            webhook_data = {
                'event': 'transaction_updated',
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            print(json.dumps(webhook_data, indent=2, ensure_ascii=False))
            
            # Montrer comment on pourrait parser
            print(f"\n🔧 EXTRACTION POSSIBLE:")
            print("-" * 40)
            
            if 'status' in data:
                print(f"Status: {data['status']}")
            if 'amount' in data:
                print(f"Montant: {data['amount']}")
            if 'reference' in data:
                print(f"Référence: {data['reference']}")
            if 'transaction_id' in data:
                print(f"ID Transaction: {data['transaction_id']}")
                
        except:
            print("❌ Impossible de simuler - données non JSON")
    
    def interactive_mode(self):
        """Mode interactif pour captures"""
        print("🎮 Mode Capture FeexPay Interactif")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Capturer une transaction spécifique")
            print("2. Capturer toutes les transactions en attente")
            print("3. Simuler webhook pour une référence")
            print("4. Lister les captures sauvegardées")
            print("5. Voir une capture sauvegardée")
            print("0. Quitter")
            
            choice = input("\nChoisir (0-5): ").strip()
            
            if choice == "1":
                reference = input("Référence à capturer: ").strip()
                if reference:
                    self.capture_transaction_raw(reference)
                    
            elif choice == "2":
                self.capture_all_pending()
                
            elif choice == "3":
                reference = input("Référence pour simulation webhook: ").strip()
                if reference:
                    self.webhook_simulator(reference)
                    
            elif choice == "4":
                self.list_captures()
                
            elif choice == "5":
                filename = input("Nom du fichier de capture: ").strip()
                if filename:
                    self.show_capture(filename)
                    
            elif choice == "0":
                print("👋 Au revoir!")
                break
            else:
                print("❌ Option invalide")
    
    def list_captures(self):
        """Lister les captures sauvegardées"""
        captures_dir = 'captures'
        if not os.path.exists(captures_dir):
            print("📁 Aucun dossier de captures trouvé")
            return
        
        files = [f for f in os.listdir(captures_dir) if f.endswith('.json')]
        
        if not files:
            print("📄 Aucune capture trouvée")
            return
        
        print(f"📋 Captures disponibles ({len(files)}):")
        print("-" * 40)
        for file in sorted(files):
            filepath = os.path.join(captures_dir, file)
            size = os.path.getsize(filepath)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            print(f"📄 {file} ({size} bytes) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def show_capture(self, filename):
        """Afficher une capture sauvegardée"""
        filepath = os.path.join('captures', filename)
        
        if not os.path.exists(filepath):
            print(f"❌ Fichier non trouvé: {filepath}")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                capture_data = json.load(f)
            
            print(f"📄 Capture: {filename}")
            print("=" * 60)
            print(f"🔗 Référence: {capture_data.get('reference', 'N/A')}")
            print(f"⏰ Timestamp: {capture_data.get('timestamp', 'N/A')}")
            print(f"📊 Status Code: {capture_data.get('status_code', 'N/A')}")
            print(f"🌐 URL: {capture_data.get('url', 'N/A')}")
            
            print(f"\n📨 Headers:")
            print("-" * 40)
            headers = capture_data.get('headers', {})
            for key, value in headers.items():
                print(f"{key}: {value}")
            
            print(f"\n📄 Contenu:")
            print("-" * 40)
            content = capture_data.get('content', '')
            
            # Tentative de formater le JSON si possible
            try:
                json_content = json.loads(content)
                print(json.dumps(json_content, indent=2, ensure_ascii=False))
            except:
                print(content)
                
        except Exception as e:
            print(f"❌ Erreur lecture fichier: {str(e)}")

def main():
    capture = FeexPayRawCapture()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "capture" and len(sys.argv) > 2:
            reference = sys.argv[2]
            capture.capture_transaction_raw(reference)
            
        elif command == "pending":
            capture.capture_all_pending()
            
        elif command == "webhook" and len(sys.argv) > 2:
            reference = sys.argv[2]
            capture.webhook_simulator(reference)
            
        elif command == "list":
            capture.list_captures()
            
        else:
            print_help()
    else:
        capture.interactive_mode()

def print_help():
    print("""
🔍 FeexPay Raw Capture - Commandes:

python capture_feexpay_raw.py                    # Mode interactif
python capture_feexpay_raw.py capture REF123     # Capturer une référence
python capture_feexpay_raw.py pending            # Capturer toutes les en attente
python capture_feexpay_raw.py webhook REF123     # Simuler webhook
python capture_feexpay_raw.py list               # Lister les captures

Les captures sont sauvegardées dans le dossier 'captures/'
""")

if __name__ == "__main__":
    main()