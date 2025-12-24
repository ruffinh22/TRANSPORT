# apps/core/utils.py
# ======================

import hashlib
import secrets
import string
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import logging

from . import SUPPORTED_CURRENCIES, DEFAULT_EXCHANGE_RATES

logger = logging.getLogger(__name__)


# ===== UTILITAIRES RÉSEAU ET CLIENT =====

def get_client_ip(request) -> str:
    """Obtenir l'adresse IP du client."""
    
    # Vérifier les headers de proxy
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    return ip


def extract_client_info(request) -> Dict[str, Any]:
    """Extraire les informations du client depuis la requête."""
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Détection basique du type d'appareil
    device_type = 'desktop'
    if 'Mobile' in user_agent or 'Android' in user_agent:
        device_type = 'mobile'
    elif 'Tablet' in user_agent or 'iPad' in user_agent:
        device_type = 'tablet'
    
    # Détection du navigateur
    browser = 'unknown'
    if 'Chrome' in user_agent:
        browser = 'chrome'
    elif 'Firefox' in user_agent:
        browser = 'firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        browser = 'safari'
    elif 'Edge' in user_agent:
        browser = 'edge'
    
    return {
        'ip_address': get_client_ip(request),
        'user_agent': user_agent,
        'device_type': device_type,
        'browser': browser,
        'timestamp': timezone.now().isoformat()
    }


# ===== UTILITAIRES DE GÉNÉRATION =====

def generate_referral_code(length: int = 8) -> str:
    """Générer un code de parrainage unique."""
    
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_transaction_id() -> str:
    """Générer un ID de transaction unique."""
    
    prefix = 'TXN'
    timestamp = int(timezone.now().timestamp())
    random_part = secrets.token_hex(4).upper()
    
    return f"{prefix}-{timestamp}-{random_part}"


def generate_game_id() -> str:
    """Générer un ID de jeu unique."""
    
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """Générer un token sécurisé."""
    
    return secrets.token_urlsafe(length)


def generate_otp_code(length: int = 6) -> str:
    """Générer un code OTP numérique."""
    
    return ''.join(secrets.choice(string.digits) for _ in range(length))


# ===== UTILITAIRES DE CHIFFREMENT =====

def hash_password(password: str) -> str:
    """Hasher un mot de passe avec bcrypt."""
    
    import bcrypt
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Vérifier un mot de passe contre son hash."""
    
    import bcrypt
    
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )


def encrypt_sensitive_data(data: str, key: str = None) -> str:
    """Chiffrer des données sensibles avec AES."""
    
    from cryptography.fernet import Fernet
    
    if not key:
        key = getattr(settings, 'ENCRYPTION_KEY', Fernet.generate_key())
    
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    
    return encrypted_data.decode()


def decrypt_sensitive_data(encrypted_data: str, key: str = None) -> str:
    """Déchiffrer des données sensibles."""
    
    from cryptography.fernet import Fernet
    
    if not key:
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            raise ValueError("Clé de chiffrement requise")
    
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data.encode())
    
    return decrypted_data.decode()


def generate_hash(data: str, algorithm: str = 'sha256') -> str:
    """Générer un hash cryptographique."""
    
    hash_algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }
    
    hasher = hash_algorithms.get(algorithm, hashlib.sha256)
    return hasher(data.encode()).hexdigest()


# ===== UTILITAIRES FINANCIERS =====

def convert_currency(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """Convertir un montant d'une devise à une autre."""
    
    if from_currency == to_currency:
        return amount
    
    # Obtenir le taux de change (cache puis API externe)
    rate = get_exchange_rate(from_currency, to_currency)
    
    if not rate:
        logger.error(f"Taux de change indisponible: {from_currency} -> {to_currency}")
        return amount  # Retourner le montant original en cas d'erreur
    
    converted = amount * Decimal(str(rate))
    
    # Arrondir selon la devise cible
    target_currency_config = SUPPORTED_CURRENCIES.get(to_currency, {})
    decimal_places = target_currency_config.get('decimal_places', 2)
    
    return converted.quantize(
        Decimal('0.' + '0' * decimal_places), 
        rounding=ROUND_HALF_UP
    )


