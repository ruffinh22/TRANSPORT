# apps/core/validators.py
# ===========================

import re
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Any, List, Optional, Dict
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.core.validators import RegexValidator
import phonenumbers
from phonenumbers import NumberParseException

from . import SUPPORTED_CURRENCIES, BUSINESS_LIMITS, REGEX_PATTERNS


# ===== VALIDATEURS DE BASE =====

class StrongPasswordValidator:
    """
    Validateur pour mots de passe forts selon les standards RUMO RUSH.
    """
    
    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special = True
        self.forbidden_passwords = [
            'password', '123456', 'password123', 'admin', 'rumorush'
        ]
    
    def __call__(self, password: str) -> None:
        """Valider le mot de passe."""
        
        if len(password) < self.min_length:
            raise ValidationError(
                f"Le mot de passe doit contenir au moins {self.min_length} caractères."
            )
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            raise ValidationError("Le mot de passe doit contenir au moins une majuscule.")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            raise ValidationError("Le mot de passe doit contenir au moins une minuscule.")
        
        if self.require_numbers and not any(c.isdigit() for c in password):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
        
        if password.lower() in self.forbidden_passwords:
            raise ValidationError("Ce mot de passe est trop commun.")


class UsernameValidator:
    """Validateur pour noms d'utilisateur."""
    
    def __init__(self):
        self.min_length = 3
        self.max_length = 30
        self.forbidden_usernames = [
            'admin', 'root', 'moderator', 'support', 'rumorush',
            'api', 'www', 'mail', 'ftp', 'test', 'demo'
        ]
    
    def __call__(self, username: str) -> None:
        """Valider le nom d'utilisateur."""
        
        if not re.match(REGEX_PATTERNS['USERNAME'], username):
            raise ValidationError(
                "Le nom d'utilisateur ne peut contenir que des lettres, "
                "chiffres et underscores."
            )
        
        if len(username) < self.min_length:
            raise ValidationError(
                f"Le nom d'utilisateur doit contenir au moins {self.min_length} caractères."
            )
        
        if len(username) > self.max_length:
            raise ValidationError(
                f"Le nom d'utilisateur ne peut pas dépasser {self.max_length} caractères."
            )
        
        if username.lower() in self.forbidden_usernames:
            raise ValidationError("Ce nom d'utilisateur n'est pas autorisé.")


class PhoneNumberValidator:
    """Validateur pour numéros de téléphone internationaux."""
    
    def __call__(self, phone_number: str) -> None:
        """Valider le numéro de téléphone."""
        
        try:
            parsed = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Numéro de téléphone invalide.")
        except NumberParseException:
            raise ValidationError("Format de numéro de téléphone invalide.")


class AgeValidator:
    """Validateur pour vérifier l'âge minimum (18 ans)."""
    
    def __init__(self, min_age: int = 18):
        self.min_age = min_age
    
    def __call__(self, birth_date: date) -> None:
        """Valider l'âge."""
        
        if not isinstance(birth_date, date):
            raise ValidationError("Date de naissance requise.")
        
        today = date.today()
        age = today.year - birth_date.year
        
        # Ajuster si l'anniversaire n'est pas encore passé
        if today < birth_date.replace(year=today.year):
            age -= 1
        
        if age < self.min_age:
            raise ValidationError(f"Vous devez avoir au moins {self.min_age} ans.")
        
        # Vérifier que la date n'est pas dans le futur
        if birth_date > today:
            raise ValidationError("La date de naissance ne peut pas être dans le futur.")


# ===== VALIDATEURS FINANCIERS =====

class CurrencyValidator:
    """Validateur pour devises supportées."""
    
    def __call__(self, currency: str) -> None:
        """Valider la devise."""
        
        if currency not in SUPPORTED_CURRENCIES:
            raise ValidationError(
                f"Devise non supportée. Devises autorisées: {', '.join(SUPPORTED_CURRENCIES.keys())}"
            )


