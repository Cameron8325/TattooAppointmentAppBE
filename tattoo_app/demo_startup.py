"""Create the separate sample database before starting the public demo."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tattoo_app.settings.demo')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from core.models import User

if not getattr(settings, 'DEMO_MODE', False) or settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
    raise RuntimeError('Demo startup requires the isolated SQLite demo settings.')
call_command('migrate', interactive=False, verbosity=0)
if not User.objects.exists():
    call_command('seed_data', verbosity=0)
# Public sample credentials open the application, never Django's system admin.
User.objects.filter(username__in=settings.DEMO_LOGIN_NAMES).update(is_staff=False, is_superuser=False)
print('Sample studio ready.', flush=True)
