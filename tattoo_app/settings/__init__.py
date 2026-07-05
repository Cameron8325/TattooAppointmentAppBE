"""
Settings package. Select an environment explicitly:

    DJANGO_SETTINGS_MODULE=tattoo_app.settings.dev   (local development)
    DJANGO_SETTINGS_MODULE=tattoo_app.settings.prod  (camcanhelp.com)

manage.py defaults to dev; wsgi.py/asgi.py default to prod.
NOTE: This package shadows the legacy tattoo_app/settings.py, which is kept
temporarily for rollback and can be deleted once the new structure is confirmed.
"""
