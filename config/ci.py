"""PostgreSQL CI uses development HTTP behavior so the same functional tests can run."""
import os
import dj_database_url
from .settings import *  # noqa: F403
DATABASES = {'default': dj_database_url.config()}

DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
