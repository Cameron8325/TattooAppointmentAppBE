"""
Development settings — local machine only. Never deploy with these.
"""
from .base import *  # noqa: F401,F403

DEBUG = env.bool("DEBUG", default=True)  # noqa: F405

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])  # noqa: F405

# React dev server
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Cross-origin cookies for localhost:3000 -> 127.0.0.1:8000.
# (Matches previous behavior; browsers exempt localhost from the Secure-flag
# requirement for SameSite=None.)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