class AmountValidator:
    """Validateur pour montants financiers."""
    
    def __init__(self, currency: str = 'FCFA', transaction_type: str = 'general'):
        self.currency = currency
        self.transaction_type = transaction_type
    
    def __call__(self, amount: Decimal) -> None:
        """Valider le montant."""
        
        if not isinstance(amount, (Decimal, int, float)):
            raise ValidationError("Le montant doit être numérique.")
        
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValidationError("Le montant doit être positif.")
        
        # Vérifier les limites selon le type de transaction
        min_amount, max_amount = self._get_limits()
        
        if amount < min_amount:
            raise ValidationError(
                f"Montant minimum: {min_amount} {self.currency}"
            )
        
        if amount > max_amount:
            raise ValidationError(
                f"Montant maximum: {max_amount} {self.currency}"
            )
        
        # Vérifier les décimales selon la devise
        currency_config = SUPPORTED_CURRENCIES.get(self.currency, {})
        decimal_places = currency_config.get('decimal_places', 2)
        
        if amount.as_tuple().exponent < -decimal_places:
            raise ValidationError(
                f"Trop de décimales pour {self.currency} (max: {decimal_places})"
            )
    
    def _get_limits(self) -> tuple:
        """Obtenir les limites min/max selon le type de transaction."""
        
        currency_config = SUPPORTED_CURRENCIES.get(self.currency, {})
        
        if self.transaction_type == 'bet':
            min_amount = BUSINESS_LIMITS['MIN_BET_AMOUNT'].get(self.currency, 500)
            max_amount = BUSINESS_LIMITS['MAX_BET_AMOUNT'].get(self.currency, 1000000)
        else:
            min_amount = currency_config.get('min_amount', 1)
            max_amount = currency_config.get('max_amount', 1000000)
        
        return Decimal(str(min_amount)), Decimal(str(max_amount))


