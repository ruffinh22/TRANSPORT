# apps/payments/migrations/0004_feexpay_models.py

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeexPayProvider',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('provider_code', models.CharField(
                    choices=[('mtn', 'MTN'), ('moov', 'Moov'), ('orange', 'Orange'), ('celtiis', 'Celtiis'),
                             ('coris', 'Coris Bank'), ('wave', 'Wave'), ('free', 'Free'), ('bank_transfer', 'Virement Bancaire'),
                             ('mastercard', 'Mastercard'), ('visa', 'Visa'), ('amex', 'American Express'),
                             ('unionpay', 'UnionPay'), ('orange_ci', 'Orange Côte d\'Ivoire'), ('moov_togo', 'Moov Togo'),
                             ('mtn_senegal', 'MTN Sénégal'), ('wave_senegal', 'Wave Sénégal')],
                    max_length=30, unique=True, verbose_name='Code du fournisseur')),
                ('provider_name', models.CharField(max_length=100, verbose_name='Nom du fournisseur')),
                ('country_code', models.CharField(
                    choices=[('SN', 'Sénégal'), ('CI', 'Côte d\'Ivoire'), ('TG', 'Togo'), ('BJ', 'Bénin'),
                             ('GW', 'Guinée-Bissau'), ('CM', 'Cameroun'), ('GA', 'Gabon')],
                    max_length=2, verbose_name='Code pays')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_test_mode', models.BooleanField(default=False, verbose_name='Mode test')),
                ('min_amount', models.DecimalField(decimal_places=2, default='100.00', max_digits=10, verbose_name='Montant minimum')),
                ('max_amount', models.DecimalField(decimal_places=2, default='1000000.00', max_digits=12, verbose_name='Montant maximum')),
                ('fee_percentage', models.DecimalField(decimal_places=2, default='0.00', max_digits=5, verbose_name='Frais (%)')),
                ('fee_fixed', models.DecimalField(decimal_places=2, default='0.00', max_digits=8, verbose_name='Frais fixes')),
                ('supported_currencies', models.JSONField(default=list, help_text='Ex: ["XOF", "EUR", "USD"]', verbose_name='Devises supportées')),
                ('processing_time_seconds', models.IntegerField(default=300, help_text='Délai estimé pour traiter une transaction', verbose_name='Délai de traitement (secondes)')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('icon_url', models.URLField(blank=True, verbose_name='URL de l\'icône')),
                ('total_transactions', models.BigIntegerField(default=0, verbose_name='Total de transactions')),
                ('total_volume', models.DecimalField(decimal_places=2, default='0.00', max_digits=15, verbose_name='Volume total')),
                ('success_rate', models.DecimalField(decimal_places=2, default='100.00', max_digits=5, verbose_name='Taux de réussite (%)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
                ('last_sync_at', models.DateTimeField(blank=True, null=True, verbose_name='Dernière synchronisation')),
            ],
            options={
                'verbose_name': 'Fournisseur FeexPay',
                'verbose_name_plural': 'Fournisseurs FeexPay',
                'db_table': 'feexpay_providers',
                'ordering': ['provider_name', 'country_code'],
            },
        ),
        migrations.CreateModel(
            name='FeexPayTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('feexpay_transaction_id', models.CharField(blank=True, max_length=255, unique=True, verbose_name='ID de transaction FeexPay')),
                ('internal_transaction_id', models.CharField(max_length=255, unique=True, verbose_name='ID de transaction interne')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Montant')),
                ('currency', models.CharField(max_length=5, verbose_name='Devise')),
                ('payment_method', models.CharField(
                    choices=[('mobile_money', 'Mobile Money'), ('bank_transfer', 'Virement Bancaire'),
                             ('card', 'Carte Bancaire'), ('wallet', 'Portefeuille Numérique')],
                    max_length=50, verbose_name='Méthode de paiement')),
                ('recipient_phone', models.CharField(blank=True, max_length=20, verbose_name='Numéro de téléphone du destinataire')),
                ('recipient_email', models.EmailField(blank=True, max_length=254, verbose_name='Email du destinataire')),
                ('recipient_account', models.CharField(blank=True, help_text='Numéro de compte bancaire ou identifiant du portefeuille', max_length=255, verbose_name='Compte du destinataire')),
                ('status', models.CharField(
                    choices=[('pending', 'En attente'), ('processing', 'En cours de traitement'), ('pending_validation', 'En attente de validation'),
                             ('successful', 'Réussi'), ('failed', 'Échoué'), ('cancelled', 'Annulé'), ('expired', 'Expiré'), ('disputed', 'En litige')],
                    default='pending', max_length=20, verbose_name='Statut')),
                ('status_message', models.TextField(blank=True, verbose_name='Message de statut')),
                ('fee_amount', models.DecimalField(decimal_places=2, default='0.00', max_digits=10, verbose_name='Montant des frais')),
                ('gross_amount', models.DecimalField(decimal_places=2, default='0.00', max_digits=12, verbose_name='Montant brut (montant + frais)')),
                ('payment_reference', models.CharField(blank=True, max_length=255, verbose_name='Référence de paiement')),
                ('callback_status', models.CharField(blank=True, max_length=50, verbose_name='Statut du callback')),
                ('feexpay_response', models.JSONField(blank=True, default=dict, verbose_name='Réponse FeexPay')),
                ('error_code', models.CharField(blank=True, max_length=100, verbose_name='Code d\'erreur')),
                ('error_message', models.TextField(blank=True, verbose_name='Message d\'erreur')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('initiated_at', models.DateTimeField(blank=True, null=True, verbose_name='Initié le')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='Traité le')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Complété le')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expire le')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP')),
                ('user_agent', models.TextField(blank=True, verbose_name='User Agent')),
                ('retry_count', models.IntegerField(default=0, verbose_name='Nombre de tentatives')),
                ('last_retry_at', models.DateTimeField(blank=True, null=True, verbose_name='Dernière tentative')),
                ('notes', models.TextField(blank=True, verbose_name='Notes internes')),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='payments.feexpayprovider', verbose_name='Fournisseur')),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='feexpay_transaction', to='payments.transaction', verbose_name='Transaction')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feexpay_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Transaction FeexPay',
                'verbose_name_plural': 'Transactions FeexPay',
                'db_table': 'feexpay_transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FeexPayWebhookSignature',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('webhook_id', models.CharField(max_length=255, unique=True, verbose_name='ID du webhook')),
                ('event_type', models.CharField(max_length=100, verbose_name='Type d\'événement')),
                ('payload', models.JSONField(verbose_name='Données du webhook')),
                ('signature', models.CharField(help_text='SHA256 de la charge utile signée avec la clé secrète FeexPay', max_length=255, verbose_name='Signature HMAC')),
                ('headers', models.JSONField(default=dict, verbose_name='En-têtes HTTP')),
                ('is_valid', models.BooleanField(default=False, verbose_name='Signature valide')),
                ('validation_error', models.TextField(blank=True, verbose_name='Erreur de validation')),
                ('is_processed', models.BooleanField(default=False, verbose_name='Traité')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='Traité le')),
                ('processing_error', models.TextField(blank=True, verbose_name='Erreur de traitement')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP source')),
                ('user_agent', models.TextField(blank=True, verbose_name='User Agent')),
                ('received_at', models.DateTimeField(auto_now_add=True, verbose_name='Reçu le')),
                ('retry_count', models.IntegerField(default=0, verbose_name='Nombre de tentatives')),
                ('next_retry_at', models.DateTimeField(blank=True, null=True, verbose_name='Prochaine tentative')),
                ('transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='webhook_signatures', to='payments.feexpaytransaction', verbose_name='Transaction')),
            ],
            options={
                'verbose_name': 'Signature du webhook FeexPay',
                'verbose_name_plural': 'Signatures des webhooks FeexPay',
                'db_table': 'feexpay_webhook_signatures',
                'ordering': ['-received_at'],
            },
        ),
        migrations.AddIndex(
            model_name='feexpaytransaction',
            index=models.Index(fields=['user', 'created_at'], name='feexpay_transactions_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaytransaction',
            index=models.Index(fields=['status', 'created_at'], name='feexpay_transactions_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaytransaction',
            index=models.Index(fields=['feexpay_transaction_id'], name='feexpay_transactions_feexpay_id_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaytransaction',
            index=models.Index(fields=['internal_transaction_id'], name='feexpay_transactions_internal_id_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaytransaction',
            index=models.Index(fields=['provider', 'status'], name='feexpay_transactions_provider_status_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaywebhooksignature',
            index=models.Index(fields=['webhook_id'], name='feexpay_webhooks_webhook_id_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaywebhooksignature',
            index=models.Index(fields=['is_valid', 'is_processed'], name='feexpay_webhooks_valid_processed_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaywebhooksignature',
            index=models.Index(fields=['event_type'], name='feexpay_webhooks_event_type_idx'),
        ),
        migrations.AddIndex(
            model_name='feexpaywebhooksignature',
            index=models.Index(fields=['received_at'], name='feexpay_webhooks_received_at_idx'),
        ),
        migrations.AddConstraint(
            model_name='feexpayprovider',
            constraint=models.UniqueConstraint(fields=['provider_code', 'country_code'], name='feexpay_provider_country_unique'),
        ),
    ]
