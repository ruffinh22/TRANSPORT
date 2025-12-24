from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import traceback


class Command(BaseCommand):
    help = 'Send a test email using current email backend (SMTP or anymail/SendGrid).'

    def add_arguments(self, parser):
        parser.add_argument('--to', '-t', dest='to', help='Recipient email', required=False)
        parser.add_argument('--subject', '-s', dest='subject', default='RUMO RUSH test email', help='Subject')
        parser.add_argument('--body', '-b', dest='body', default='This is a test email from RUMO RUSH.', help='Body')
        parser.add_argument('--from', dest='from_email', help='From email (overrides DEFAULT_FROM_EMAIL)', required=False)

    def handle(self, *args, **options):
        to = options.get('to') or 'you@example.com'
        subject = options.get('subject')
        body = options.get('body')
        from_email = options.get('from_email') or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

        self.stdout.write(self.style.MIGRATE_HEADING('Send test email'))
        self.stdout.write(f'Using EMAIL_BACKEND={getattr(settings, "EMAIL_BACKEND", None)}')
        self.stdout.write(f'From: {from_email}  To: {to}')

        try:
            result = send_mail(subject, body, from_email, [to], fail_silently=False)
            self.stdout.write(self.style.SUCCESS(f'send_mail returned: {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Exception while sending email:'))
            self.stdout.write(self.style.ERROR(str(e)))
            tb = traceback.format_exc()
            self.stdout.write(tb)
            self.stdout.write(self.style.WARNING('Check the following:'))
            self.stdout.write('- Is SENDGRID_API_KEY / EMAIL_HOST_USER set correctly?')
            self.stdout.write('- Does the API key have Mail Send permission?')
            self.stdout.write('- Is the sender (DEFAULT_FROM_EMAIL) verified in SendGrid or Gmail?')
            self.stdout.write('- Is your account suspended or blocked?')
            raise SystemExit(1)
