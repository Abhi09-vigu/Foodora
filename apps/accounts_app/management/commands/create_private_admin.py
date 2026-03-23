import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates/updates the private admin user (email from settings.PRIVATE_ADMIN_EMAIL).'

    def add_arguments(self, parser):
        parser.add_argument('--password', help='Password to set for the admin user')
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Do not prompt for missing values (fail instead).',
        )

    def handle(self, *args, **options):
        # Preferred (per Railway Variables requirement)
        email = (os.getenv('ADMIN_EMAIL') or '').strip()
        username = (os.getenv('ADMIN_USERNAME') or '').strip()

        # Backwards-compatible fallbacks
        if not email:
            email = (
                (getattr(settings, 'PRIVATE_ADMIN_EMAIL', '') or '').strip()
                or (getattr(settings, 'DJANGO_SUPERUSER_EMAIL', '') or '').strip()
                or (os.getenv('DJANGO_SUPERUSER_EMAIL') or '').strip()
            )

        if not username:
            username = (
                (getattr(settings, 'DJANGO_SUPERUSER_USERNAME', '') or '').strip()
                or (os.getenv('DJANGO_SUPERUSER_USERNAME') or '').strip()
            )

        if not email:
            self.stderr.write(
                self.style.ERROR(
                    'Admin email not configured (set ADMIN_EMAIL).'
                )
            )
            return

        password = options.get('password')
        if not password:
            password = os.getenv('ADMIN_PASSWORD') or ''

        # Backwards-compatible fallbacks
        if not password:
            password = getattr(settings, 'PRIVATE_ADMIN_PASSWORD', '') or ''
        if not password:
            password = getattr(settings, 'DJANGO_SUPERUSER_PASSWORD', '') or ''
        if not password:
            password = os.getenv('DJANGO_SUPERUSER_PASSWORD') or ''

        if not password:
            if options.get('noinput'):
                raise CommandError(
                    'No password provided (use --password or set ADMIN_PASSWORD).'
                )
            password = self._prompt_password()

        User = get_user_model()
        base_username = username or 'admin'
        defaults = {'username': self._unique_username(User, base=base_username)}
        user, created = User.objects.get_or_create(email=email, defaults=defaults)

        if username:
            user.username = self._unique_username(User, base=username)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        msg = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f"{msg} private admin: {email}"))

    def _unique_username(self, User, base: str) -> str:
        base = (base or 'private-admin').strip() or 'private-admin'
        candidate = base
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def _prompt_password(self):
        import getpass

        while True:
            p1 = getpass.getpass('Password: ')
            p2 = getpass.getpass('Password (again): ')
            if not p1:
                self.stderr.write('Password cannot be empty.')
                continue
            if p1 != p2:
                self.stderr.write('Passwords do not match. Try again.')
                continue
            return p1
