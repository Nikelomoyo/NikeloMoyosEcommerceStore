"""Production settings for Render. Local development continues to use settings.py."""
import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from .settings import *  # noqa: F403

DEBUG = False
if not os.environ.get('DJANGO_SECRET_KEY') or SECRET_KEY == 'development-only-change-this-before-deployment':
    raise ImproperlyConfigured('A unique DJANGO_SECRET_KEY is required in production.')
if not os.environ.get('DATABASE_URL'):
    raise ImproperlyConfigured('DATABASE_URL is required; production must not use ephemeral SQLite.')
DATABASES = {'default': dj_database_url.config(conn_max_age=600, conn_health_checks=True)}
if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise ImproperlyConfigured('Production requires PostgreSQL.')
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]
render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_host:
    ALLOWED_HOSTS.append(render_host)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('Set DJANGO_ALLOWED_HOSTS or RENDER_EXTERNAL_HOSTNAME.')
CSRF_TRUSTED_ORIGINS = [value.strip() for value in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if value.strip()]
if render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{render_host}')
# Render terminates HTTPS and overwrites X-Forwarded-Proto at its trusted proxy.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
MIDDLEWARE = [MIDDLEWARE[0], 'whitenoise.middleware.WhiteNoiseMiddleware', *MIDDLEWARE[1:]]
STATIC_URL = '/static/'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
if not os.environ.get('DJANGO_MEDIA_ROOT'):
    raise ImproperlyConfigured('DJANGO_MEDIA_ROOT must point to persistent storage.')
MEDIA_ROOT = os.environ['DJANGO_MEDIA_ROOT']
LOGGING = {'version': 1, 'disable_existing_loggers': False,
           'handlers': {'console': {'class': 'logging.StreamHandler'}},
           'root': {'handlers': ['console'], 'level': 'INFO'}}

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

