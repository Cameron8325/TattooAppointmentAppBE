"""Isolated test storage; this configuration never uses DATABASE_URL."""
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ.setdefault('SECRET_KEY', 'isolated-test-settings-not-for-deployment')
from .base import *  # noqa: F403,E402

DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3', 'NAME':':memory:'}}
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
