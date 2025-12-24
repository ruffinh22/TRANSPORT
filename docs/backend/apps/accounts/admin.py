# apps/accounts/admin.py
# ======================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count, Q

from .models import User, KYCDocument, UserActivity, UserSettings


# apps/accounts/admin.py
# ======================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count, Q

from .models import User, KYCDocument, UserActivity, UserSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Interface d'administration des utilisateurs RUMO RUSH."""
    
    # Configuration de l'affichage de liste
    list_display = [
        'username_display', 'email', 'full_name', 'country', 
        'kyc_status_badge', 'balance_display', 'verification_status',
        'created_at', 'last_activity'
    ]
    
    list_filter = [
        'kyc_status', 'is_verified', 'is_active', 'country',
        'preferred_language', 'created_at', 'last_activity'
    ]
    
    search_fields = [
        'username', 'email', 'first_name', 'last_name', 
        'phone_number', 'referral_code'
    ]
    
    ordering = ['-created_at']
    list_per_page = 50
    
    readonly_fields = [
        'id', 'referral_code', 'created_at', 'updated_at', 
        'last_activity', 'total_balance_display', 'age_display',
        'referral_stats', 'game_stats'
    ]
    
    # Organisation des champs en sections
    fieldsets = (
        (_('Informations de connexion'), {
            'fields': ('username', 'email', 'password'),
            'classes': ('wide',)
        }),
        (_('Informations personnelles'), {
            'fields': (
                ('first_name', 'last_name'),
                ('phone_number', 'date_of_birth', 'age_display'),
                ('country', 'city'),
                'address'
            )
        }),
        (_('Préférences'), {
            'fields': (
                ('preferred_language', 'timezone'),
                'preferred_currency'
            ),
            'classes': ('collapse',)
        }),
        (_('Soldes et finances'), {
            'fields': (
                ('balance_fcfa', 'balance_eur', 'balance_usd'),
                'total_balance_display'
            )
        }),
        (_('Vérification et KYC'), {
            'fields': (
                ('is_verified', 'kyc_status'),
                ('kyc_submitted_at', 'kyc_reviewed_at'),
                'kyc_rejection_reason'
            )
        }),
        (_('Système de parrainage'), {
            'fields': (
                ('referral_code', 'referred_by'),
                'referral_stats'
            ),
            'classes': ('collapse',)
        }),
        (_('Sécurité et activité'), {
            'fields': (
                ('last_login_ip', 'failed_login_attempts'),
                'account_locked_until',
                'last_activity'
            ),
            'classes': ('collapse',)
        }),
        (_('Permissions système'), {
            'fields': (
                ('is_active', 'is_staff', 'is_superuser'),
                ('groups', 'user_permissions')
            ),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('game_stats',),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuration pour l'ajout d'utilisateurs
    add_fieldsets = (
        (_('Informations requises'), {
            'classes': ('wide',),
            'fields': (
                ('username', 'email'),
                ('password1', 'password2'),
                ('first_name', 'last_name'),
                ('phone_number', 'date_of_birth'),
                'country'
            ),
        }),
        (_('Paramètres avancés'), {
            'classes': ('collapse', 'wide'),
            'fields': (
                ('is_staff', 'is_superuser'),
                'preferred_language'
            ),
        }),
    )
    
    # Actions personnalisées
    actions = [
        'approve_kyc', 'reject_kyc', 'unlock_accounts', 
        'verify_emails', 'send_welcome_email', 'export_users'
    ]
    
    # Méthodes d'affichage personnalisées
    def username_display(self, obj):
        """Affichage du nom d'utilisateur avec statut."""
        if obj.is_account_locked():
            return format_html(
                '<span style="color: red;">🔒 {}</span>',
                obj.username
            )
        elif not obj.is_verified:
            return format_html(
                '<span style="color: orange;">⚠️ {}</span>',
                obj.username
            )
        return format_html(
            '<span style="color: green;">✅ {}</span>',
            obj.username
        )
    username_display.short_description = 'Nom d\'utilisateur'
    username_display.admin_order_field = 'username'
    
    def kyc_status_badge(self, obj):
        """Badge coloré pour le statut KYC."""
        colors = {
            'pending': '#ffc107',
            'under_review': '#17a2b8',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'expired': '#6c757d'
        }
        
        color = colors.get(obj.kyc_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_kyc_status_display()
        )
    kyc_status_badge.short_description = 'Statut KYC'
    kyc_status_badge.admin_order_field = 'kyc_status'
    
    def balance_display(self, obj):
        """Affichage du solde principal."""
        balance = float(obj.balance_fcfa) if obj.balance_fcfa else 0.0
        formatted_balance = f'{balance:,.2f}'
        return format_html(
            '<strong>{} FCFA</strong>',
            formatted_balance
        )
    balance_display.short_description = 'Solde principal'
    balance_display.admin_order_field = 'balance_fcfa'
    
    def verification_status(self, obj):
        """Statut de vérification combiné."""
        if obj.is_verified and obj.kyc_status == 'approved':
            return format_html('<span style="color: green;">✅ Complet</span>')
        elif obj.is_verified:
            return format_html('<span style="color: orange;">📧 Email seul</span>')
        else:
            return format_html('<span style="color: red;">❌ Non vérifié</span>')
    verification_status.short_description = 'Vérification'
    
    def total_balance_display(self, obj):
        """Affichage du solde total converti."""
        total = float(obj.total_balance_fcfa) if obj.total_balance_fcfa else 0.0
        eur = float(obj.balance_eur) if obj.balance_eur else 0.0
        usd = float(obj.balance_usd) if obj.balance_usd else 0.0
        
        return format_html(
            '<strong>{} FCFA</strong><br><small>EUR: {} | USD: {}</small>',
            f'{total:,.2f}',
            f'{eur:,.2f}',
            f'{usd:,.2f}'
        )
    total_balance_display.short_description = 'Solde total'
    
    def age_display(self, obj):
        """Affichage de l'âge calculé."""
        return f"{obj.age} ans" if obj.age else "N/A"
    age_display.short_description = 'Âge'
    
    def referral_stats(self, obj):
        """Statistiques de parrainage."""
        referred_count = obj.referred_users.count()
        total_earnings = obj.referred_users.aggregate(
            total=Sum('balance_fcfa')
        )['total'] or 0
        
        commission = float(total_earnings) * 0.1
        
        return format_html(
            '<strong>Parrainés:</strong> {}<br><strong>Gains générés:</strong> {} FCFA',
            referred_count,
            f'{commission:,.2f}'
        )
    referral_stats.short_description = 'Stats parrainage'
    
    def game_stats(self, obj):
        """Statistiques de jeu."""
        from apps.games.models import Game
        
        games_played = Game.objects.filter(
            Q(player1=obj) | Q(player2=obj)
        ).count()
        
        games_won = Game.objects.filter(winner=obj).count()
        
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        
        return format_html(
            '<strong>Parties:</strong> {}<br><strong>Victoires:</strong> {} ({}%)',
            games_played,
            games_won,
            f'{win_rate:.1f}'
        )
    game_stats.short_description = 'Stats de jeu'
    
    # Actions en lot
    def approve_kyc(self, request, queryset):
        """Approuver le KYC en lot."""
        updated = 0
        for user in queryset.filter(kyc_status__in=['pending', 'under_review']):
            user.kyc_status = 'approved'
            user.kyc_reviewed_at = timezone.now()
            user.save(update_fields=['kyc_status', 'kyc_reviewed_at'])
            updated += 1
        
        self.message_user(
            request, 
            f"{updated} utilisateur(s) KYC approuvé(s) avec succès."
        )
    approve_kyc.short_description = "✅ Approuver le KYC sélectionné"
    
    def reject_kyc(self, request, queryset):
        """Rejeter le KYC en lot."""
        updated = 0
        for user in queryset.filter(kyc_status__in=['pending', 'under_review']):
            user.kyc_status = 'rejected'
            user.kyc_reviewed_at = timezone.now()
            user.kyc_rejection_reason = "Rejeté en lot par l'administrateur"
            user.save(update_fields=['kyc_status', 'kyc_reviewed_at', 'kyc_rejection_reason'])
            updated += 1
        
        self.message_user(
            request, 
            f"{updated} utilisateur(s) KYC rejeté(s).",
            level='WARNING'
        )
    reject_kyc.short_description = "❌ Rejeter le KYC sélectionné"
    
    def unlock_accounts(self, request, queryset):
        """Déverrouiller les comptes en lot."""
        updated = 0
        for user in queryset:
            if user.is_account_locked():
                user.unlock_account()
                updated += 1
        
        self.message_user(
            request, 
            f"{updated} compte(s) déverrouillé(s)."
        )
    unlock_accounts.short_description = "🔓 Déverrouiller les comptes"
    
    def verify_emails(self, request, queryset):
        """Vérifier les emails en lot."""
        updated = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(
            request, 
            f"{updated} email(s) vérifié(s)."
        )
    verify_emails.short_description = "📧 Vérifier les emails"
    
    def send_welcome_email(self, request, queryset):
        """Envoyer un email de bienvenue."""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        sent = 0
        for user in queryset:
            try:
                subject = f"Bienvenue sur RUMO RUSH, {user.first_name}!"
                message = render_to_string('emails/welcome.html', {'user': user})
                
                send_mail(
                    subject,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=message,
                    fail_silently=False
                )
                sent += 1
            except Exception:
                continue
        
        self.message_user(
            request,
            f"{sent} email(s) de bienvenue envoyé(s)."
        )
    send_welcome_email.short_description = "📬 Envoyer email de bienvenue"
    
    def export_users(self, request, queryset):
        """Exporter les utilisateurs sélectionnés."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'Nom complet', 'Pays', 'Statut KYC',
            'Solde FCFA', 'Vérifié', 'Date création'
        ])
        
        for user in queryset:
            writer.writerow([
                user.username,
                user.email,
                user.full_name,
                user.country,
                user.get_kyc_status_display(),
                user.balance_fcfa,
                'Oui' if user.is_verified else 'Non',
                user.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    export_users.short_description = "📊 Exporter les utilisateurs"


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    """Interface d'administration des documents KYC."""
    
    list_display = [
        'user_link', 'document_type_badge', 'status_badge', 
        'file_info', 'created_at', 'reviewed_info'
    ]
    
    list_filter = [
        'status', 'document_type', 'created_at', 'reviewed_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name'
    ]
    
    readonly_fields = [
        'id', 'original_filename', 'file_size', 'created_at', 
        'updated_at', 'file_preview'
    ]
    
    fieldsets = (
        (_('Document'), {
            'fields': (
                'user', 'document_type', 'file', 'file_preview',
                'original_filename', 'file_size'
            )
        }),
        (_('Vérification'), {
            'fields': (
                'status', 'reviewed_by', 'reviewed_at',
                'rejection_reason', 'notes'
            )
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_documents', 'reject_documents', 'mark_expired']
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.username
        )
    user_link.short_description = 'Utilisateur'
    user_link.admin_order_field = 'user__username'
    
    def document_type_badge(self, obj):
        """Badge pour le type de document."""
        colors = {
            'id_card': '#007bff',
            'passport': '#6610f2',
            'driving_license': '#e83e8c',
            'proof_of_address': '#fd7e14',
            'selfie': '#20c997'
        }
        
        color = colors.get(obj.document_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_document_type_display()
        )
    document_type_badge.short_description = 'Type'
    document_type_badge.admin_order_field = 'document_type'
    
    def status_badge(self, obj):
        """Badge coloré pour le statut."""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'expired': '#6c757d'
        }
        
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'status'
    
    def file_info(self, obj):
        """Informations sur le fichier."""
        size_mb = obj.file_size / (1024 * 1024) if obj.file_size else 0
        return format_html(
            '<strong>{} MB</strong><br><small>{}</small>',
            f'{size_mb:.2f}',
            obj.original_filename[:30] + '...' if len(obj.original_filename) > 30 else obj.original_filename
        )
    file_info.short_description = 'Fichier'
    
    def reviewed_info(self, obj):
        """Informations de révision."""
        if obj.reviewed_at and obj.reviewed_by:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.reviewed_by.username,
                obj.reviewed_at.strftime('%d/%m/%Y %H:%M')
            )
        return "Non révisé"
    reviewed_info.short_description = 'Révisé par'
    
    def file_preview(self, obj):
        """Aperçu du fichier."""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📄 Voir le fichier</a>',
                obj.file.url
            )
        return "Pas de fichier"
    file_preview.short_description = 'Aperçu'
    
    def approve_documents(self, request, queryset):
        """Approuver les documents en lot."""
        updated = queryset.filter(status='pending').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} document(s) approuvé(s).")
    approve_documents.short_description = "✅ Approuver les documents"
    
    def reject_documents(self, request, queryset):
        """Rejeter les documents en lot."""
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason="Rejeté en lot par l'administrateur"
        )
        self.message_user(request, f"{updated} document(s) rejeté(s).", level='WARNING')
    reject_documents.short_description = "❌ Rejeter les documents"
    
    def mark_expired(self, request, queryset):
        """Marquer comme expiré."""
        updated = queryset.exclude(status='expired').update(status='expired')
        self.message_user(request, f"{updated} document(s) marqué(s) comme expiré(s).")
    mark_expired.short_description = "⏰ Marquer comme expiré"


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Interface d'administration des activités utilisateur."""
    
    list_display = [
        'user_link', 'activity_type_badge', 'description_short', 
        'ip_address', 'created_at'
    ]
    
    list_filter = [
        'activity_type', 'created_at'
    ]
    
    search_fields = [
        'user__username', 'description', 'ip_address'
    ]
    
    readonly_fields = [
        'id', 'user', 'activity_type', 'description', 
        'ip_address', 'user_agent', 'metadata', 
        'created_at', 'session_id'
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 100
    
    def has_add_permission(self, request):
        """Les activités sont créées automatiquement."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les activités ne peuvent pas être modifiées."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Seules les anciennes activités peuvent être supprimées."""
        return request.user.is_superuser
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.username
        )
    user_link.short_description = 'Utilisateur'
    user_link.admin_order_field = 'user__username'
    
    def activity_type_badge(self, obj):
        """Badge coloré pour le type d'activité."""
        colors = {
            'login': '#28a745',
            'logout': '#6c757d',
            'game_created': '#007bff',
            'game_won': '#ffc107',
            'deposit': '#17a2b8',
            'withdrawal': '#fd7e14',
            'kyc_submitted': '#e83e8c'
        }
        
        color = colors.get(obj.activity_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_badge.short_description = 'Type'
    activity_type_badge.admin_order_field = 'activity_type'
    
    def description_short(self, obj):
        """Description raccourcie."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """Interface d'administration des paramètres utilisateur."""
    
    list_display = [
        'user_link', 'notifications_status', 'security_status', 
        'game_preferences', 'updated_at'
    ]
    
    list_filter = [
        'email_notifications', 'two_factor_enabled', 
        'sound_effects', 'created_at'
    ]
    
    search_fields = ['user__username', 'user__email']
    
    fieldsets = (
        (_('Notifications'), {
            'fields': (
                ('email_notifications', 'sms_notifications'),
                ('push_notifications', 'marketing_emails'),
                'login_notifications'
            )
        }),
        (_('Paramètres de jeu'), {
            'fields': (
                'auto_accept_games', 'show_game_tips', 'sound_effects'
            )
        }),
        (_('Sécurité'), {
            'fields': ('two_factor_enabled',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.username
        )
    user_link.short_description = 'Utilisateur'
    user_link.admin_order_field = 'user__username'
    
    def notifications_status(self, obj):
        """Statut des notifications."""
        status = []
        if obj.email_notifications:
            status.append('📧')
        if obj.sms_notifications:
            status.append('📱')
        if obj.push_notifications:
            status.append('🔔')
        
        return ' '.join(status) if status else '🔕'
    notifications_status.short_description = 'Notifications'
    
    def security_status(self, obj):
        """Statut de sécurité."""
        return '🔐' if obj.two_factor_enabled else '🔓'
    security_status.short_description = '2FA'
    
    def game_preferences(self, obj):
        """Préférences de jeu."""
        prefs = []
        if obj.auto_accept_games:
            prefs.append('Auto')
        if obj.sound_effects:
            prefs.append('Son')
        if obj.show_game_tips:
            prefs.append('Conseils')
        
        return ', '.join(prefs) if prefs else 'Aucune'
    game_preferences.short_description = 'Préfs jeu'  