def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[float]:
    """Obtenir le taux de change entre deux devises."""
    
    # Vérifier le cache
    cache_key = f"exchange_rate:{from_currency}:{to_currency}"
    rate = cache.get(cache_key)
    
    if rate:
        return rate
    
    # Obtenir depuis les taux par défaut
    default_rates = DEFAULT_EXCHANGE_RATES.get(from_currency, {})
    rate = default_rates.get(to_currency)
    
    if rate:
        # Mettre en cache pour 1 heure
        cache.set(cache_key, rate, 3600)
        return rate
    
    # TODO: Intégrer une API de taux de change externe
    logger.warning(f"Taux de change non trouvé: {from_currency} -> {to_currency}")
    return None


def calculate_commission(amount: Decimal, rate: float) -> Decimal:
    """Calculer une commission."""
    
    commission = amount * Decimal(str(rate))
    return commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_platform_commission(total_bet: Decimal) -> Decimal:
    """Calculer la commission de la plateforme (14%)."""
    
    from . import BUSINESS_LIMITS
    
    commission_rate = BUSINESS_LIMITS['PLATFORM_COMMISSION_RATE']
    return calculate_commission(total_bet, commission_rate)


def calculate_referral_commission(bet_amount: Decimal) -> Decimal:
    """Calculer la commission de parrainage (10%)."""
    
    from . import BUSINESS_LIMITS
    
    commission_rate = BUSINESS_LIMITS['REFERRAL_COMMISSION_RATE']
    return calculate_commission(bet_amount, commission_rate)


def format_currency(amount: Decimal, currency: str) -> str:
    """Formater un montant selon la devise."""
    
    currency_config = SUPPORTED_CURRENCIES.get(currency, {})
    symbol = currency_config.get('symbol', currency)
    decimal_places = currency_config.get('decimal_places', 2)
    
    # Formater avec le bon nombre de décimales
    if decimal_places == 0:
        formatted = f"{int(amount):,}"
    else:
        formatted = f"{amount:,.{decimal_places}f}"
    
    # Ajouter le symbole selon la devise
    if currency in ['EUR']:
        return f"{formatted} {symbol}"
    elif currency in ['USD']:
        return f"{symbol}{formatted}"
    else:  # FCFA et autres
        return f"{formatted} {symbol}"


# ===== UTILITAIRES DE VALIDATION =====

def validate_phone_number(phone: str, country_code: str = 'FR') -> bool:
    """Valider un numéro de téléphone."""
    
    try:
        import phonenumbers
        
        parsed = phonenumbers.parse(phone, country_code)
        return phonenumbers.is_valid_number(parsed)
    except:
        # Validation basique si phonenumbers n'est pas disponible
        import re
        pattern = r'^[\+]?[1-9][\d]{0,15}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))


def validate_email_domain(email: str, allowed_domains: List[str] = None) -> bool:
    """Valider le domaine d'un email."""
    
    if not allowed_domains:
        return True
    
    domain = email.split('@')[-1].lower()
    return domain in [d.lower() for d in allowed_domains]


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Valider la force d'un mot de passe."""
    
    import re
    
    checks = {
        'length': len(password) >= 8,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'digit': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    }
    
    score = sum(checks.values())
    
    if score >= 4:
        strength = 'strong'
    elif score >= 3:
        strength = 'medium'
    else:
        strength = 'weak'
    
    return {
        'strength': strength,
        'score': score,
        'checks': checks,
        'is_valid': score >= 3
    }


# ===== UTILITAIRES DE TEMPS =====

def get_game_timeout_timestamp() -> datetime:
    """Obtenir le timestamp de timeout d'un jeu (2 minutes)."""
    
    from . import BUSINESS_LIMITS
    
    timeout_seconds = BUSINESS_LIMITS['GAME_TIMEOUT_SECONDS']
    return timezone.now() + timedelta(seconds=timeout_seconds)


