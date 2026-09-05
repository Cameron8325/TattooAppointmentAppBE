"""Public, disposable demo. Never connects to the studio database."""
import os
import tempfile
from pathlib import Path

demo_path = Path(os.environ.get('DEMO_DATABASE_PATH', str(Path(tempfile.gettempdir()) / 'imaginarium-demo.sqlite3')))
os.environ['DATABASE_URL'] = 'sqlite:///' + demo_path.as_posix()
from .base import *  # noqa: F403,E402

DEMO_MODE = True
DEMO_LOGIN_NAMES = ('admin', 'mia.torres', 'leo.nakamura', 'ava.bennett')
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
FRONTEND_URL = os.environ.get('FRONTEND_URL', '').rstrip('/')
CORS_ALLOWED_ORIGINS = [FRONTEND_URL] if FRONTEND_URL else []
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
