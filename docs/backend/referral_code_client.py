"""
Exemple complet d'intégration du système de codes de parrainage.
Peut être utilisé comme référence pour l'implémentation frontend.
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class ReferralCodeManager:
    """
    Gestionnaire client pour les codes de parrainage.
    Simplifie l'interaction avec l'API des codes de parrainage.
    """
    
    def __init__(self, api_base_url: str, auth_token: str):
        """
        Initialiser le gestionnaire.
        
        Args:
            api_base_url: URL de base de l'API (ex: http://localhost:8000/api/v1)
            auth_token: Token d'authentification JWT
        """
        self.api_url = f"{api_base_url}/referrals/codes"
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    # ===== GESTION DES CODES =====
    
    def get_all_codes(self) -> List[Dict]:
        """Obtenir tous les codes de parrainage de l'utilisateur."""
        response = requests.get(self.api_url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_code(self, code_id: str) -> Dict:
        """Obtenir les détails d'un code spécifique."""
        response = requests.get(f"{self.api_url}/{code_id}/", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_code(self, max_uses: int = 1000, expiration_date: Optional[str] = None) -> Dict:
        """
        Créer un nouveau code de parrainage.
        
        Args:
            max_uses: Nombre maximum d'utilisation (0 = illimité)
            expiration_date: Date d'expiration (format ISO 8601)
        
        Returns:
            Les données du code créé
        """
        payload = {
            'max_uses': max_uses,
            'expiration_date': expiration_date
        }
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # ===== PARTAGE =====
    
    def share_code(self, code_id: str, channel: str, message: str = '') -> Dict:
        """
        Partager un code via un canal spécifique.
        
        Args:
            code_id: ID du code à partager
            channel: Canal (whatsapp, telegram, email, etc.)
            message: Message personnalisé
        
        Returns:
            Les données de partage incluant les URLs
        """
        payload = {
            'channel': channel,
            'message': message
        }
        
        response = requests.post(
            f"{self.api_url}/{code_id}/share/",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def share_on_whatsapp(self, code_id: str, message: str = 'Rejoins-moi!'):
        """Partager sur WhatsApp."""
        return self.share_code(code_id, 'whatsapp', message)
    
    def share_on_telegram(self, code_id: str, message: str = 'Rejoins-moi!'):
        """Partager sur Telegram."""
        return self.share_code(code_id, 'telegram', message)
    
    def share_on_facebook(self, code_id: str, message: str = ''):
        """Partager sur Facebook."""
        return self.share_code(code_id, 'facebook', message)
    
    def share_on_twitter(self, code_id: str, message: str = ''):
        """Partager sur Twitter."""
        return self.share_code(code_id, 'twitter', message)
    
    def share_via_email(self, code_id: str, message: str = ''):
        """Partager par Email."""
        return self.share_code(code_id, 'email', message)
    
    def share_via_sms(self, code_id: str, message: str = ''):
        """Partager par SMS."""
        return self.share_code(code_id, 'sms', message)
    
    # ===== STATISTIQUES =====
    
    def get_code_stats(self, code_id: str) -> Dict:
        """Obtenir les statistiques d'un code."""
        response = requests.get(
            f"{self.api_url}/{code_id}/stats/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_conversions(self, code_id: str, page: int = 1, limit: int = 20) -> Dict:
        """
        Obtenir les conversions d'un code.
        
        Args:
            code_id: ID du code
            page: Numéro de page
            limit: Nombre de résultats par page
        
        Returns:
            Les conversions paginées
        """
        params = {'page': page, 'limit': limit}
        response = requests.get(
            f"{self.api_url}/{code_id}/conversions/",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_analytics(self) -> Dict:
        """Obtenir les analytiques globales."""
        response = requests.get(
            f"{self.api_url}/analytics/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # ===== GESTION DU CODE =====
    
    def activate_code(self, code_id: str) -> Dict:
        """Activer un code."""
        response = requests.post(
            f"{self.api_url}/{code_id}/activate/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def deactivate_code(self, code_id: str) -> Dict:
        """Désactiver un code."""
        response = requests.post(
            f"{self.api_url}/{code_id}/deactivate/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # ===== QR CODE =====
    
    def get_qr_code_url(self, code_id: str) -> str:
        """Obtenir l'URL du QR code."""
        return f"{self.api_url}/{code_id}/qr-code/"
    
    def get_qr_code_image(self, code_id: str) -> bytes:
        """Télécharger l'image du QR code."""
        response = requests.get(
            self.get_qr_code_url(code_id),
            headers={'Authorization': self.headers['Authorization']}
        )
        response.raise_for_status()
        return response.content


# ===== EXEMPLE D'UTILISATION =====

def example_usage():
    """Exemple complet d'utilisation du gestionnaire."""
    
    # Configuration
    api_url = "http://localhost:8000/api/v1"
    auth_token = "YOUR_JWT_TOKEN_HERE"
    
    # Créer le gestionnaire
    manager = ReferralCodeManager(api_url, auth_token)
    
    try:
        # 1. Créer un nouveau code
        print("📝 Création d'un nouveau code...")
        new_code = manager.create_code(
            max_uses=1000,
            expiration_date=(datetime.now() + timedelta(days=365)).isoformat()
        )
        code_id = new_code['id']
        print(f"✅ Code créé: {new_code['code']}")
        
        # 2. Partager le code
        print("\n📤 Partage du code sur WhatsApp...")
        share_result = manager.share_on_whatsapp(
            code_id,
            message="Rejoins-moi sur RUMO RUSH avec mon code de parrainage!"
        )
        print(f"✅ Partagé: {share_result['share_data']['share_url']}")
        
        # 3. Obtenir les statistiques
        print("\n📊 Récupération des statistiques...")
        stats = manager.get_code_stats(code_id)
        print(f"Clics: {stats['total_clicks']}")
        print(f"Conversions: {stats['total_conversions']}")
        print(f"Taux: {stats['conversion_rate']:.1f}%")
        print(f"Commission: {stats['total_commission']} FCFA")
        
        # 4. Obtenir les conversions
        print("\n👥 Utilisateurs convertis...")
        conversions = manager.get_conversions(code_id)
        for conv in conversions['conversions']:
            print(f"- {conv['username']} ({conv['email']})")
        
        # 5. Obtenir les analytiques globales
        print("\n📈 Analytiques globales...")
        analytics = manager.get_analytics()
        print(f"Total de codes: {analytics['total_codes']}")
        print(f"Total de clics: {analytics['total_clicks']}")
        print(f"Total de conversions: {analytics['total_conversions']}")
        
        # 6. Télécharger le QR code
        print("\n🔲 Téléchargement du QR code...")
        qr_image = manager.get_qr_code_image(code_id)
        with open('qr_code.png', 'wb') as f:
            f.write(qr_image)
        print("✅ QR code sauvegardé: qr_code.png")
        
        # 7. Lister tous les codes
        print("\n📋 Tous les codes...")
        all_codes = manager.get_all_codes()
        for code in all_codes:
            print(f"- {code['code']}: {code['total_clicks']} clics, {code['total_conversions']} conversions")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur: {e}")


# ===== CLASSE HELPER POUR FRONTEND =====

class ReferralCodeWidget:
    """Helper pour l'intégration dans le frontend."""
    
    def __init__(self, manager: ReferralCodeManager):
        self.manager = manager
    
    def render_widget_html(self, code_id: str) -> str:
        """Générer le HTML du widget."""
        code = self.manager.get_code(code_id)
        stats = self.manager.get_code_stats(code_id)
        
        html = f"""
        <div class="referral-widget">
            <h2>Mon Code de Parrainage</h2>
            
            <div class="code-display">
                <input type="text" value="{code['short_url']}" readonly />
                <button onclick="copyToClipboard()">Copier</button>
            </div>
            
            <div class="share-buttons">
                <button onclick="shareWhatsApp('{code_id}')">📱 WhatsApp</button>
                <button onclick="shareTelegram('{code_id}')">✈️ Telegram</button>
                <button onclick="shareEmail('{code_id}')">📧 Email</button>
                <button onclick="shareFacebook('{code_id}')">👍 Facebook</button>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <span>Clics</span>
                    <strong>{stats['total_clicks']}</strong>
                </div>
                <div class="stat">
                    <span>Conversions</span>
                    <strong>{stats['total_conversions']}</strong>
                </div>
                <div class="stat">
                    <span>Taux</span>
                    <strong>{stats['conversion_rate']:.1f}%</strong>
                </div>
            </div>
            
            <div class="qr-code">
                <img src="{self.manager.get_qr_code_url(code_id)}" alt="QR Code" />
            </div>
        </div>
        """
        
        return html
    
    def render_stats_chart(self, code_id: str) -> Dict:
        """Données pour créer un graphique des statistiques."""
        code = self.manager.get_code(code_id)
        
        return {
            'code': code['code'],
            'clicks': code['total_clicks'],
            'conversions': code['total_conversions'],
            'conversion_rate': code['conversion_rate'],
            'commission': str(code['total_commission_generated']),
            'channels': [
                {
                    'name': share['channel'],
                    'clicks': share['click_count'],
                    'conversions': share['conversion_count']
                }
                for share in code['shares']
            ]
        }


if __name__ == '__main__':
    # Lancer l'exemple
    example_usage()
