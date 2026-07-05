"""
Production settings — camcanhelp.com.

Requires (no defaults, fails loudly if missing): SECRET_KEY, DATABASE_URL,
ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS.
"""
from .base import *  # noqa: F401,F403

DEBUG = False  # Never override in prod.

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405

# e.g. CORS_ALLOWED_ORIGINS=https://camcanhelp.com,https://www.camcanhelp.com
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")  # noqa: F405
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")  # noqa: F405

# Cookies — HTTPS only. Lax is sufficient when the SPA and API share a site
# (e.g. camcanhelp.com + api.camcanhelp.com).
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # FE reads the token via /csrf/; revisit in Phase 2.
CSRF_COOKIE_SAMESITE = "Lax"

# TLS / security headers
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days; raise to 1 year once HTTPS is verified stable.
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
