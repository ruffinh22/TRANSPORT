# Generated migration for referral system update
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('referrals', '0001_initial'),
    ]

    operations = [
        # Renommer commission_games_count en winning_games_count
        migrations.RenameField(
            model_name='referral',
            old_name='commission_games_count',
            new_name='winning_games_count',
        ),
        
        # Modifier le champ pour ajouter help_text
        migrations.AlterField(
            model_name='referral',
            name='winning_games_count',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Compte uniquement les parties gagnantes',
                verbose_name='Parties gagnantes ayant généré commission'
            ),
        ),
        
        # Modifier le champ is_premium_referrer pour ajouter help_text
        migrations.AlterField(
            model_name='referral',
            name='is_premium_referrer',
            field=models.BooleanField(
                default=False,
                help_text='Premium = 10% commission illimitée. Non-premium = 10% sur 3 premières parties gagnantes seulement',
                verbose_name='Parrain premium'
            ),
        ),
    ]
