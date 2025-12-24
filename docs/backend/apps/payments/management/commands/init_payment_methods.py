"""
Commande de management pour initialiser les méthodes de paiement.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.payments.models import PaymentMethod


class Command(BaseCommand):
    help = 'Initialise les méthodes de paiement de base'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la recréation des méthodes existantes'
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if force:
            PaymentMethod.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Méthodes de paiement existantes supprimées')
            )

        # Méthodes de paiement à créer
        payment_methods = [
            {
                'name': 'Orange Money',
                'method_type': 'mobile_money',
                'provider': 'orange_money',
                'supported_currencies': ['FCFA', 'XOF'],
                'min_deposit': {'FCFA': 500, 'XOF': 500},
                'max_deposit': {'FCFA': 500000, 'XOF': 500000},
                'min_withdrawal': {'FCFA': 1000, 'XOF': 1000},
                'max_withdrawal': {'FCFA': 250000, 'XOF': 250000},
                'deposit_fee_percentage': Decimal('1.5'),
                'withdrawal_fee_percentage': Decimal('2.0'),
                'deposit_fee_fixed': Decimal('0'),
                'withdrawal_fee_fixed': Decimal('100'),
                'supports_deposit': True,
                'supports_withdrawal': True,
                'is_active': True,
                'display_order': 1,
                'description': 'Paiement mobile via Orange Money',
                'icon': 'orange-money.png'
            },
            {
                'name': 'MTN Mobile Money',
                'method_type': 'mobile_money',
                'provider': 'mtn_money',
                'supported_currencies': ['FCFA', 'XOF'],
                'min_deposit': {'FCFA': 500, 'XOF': 500},
                'max_deposit': {'FCFA': 500000, 'XOF': 500000},
                'min_withdrawal': {'FCFA': 1000, 'XOF': 1000},
                'max_withdrawal': {'FCFA': 250000, 'XOF': 250000},
                'deposit_fee_percentage': Decimal('1.5'),
                'withdrawal_fee_percentage': Decimal('2.0'),
                'deposit_fee_fixed': Decimal('0'),
                'withdrawal_fee_fixed': Decimal('100'),
                'supports_deposit': True,
                'supports_withdrawal': True,
                'is_active': True,
                'display_order': 2,
                'description': 'Paiement mobile via MTN Mobile Money',
                'icon': 'mtn-money.png'
            },
            {
                'name': 'Moov Money',
                'method_type': 'mobile_money',
                'provider': 'moov_money',
                'supported_currencies': ['FCFA', 'XOF'],
                'min_deposit': {'FCFA': 500, 'XOF': 500},
                'max_deposit': {'FCFA': 500000, 'XOF': 500000},
                'min_withdrawal': {'FCFA': 1000, 'XOF': 1000},
                'max_withdrawal': {'FCFA': 250000, 'XOF': 250000},
                'deposit_fee_percentage': Decimal('1.5'),
                'withdrawal_fee_percentage': Decimal('2.0'),
                'deposit_fee_fixed': Decimal('0'),
                'withdrawal_fee_fixed': Decimal('100'),
                'supports_deposit': True,
                'supports_withdrawal': True,
                'is_active': True,
                'display_order': 3,
                'description': 'Paiement mobile via Moov Money',
                'icon': 'moov-money.png'
            },
            {
                'name': 'FeexPay',
                'method_type': 'digital_wallet',
                'provider': 'feexpay',
                'supported_currencies': ['FCFA', 'XOF'],
                'min_deposit': {'FCFA': 100, 'XOF': 100},
                'max_deposit': {'FCFA': 1000000, 'XOF': 1000000},
                'min_withdrawal': {'FCFA': 500, 'XOF': 500},
                'max_withdrawal': {'FCFA': 500000, 'XOF': 500000},
                'deposit_fee_percentage': Decimal('1.0'),
                'withdrawal_fee_percentage': Decimal('1.5'),
                'deposit_fee_fixed': Decimal('0'),
                'withdrawal_fee_fixed': Decimal('50'),
                'supports_deposit': True,
                'supports_withdrawal': True,
                'is_active': True,
                'display_order': 4,
                'description': 'Portefeuille électronique FeexPay',
                'icon': 'feexpay.png'
            },
            {
                'name': 'Carte Bancaire',
                'method_type': 'card',
                'provider': 'stripe',
                'supported_currencies': ['EUR', 'USD', 'FCFA'],
                'min_deposit': {'EUR': 5, 'USD': 5, 'FCFA': 3000},
                'max_deposit': {'EUR': 5000, 'USD': 5000, 'FCFA': 3000000},
                'min_withdrawal': {'EUR': 10, 'USD': 10, 'FCFA': 6000},
                'max_withdrawal': {'EUR': 2000, 'USD': 2000, 'FCFA': 1200000},
                'deposit_fee_percentage': Decimal('2.9'),
                'withdrawal_fee_percentage': Decimal('3.5'),
                'deposit_fee_fixed': Decimal('0.30'),
                'withdrawal_fee_fixed': Decimal('1.00'),
                'supports_deposit': True,
                'supports_withdrawal': True,
                'is_active': True,
                'display_order': 5,
                'description': 'Paiement par carte bancaire Visa/MasterCard',
                'icon': 'credit-card.png'
            },
            {
                'name': 'Virement Bancaire',
                'method_type': 'bank_transfer',
                'provider': 'bank',
                'supported_currencies': ['EUR', 'USD', 'FCFA'],
                'min_deposit': {'EUR': 20, 'USD': 20, 'FCFA': 15000},
                'max_deposit': {'EUR': 10000, 'USD': 10000, 'FCFA': 6000000},
                'min_withdrawal': {'EUR': 50, 'USD': 50, 'FCFA': 30000},
                'max_withdrawal': {'EUR': 5000, 'USD': 5000, 'FCFA': 3000000},
                'deposit_fee_percentage': Decimal('0.5'),
                'withdrawal_fee_percentage': Decimal('1.0'),
                'deposit_fee_fixed': Decimal('2.00'),
                'withdrawal_fee_fixed': Decimal('5.00'),
                'supports_deposit': True,
                'supports_withdrawal': True,
                'is_active': False,  # Désactivé par défaut car nécessite plus de configuration
                'display_order': 6,
                'description': 'Virement bancaire SEPA/International',
                'icon': 'bank.png'
            }
        ]

        created_count = 0
        
        with transaction.atomic():
            for method_data in payment_methods:
                method_name = method_data['name']
                
                # Vérifier si la méthode existe déjà
                if not force and PaymentMethod.objects.filter(name=method_name).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Méthode "{method_name}" existe déjà (utilisez --force pour recréer)')
                    )
                    continue
                
                try:
                    payment_method = PaymentMethod.objects.create(**method_data)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Méthode "{method_name}" créée')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Erreur lors de la création de "{method_name}": {e}')
                    )

        # Résumé
        total_methods = PaymentMethod.objects.count()
        active_methods = PaymentMethod.objects.filter(is_active=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Initialisation terminée:'
                f'\n   - {created_count} méthodes créées'
                f'\n   - {total_methods} méthodes au total'
                f'\n   - {active_methods} méthodes actives'
            )
        )
        
        # Afficher les méthodes actives
        active_methods_list = PaymentMethod.objects.filter(is_active=True).order_by('display_order')
        if active_methods_list:
            self.stdout.write('\n📋 Méthodes actives:')
            for method in active_methods_list:
                currencies = ', '.join(method.supported_currencies)
                self.stdout.write(f'   • {method.name} ({method.method_type}) - {currencies}')