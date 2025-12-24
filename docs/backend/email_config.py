# Configuration Email RumoRush
# À ajouter aux variables d'environnement ou settings

# Configuration SMTP RumoRush - FONCTIONNE EN PRODUCTION
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.rumorush.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'support@rumorush.com'
EMAIL_HOST_PASSWORD = '7VHSQNzKj4T3Xy'
DEFAULT_FROM_EMAIL = 'RumoRush Support <support@rumorush.com>'
SERVER_EMAIL = 'support@rumorush.com'

# Configuration pour développement local (si SMTP bloqué)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Expéditeurs spécialisés
NOREPLY_EMAIL = 'noreply@rumorush.com'
ADMIN_EMAIL = 'admin@rumorush.com'
CONTACT_EMAIL = 'contact@rumorush.com'

# Configuration avancée
EMAIL_TIMEOUT = 30
EMAIL_USE_LOCALTIME = True
EMAIL_SUBJECT_PREFIX = '[RumoRush] '