def is_within_business_hours() -> bool:
    """Vérifier si on est dans les heures d'ouverture."""
    
    # Configuration par défaut: 24h/24
    business_start = getattr(settings, 'BUSINESS_HOURS_START', 0)
    business_end = getattr(settings, 'BUSINESS_HOURS_END', 24)
    
    current_hour = timezone.now().hour
    
    return business_start <= current_hour < business_end


def calculate_age(birth_date: datetime.date) -> int:
    """Calculer l'âge en années."""
    
    today = timezone.now().date()
    age = today.year - birth_date.year
    
    # Ajuster si l'anniversaire n'est pas encore passé cette année
    if today < birth_date.replace(year=today.year):
        age -= 1
    
    return age


def is_valid_age_for_gambling(birth_date: datetime.date, min_age: int = 18) -> bool:
    """Vérifier si l'âge est valide pour les jeux d'argent."""
    
    age = calculate_age(birth_date)
    return age >= min_age


# ===== UTILITAIRES DE FORMATAGE =====

def format_file_size(size_bytes: int) -> str:
    """Formater une taille de fichier."""
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Tronquer un texte."""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def slugify_text(text: str) -> str:
    """Créer un slug à partir d'un texte."""
    
    import re
    from django.utils.text import slugify
    
    return slugify(text)


# ===== UTILITAIRES DE CACHE =====

def get_cache_key(*parts: str) -> str:
    """Générer une clé de cache."""
    
    return ":".join(str(part) for part in parts)


def invalidate_cache_pattern(pattern: str) -> int:
    """Invalider les clés de cache correspondant à un pattern."""
    
    # Note: Cette fonction nécessite Redis pour fonctionner pleinement
    try:
        from django.core.cache import cache
        from django.core.cache.backends.redis import RedisCache
        
        if isinstance(cache, RedisCache):
            redis_client = cache._cache.get_client(1)
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
        
        return 0
    except:
        logger.warning("Impossible d'invalider le cache par pattern")
        return 0


# ===== UTILITAIRES DIVERS =====

def safe_divide(numerator: Union[int, float, Decimal], 
                denominator: Union[int, float, Decimal], 
                default: Union[int, float, Decimal] = 0) -> Union[int, float, Decimal]:
    """Division sécurisée (évite la division par zéro)."""
    
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default


def get_client_country(request) -> str:
    """Obtenir le pays du client (basique)."""
    
    # Vérifier les headers de géolocalisation
    country = request.META.get('HTTP_CF_IPCOUNTRY')  # Cloudflare
    if country:
        return country.upper()
    
    # TODO: Intégrer un service de géolocalisation IP
    return 'UNKNOWN'


def generate_unique_filename(original_filename: str, prefix: str = '') -> str:
    """Générer un nom de fichier unique."""
    
    import os
    from django.utils import timezone
    
    name, ext = os.path.splitext(original_filename)
    timestamp = int(timezone.now().timestamp())
    random_part = secrets.token_hex(4)
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}{ext}"
    else:
        return f"{timestamp}_{random_part}{ext}"


def is_development() -> bool:
    """Vérifier si on est en mode développement."""
    
    return getattr(settings, 'DEBUG', False)


def get_app_version() -> str:
    """Obtenir la version de l'application."""
    
    return getattr(settings, 'APP_VERSION', '1.0.0')


def log_user_activity(user, activity_type: str, description: str, metadata: dict = None):
    """Logger une activité utilisateur."""
    
    try:
        from apps.accounts.models import UserActivity
        
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"Erreur lors du logging d'activité: {e}")
        
        
      
      
      
# Dans apps/core/utils.py
def log_user_activity_with_ip(user, activity_type, description, ip_address=None, user_agent=None, metadata=None):
    """Wrapper pour log_user_activity qui accepte ip_address."""
    return log_user_activity(
        user=user,
        activity_type=activity_type,
        description=description,
        metadata=metadata or {}
    )
        
