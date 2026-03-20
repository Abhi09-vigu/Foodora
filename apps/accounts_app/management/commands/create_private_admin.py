from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates/updates the private admin user (email from settings.PRIVATE_ADMIN_EMAIL).'

    def add_arguments(self, parser):
        parser.add_argument('--password', help='Password to set for the admin user')

    def handle(self, *args, **options):
        email = (getattr(settings, 'PRIVATE_ADMIN_EMAIL', '') or '').strip()
        if not email:
            self.stderr.write(self.style.ERROR('settings.PRIVATE_ADMIN_EMAIL is empty'))
            return

        password = options.get('password')
        if not password:
            password = getattr(settings, 'PRIVATE_ADMIN_PASSWORD', '') or ''
        if not password:
            password = self._prompt_password()

        User = get_user_model()
        defaults = {'username': self._unique_username(User, base='private-admin')}
        user, created = User.objects.get_or_create(email=email, defaults=defaults)
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
