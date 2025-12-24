# Migration pour ajouter le modèle FeexPayWithdrawal
# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FeexPayWithdrawal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Montant en FCFA', max_digits=12, verbose_name='Montant')),
                ('fee', models.DecimalField(decimal_places=2, default=0, help_text='Frais de retrait', max_digits=12, verbose_name='Frais')),
                ('phone_number', models.CharField(help_text='Numéro Mobile Money destinataire', max_length=20, verbose_name='Numéro de téléphone')),
                ('network', models.CharField(choices=[('MTN', 'MTN Mobile Money'), ('ORANGE', 'Orange Money'), ('MOOV', 'Moov Money'), ('WAVE', 'Wave'), ('CELTIIS', 'Celtiis'), ('TOGOCOM', 'Togocom'), ('FREE', 'Free Money')], help_text='Réseau Mobile Money', max_length=20, verbose_name='Réseau')),
                ('recipient_name', models.CharField(help_text='Nom du bénéficiaire', max_length=100, verbose_name='Nom du bénéficiaire')),
                ('description', models.CharField(blank=True, help_text='Description du retrait', max_length=200, verbose_name='Description')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('processing', 'En cours'), ('completed', 'Terminé'), ('failed', 'Échoué'), ('cancelled', 'Annulé')], default='pending', max_length=20, verbose_name='Statut')),
                ('feexpay_transfer_id', models.CharField(blank=True, help_text='ID de transfert FeexPay', max_length=100, null=True, verbose_name='ID FeexPay')),
                ('feexpay_response', models.JSONField(blank=True, default=dict, help_text='Réponse complète de FeexPay', verbose_name='Réponse FeexPay')),
                ('error_message', models.TextField(blank=True, help_text='Message d\'erreur en cas d\'échec', verbose_name='Message d\'erreur')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('processed_at', models.DateTimeField(blank=True, help_text='Date de traitement', null=True, verbose_name='Traité le')),
                ('user', models.ForeignKey(help_text='Utilisateur demandeur', on_delete=django.db.models.deletion.CASCADE, related_name='feexpay_withdrawals', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Retrait FeexPay',
                'verbose_name_plural': 'Retraits FeexPay',
                'db_table': 'feexpay_withdrawals',
                'ordering': ['-created_at'],
            },
        ),
    ]