class BetAmountValidator(AmountValidator):
    """Validateur spécifique pour montants de mise."""
    
    def __init__(self, currency: str = 'FCFA'):
        super().__init__(currency, 'bet')
    
    def __call__(self, amount: Decimal) -> None:
        """Valider le montant de mise."""
        
        super().__call__(amount)
        
        # Vérifier que c'est un montant autorisé
        allowed_amounts = self._get_allowed_bet_amounts()
        
        if amount not in allowed_amounts:
            raise ValidationError(
                f"Montant de mise non autorisé. "
                f"Montants autorisés: {', '.join(map(str, allowed_amounts))}"
            )
    
    def _get_allowed_bet_amounts(self) -> List[Decimal]:
        """Obtenir les montants de mise autorisés."""
        
        # Montants prédéfinis selon la devise
        amounts_config = {
            'FCFA': [500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
            'EUR': [1, 2, 5, 10, 25, 50, 100, 250],
            'USD': [1, 2, 5, 10, 25, 50, 100, 250]
        }
        
        amounts = amounts_config.get(self.currency, amounts_config['FCFA'])
        return [Decimal(str(amount)) for amount in amounts]


# ===== VALIDATEURS DE JEU =====

class GameMoveValidator:
    """Validateur pour mouvements de jeu."""
    
    def __init__(self, game_type: str):
        self.game_type = game_type
    
    def __call__(self, move_data: Dict[str, Any]) -> None:
        """Valider un mouvement de jeu."""
        
        if not isinstance(move_data, dict):
            raise ValidationError("Les données de mouvement doivent être un objet.")
        
        # Validation selon le type de jeu
        validator_map = {
            'chess': self._validate_chess_move,
            'checkers': self._validate_checkers_move,
            'ludo': self._validate_ludo_move,
            'cards': self._validate_cards_move
        }
        
        validator = validator_map.get(self.game_type)
        if validator:
            validator(move_data)
        else:
            raise ValidationError(f"Type de jeu non supporté: {self.game_type}")
    
    def _validate_chess_move(self, move_data: Dict[str, Any]) -> None:
        """Valider un mouvement d'échecs."""
        
        required_fields = ['from_square', 'to_square', 'piece']
        
        for field in required_fields:
            if field not in move_data:
                raise ValidationError(f"Champ requis manquant: {field}")
        
        # Valider les positions (format: a1-h8)
        square_pattern = r'^[a-h][1-8]
        
        if not re.match(square_pattern, move_data['from_square']):
            raise ValidationError("Position de départ invalide.")
        
        if not re.match(square_pattern, move_data['to_square']):
            raise ValidationError("Position d'arrivée invalide.")
        
        # Valider le type de pièce
        valid_pieces = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
        if move_data['piece'] not in valid_pieces:
            raise ValidationError("Type de pièce invalide.")
    
    def _validate_checkers_move(self, move_data: Dict[str, Any]) -> None:
        """Valider un mouvement de dames."""
        
        required_fields = ['from_position', 'to_position']
        
        for field in required_fields:
            if field not in move_data:
                raise ValidationError(f"Champ requis manquant: {field}")
        
        # Valider les positions (0-31 pour damier 8x8)
        for field in ['from_position', 'to_position']:
            pos = move_data[field]
            if not isinstance(pos, int) or pos < 0 or pos > 31:
                raise ValidationError(f"Position invalide: {field}")
    
    def _validate_ludo_move(self, move_data: Dict[str, Any]) -> None:
        """Valider un mouvement de ludo."""
        
        required_fields = ['piece_id', 'dice_value']
        
        for field in required_fields:
            if field not in move_data:
                raise ValidationError(f"Champ requis manquant: {field}")
        
        # Valider la valeur du dé
        dice_value = move_data['dice_value']
        if not isinstance(dice_value, int) or dice_value < 1 or dice_value > 6:
            raise ValidationError("Valeur de dé invalide (1-6).")
        
        # Valider l'ID de pièce
        piece_id = move_data['piece_id']
        if not isinstance(piece_id, int) or piece_id < 0 or piece_id > 3:
            raise ValidationError("ID de pièce invalide (0-3).")
    
    def _validate_cards_move(self, move_data: Dict[str, Any]) -> None:
        """Valider un mouvement de cartes."""
        
        required_fields = ['card_played']
        
        for field in required_fields:
            if field not in move_data:
                raise ValidationError(f"Champ requis manquant: {field}")
        
        # Valider la carte jouée (format: "2H", "AS", etc.)
        card = move_data['card_played']
        if not re.match(r'^(A|[2-9]|10|J|Q|K)[HDCS], card):
            raise ValidationError("Format de carte invalide.")


# ===== VALIDATEURS DE TRANSACTION =====

class TransactionValidator:
    """Validateur pour transactions financières."""
    
    def __call__(self, transaction_data: Dict[str, Any]) -> None:
        """Valider les données de transaction."""
        
        required_fields = ['amount', 'currency', 'transaction_type']
        
        for field in required_fields:
            if field not in transaction_data:
                raise ValidationError(f"Champ requis manquant: {field}")
        
        # Valider la devise
        currency_validator = CurrencyValidator()
        currency_validator(transaction_data['currency'])
        
        # Valider le montant
        amount_validator = AmountValidator(
            currency=transaction_data['currency'],
            transaction_type=transaction_data['transaction_type']
        )
        amount_validator(transaction_data['amount'])
        
        # Valider le type de transaction
        valid_types = ['deposit', 'withdrawal', 'bet', 'win', 'commission', 'referral']
        if transaction_data['transaction_type'] not in valid_types:
            raise ValidationError(f"Type de transaction invalide: {transaction_data['transaction_type']}")


class WithdrawalValidator:
    """Validateur pour demandes de retrait."""
    
    def __call__(self, withdrawal_data: Dict[str, Any], user) -> None:
        """Valider une demande de retrait."""
        
        # Validation de base
        transaction_validator = TransactionValidator()
        transaction_validator(withdrawal_data)
        
        # Vérifications spécifiques aux retraits
        self._validate_user_eligibility(user)
        self._validate_withdrawal_limits(withdrawal_data, user)
        self._validate_payment_method(withdrawal_data)
    
    def _validate_user_eligibility(self, user) -> None:
        """Vérifier l'éligibilité de l'utilisateur."""
        
        if not getattr(user, 'is_verified', False):
            raise ValidationError("Compte non vérifié. KYC requis pour les retraits.")
        
        if not getattr(user, 'is_active', True):
            raise ValidationError("Compte désactivé.")
    
    def _validate_withdrawal_limits(self, withdrawal_data: Dict[str, Any], user) -> None:
        """Vérifier les limites de retrait."""
        
        amount = Decimal(str(withdrawal_data['amount']))
        currency = withdrawal_data['currency']
        
        # Montants minimum selon la méthode
        min_amounts = {
            'mobile_money': {'FCFA': 4000},
            'bank_transfer': {'FCFA': 5600, 'EUR': 10, 'USD': 10},
            'crypto': {'FCFA': 5600, 'EUR': 10, 'USD': 10}
        }
        
        payment_method = withdrawal_data.get('payment_method', 'mobile_money')
        min_amount = min_amounts.get(payment_method, {}).get(currency, 1000)
        
        if amount < min_amount:
            raise ValidationError(f"Montant minimum pour {payment_method}: {min_amount} {currency}")
        
        # Vérifier le solde utilisateur
        balance = self._get_user_balance(user, currency)
        if amount > balance:
            raise ValidationError(f"Solde insuffisant. Disponible: {balance} {currency}")
    
    def _validate_payment_method(self, withdrawal_data: Dict[str, Any]) -> None:
        """Valider la méthode de paiement."""
        
        valid_methods = ['mobile_money', 'bank_transfer', 'crypto']
        method = withdrawal_data.get('payment_method', 'mobile_money')
        
        if method not in valid_methods:
            raise ValidationError(f"Méthode de paiement invalide: {method}")
    
    def _get_user_balance(self, user, currency: str) -> Decimal:
        """Obtenir le solde de l'utilisateur."""
        
        balance_fields = {
            'FCFA': 'balance_fcfa',
            'EUR': 'balance_eur',
            'USD': 'balance_usd'
        }
        
        field = balance_fields.get(currency, 'balance_fcfa')
        return Decimal(str(getattr(user, field, 0)))


# ===== VALIDATEURS DE FICHIERS =====

class FileValidator:
    """Validateur pour uploads de fichiers."""
    
    def __init__(self, allowed_extensions: List[str] = None, max_size: int = None):
        self.allowed_extensions = allowed_extensions or ['jpg', 'jpeg', 'png', 'pdf']
        self.max_size = max_size or 10485760  # 10MB par défaut
    
    def __call__(self, uploaded_file) -> None:
        """Valider le fichier uploadé."""
        
        if not uploaded_file:
            raise ValidationError("Fichier requis.")
        
        # Vérifier la taille
        if uploaded_file.size > self.max_size:
            max_size_mb = self.max_size / 1024 / 1024
            raise ValidationError(f"Taille maximale autorisée: {max_size_mb}MB")
        
        # Vérifier l'extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in self.allowed_extensions:
            raise ValidationError(
                f"Extension non autorisée. Extensions autorisées: {', '.join(self.allowed_extensions)}"
            )
        
        # Vérifications de sécurité basiques
        self._validate_file_content(uploaded_file, file_extension)
    
    def _validate_file_content(self, uploaded_file, extension: str) -> None:
        """Valider le contenu du fichier pour éviter les malwares."""
        
        # Lire les premiers octets pour vérifier la signature
        uploaded_file.seek(0)
        header = uploaded_file.read(512)
        uploaded_file.seek(0)  # Remettre le curseur au début
        
        # Signatures de fichiers connues
        file_signatures = {
            'pdf': b'%PDF',
            'jpg': b'\xff\xd8\xff',
            'jpeg': b'\xff\xd8\xff',
            'png': b'\x89PNG\r\n\x1a\n'
        }
        
        signature = file_signatures.get(extension)
        if signature and not header.startswith(signature):
            raise ValidationError("Type de fichier non conforme à l'extension.")


# ===== VALIDATEURS COMPOSÉS =====

def validate_user_registration(user_data: Dict[str, Any]) -> None:
    """Valider toutes les données d'inscription utilisateur."""
    
    # Valider le nom d'utilisateur
    if 'username' in user_data:
        username_validator = UsernameValidator()
        username_validator(user_data['username'])
    
    # Valider le mot de passe
    if 'password' in user_data:
        password_validator = StrongPasswordValidator()
        password_validator(user_data['password'])
    
    # Valider l'âge
    if 'date_of_birth' in user_data:
        age_validator = AgeValidator()
        age_validator(user_data['date_of_birth'])
    
    # Valider le téléphone
    if 'phone_number' in user_data:
        phone_validator = PhoneNumberValidator()
        phone_validator(user_data['phone_number'])


def validate_game_creation(game_data: Dict[str, Any]) -> None:
    """Valider les données de création de jeu."""
    
    required_fields = ['game_type', 'bet_amount', 'currency']
    
    for field in required_fields:
        if field not in game_data:
            raise ValidationError(f"Champ requis manquant: {field}")
    
    # Valider le montant de mise
    bet_validator = BetAmountValidator(game_data['currency'])
    bet_validator(game_data['bet_amount'])
    
    # Valider le type de jeu
    valid_game_types = ['chess', 'checkers', 'ludo', 'cards']
    if game_data['game_type'] not in valid_game_types:
        raise ValidationError(f"Type de jeu invalide: {game_data['game_type']}")


# ===== VALIDATEURS REGEX PRÉDÉFINIS =====

username_validator = RegexValidator(
    regex=REGEX_PATTERNS['USERNAME'],
    message="Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscores (3-30 caractères)."
)

referral_code_validator = RegexValidator(
    regex=REGEX_PATTERNS['REFERRAL_CODE'],
    message="Code de parrainage invalide (6-10 caractères alphanumériques)."
)

transaction_id_validator = RegexValidator(
    regex=REGEX_PATTERNS['TRANSACTION_ID'],
    message="ID de transaction invalide."
)
